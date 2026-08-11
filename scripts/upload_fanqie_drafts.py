"""Upload local chapter files to Fanqie writer drafts.

This is a draft-only delivery helper. It must not publish chapters.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


EXIT_SUCCESS = 0
EXIT_PREFLIGHT = 1
EXIT_AUTH = 2
EXIT_BROWSER = 3
EXIT_BODY = 4
EXIT_SAVE = 5
EXIT_CONFIG = 6
EXIT_AUTH_IMPORT = 7

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".local" / "fanqie-books.yaml"
DEFAULT_LOG_DIR = ROOT / ".local" / "fanqie-upload-runs"
FANQIE_DOMAIN = "fanqienovel.com"


class UploadError(Exception):
    exit_code = EXIT_BROWSER

    def __init__(self, message: str, step: str = "unknown") -> None:
        super().__init__(message)
        self.step = step


class ConfigError(UploadError):
    exit_code = EXIT_CONFIG


class PreflightError(UploadError):
    exit_code = EXIT_PREFLIGHT


class AuthError(UploadError):
    exit_code = EXIT_AUTH


class BrowserError(UploadError):
    exit_code = EXIT_BROWSER


class BodyError(UploadError):
    exit_code = EXIT_BODY


class SaveError(UploadError):
    exit_code = EXIT_SAVE


class AuthImportError(UploadError):
    exit_code = EXIT_AUTH_IMPORT


@dataclass(frozen=True)
class BookConfig:
    key: str
    book_id: str
    book_name: str
    session_name: str
    draft_box_url: str
    new_draft_url: str
    editor_x: int
    editor_y: int
    login_url: str


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    path: Path
    body: str

    @property
    def display_name(self) -> str:
        return f"第{self.number}章 {self.title}"

    @property
    def local_word_count(self) -> int:
        return len(re.sub(r"\s+", "", self.body))


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def text(self) -> str:
        return f"{self.stdout}\n{self.stderr}".strip()


class RunLogger:
    def __init__(self, log_dir: Path) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.path = log_dir / f"{timestamp}.jsonl"

    def write(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("at", dt.datetime.now(dt.timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


class BrowserClient:
    def __init__(self, session_name: str, logger: RunLogger, headed: bool = True) -> None:
        self.session_name = session_name
        self.logger = logger
        self.headed = headed
        self.restarted_for_headed = False
        self.executable = resolve_agent_browser()

    def run(
        self,
        command: list[str],
        *,
        timeout: int = 30,
        include_session: bool = True,
        headed: bool = False,
        check: bool = True,
        capture_output: bool = True,
    ) -> CommandResult:
        args = [self.executable]
        if include_session:
            if self.headed and headed:
                args.append("--headed")
            args.extend(["--session-name", self.session_name])
        args.extend(command)
        command_name = " ".join(command[:2])
        self.logger.write({"event": "agent_browser_start", "command": command_name, "timeout": timeout})
        print(f"agent-browser: {command_name}", flush=True)

        try:
            stdout = subprocess.PIPE if capture_output else subprocess.DEVNULL
            stderr = subprocess.PIPE if capture_output else subprocess.DEVNULL
            completed = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise BrowserError("agent-browser 未安装或不在 PATH 中", "agent-browser") from exc
        except subprocess.TimeoutExpired as exc:
            raise BrowserError(f"agent-browser 命令超时: {' '.join(args)}", "agent-browser") from exc

        result = CommandResult(args, completed.returncode, completed.stdout or "", completed.stderr or "")
        self.logger.write(
            {
                "event": "agent_browser_done",
                "command": command_name,
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-300:],
                "stderr_tail": result.stderr[-300:],
            }
        )
        if check and result.returncode != 0:
            raise BrowserError(result.text or f"agent-browser 失败: {' '.join(args)}", "agent-browser")
        return result

    def open(self, url: str, *, timeout: int = 60) -> CommandResult:
        result = self.run(["open", url], timeout=timeout, headed=True, check=False, capture_output=False)
        if result.returncode != 0:
            raise BrowserError(result.text or f"打开页面失败: {url}", "open")
        return result

    def close_all(self, *, check: bool = True) -> None:
        self.run(["close", "--all"], timeout=20, include_session=False, check=check, capture_output=False)

    def wait_load(self) -> None:
        self.run(["wait", "--load", "networkidle"], timeout=40)

    def wait_ms(self, ms: int) -> None:
        self.run(["wait", str(ms)], timeout=max(5, ms // 1000 + 5))

    def get_url(self) -> str:
        return self.run(["get", "url"], timeout=15).stdout.strip()

    def snapshot(self) -> str:
        return self.run(["snapshot", "-i", "-c"], timeout=30).stdout

    def fill(self, selector: str, value: str) -> None:
        self.run(["fill", selector, value], timeout=20)

    def click(self, selector: str) -> None:
        self.run(["click", selector], timeout=20)

    def mouse_click(self, x: int, y: int) -> None:
        self.run(["mouse", "move", str(x), str(y)], timeout=10)
        self.run(["mouse", "down"], timeout=10)
        self.run(["mouse", "up"], timeout=10)

    def press(self, key: str) -> None:
        self.run(["press", key], timeout=20)

    def clipboard_paste(self) -> None:
        self.run(["clipboard", "paste"], timeout=20)

    def screenshot(self, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.run(["screenshot", str(path)], timeout=30)
        return str(path)

    def state_save_from_cdp(self, cdp_port: int, state_path: Path) -> None:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        args = [self.executable, "--cdp", str(cdp_port), "state", "save", str(state_path)]
        run_external(args, timeout=30)

    def state_load(self, state_path: Path) -> None:
        self.run(["state", "load", str(state_path)], timeout=30)

    def cookies_set_curl(self, curl_file: Path) -> None:
        self.run(["cookies", "set", "--curl", str(curl_file)], timeout=30)


def run_external(args: list[str], timeout: int) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AuthImportError(f"命令不存在: {args[0]}", "auth-import") from exc
    except subprocess.TimeoutExpired as exc:
        raise AuthImportError(f"命令超时: {' '.join(args)}", "auth-import") from exc
    result = CommandResult(args, completed.returncode, completed.stdout, completed.stderr)
    if result.returncode != 0:
        raise AuthImportError(result.text or f"命令失败: {' '.join(args)}", "auth-import")
    return result


def resolve_agent_browser() -> str:
    candidates = ["agent-browser.cmd", "agent-browser.exe", "agent-browser"]
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            direct = direct_agent_browser_exe(Path(path))
            return str(direct or path)
    raise BrowserError("agent-browser 未安装或不在 PATH 中", "agent-browser")


def direct_agent_browser_exe(path: Path) -> Path | None:
    base = path.parent
    exe = base / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe"
    if exe.exists():
        return exe
    return None


def load_book_config(config_path: Path, key: str) -> BookConfig:
    if not config_path.exists():
        raise ConfigError(f"配置文件不存在: {config_path}", "config")
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    books = data.get("books")
    if not isinstance(books, dict) or key not in books:
        raise ConfigError(f"配置中找不到 book key: {key}", "config")
    raw = books[key] or {}
    required = ["book_id", "book_name", "session_name", "draft_box_url", "new_draft_url"]
    missing = [name for name in required if not raw.get(name)]
    if missing:
        raise ConfigError(f"书籍配置缺少字段: {', '.join(missing)}", "config")
    editor = raw.get("editor_click") or {}
    return BookConfig(
        key=key,
        book_id=str(raw["book_id"]),
        book_name=str(raw["book_name"]),
        session_name=str(raw["session_name"]),
        draft_box_url=str(raw["draft_box_url"]),
        new_draft_url=str(raw["new_draft_url"]),
        editor_x=int(editor.get("x", 480)),
        editor_y=int(editor.get("y", 310)),
        login_url=str(raw.get("login_url") or "https://fanqienovel.com/main/writer/book-manage"),
    )


def parse_chapter_file(path: Path, number: int) -> Chapter:
    match = re.fullmatch(rf"CH-{number:04d}-(.+)\.txt", path.name)
    if not match:
        raise PreflightError(f"章节文件名不符合预期: {path.name}", "preflight")
    body = path.read_text(encoding="utf-8-sig")
    if not body.strip():
        raise PreflightError(f"章节正文为空: {path}", "preflight")
    return Chapter(number=number, title=match.group(1), path=path, body=body)


def preflight_chapters(from_chapter: int, to_chapter: int, chapters_dir: Path) -> list[Chapter]:
    if from_chapter <= 0 or to_chapter <= 0 or from_chapter > to_chapter:
        raise PreflightError("--from/--to 范围无效", "preflight")
    if not chapters_dir.exists():
        raise PreflightError(f"章节目录不存在: {chapters_dir}", "preflight")

    chapters: list[Chapter] = []
    for number in range(from_chapter, to_chapter + 1):
        matches = sorted(chapters_dir.glob(f"CH-{number:04d}-*.txt"))
        if not matches:
            raise PreflightError(f"缺少章节文件: CH-{number:04d}-*.txt", "preflight")
        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise PreflightError(f"章节文件重复匹配: {names}", "preflight")
        chapters.append(parse_chapter_file(matches[0], number))
    return chapters


def get_clipboard_text() -> str:
    try:
        return windows_get_clipboard_text()
    except UploadError:
        return ""


def set_clipboard_text(text: str) -> None:
    windows_set_clipboard_text(text)


def windows_get_clipboard_text() -> str:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    CF_UNICODETEXT = 13
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.GetClipboardData.restype = ctypes.c_void_p

    if not user32.OpenClipboard(None):
        raise UploadError("打开剪贴板失败", "clipboard")
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return ""
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def windows_set_clipboard_text(text: str) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

    data = (text + "\0").encode("utf-16-le")
    if not user32.OpenClipboard(None):
        raise UploadError("打开剪贴板失败", "clipboard")
    handle = None
    try:
        if not user32.EmptyClipboard():
            raise UploadError("清空剪贴板失败", "clipboard")
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise UploadError("分配剪贴板内存失败", "clipboard")
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            raise UploadError("锁定剪贴板内存失败", "clipboard")
        try:
            ctypes.memmove(ptr, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise UploadError("写入剪贴板失败", "clipboard")
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", "", text)


def body_prefix(body: str, length: int = 24) -> str:
    return normalize_for_match(body)[:length]


def parse_refs(snapshot: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    textbox_refs = re.findall(r"textbox[^\n]*\[ref=(e\d+)\]", snapshot)
    textbox_refs.extend(re.findall(r"\[ref=(e\d+)\][^\n]*textbox[^\n]*", snapshot))
    if textbox_refs:
        refs["chapter_no"] = textbox_refs[0]
    title = re.search(r'textbox "请输入标题"[^\n]*\[ref=(e\d+)\]', snapshot)
    if not title:
        title = re.search(r'\[ref=(e\d+)\][^\n]*textbox "请输入标题"', snapshot)
    if title:
        refs["title"] = title.group(1)
    save = re.search(r'button "存草稿"[^\n]*\[ref=(e\d+)\]', snapshot)
    if not save:
        save = re.search(r'\[ref=(e\d+)\][^\n]*button "存草稿"', snapshot)
    if save:
        refs["save"] = save.group(1)
    experience = re.search(r'button "立即体验"[^\n]*\[ref=(e\d+)\]', snapshot)
    if not experience:
        experience = re.search(r'\[ref=(e\d+)\][^\n]*button "立即体验"', snapshot)
    if experience:
        refs["experience"] = experience.group(1)
    guide_next = re.search(r'button "下一步"[^\n]*\[ref=(e\d+)\]', snapshot)
    if not guide_next:
        guide_next = re.search(r'\[ref=(e\d+)\][^\n]*button "下一步"', snapshot)
    if guide_next:
        refs["guide_next"] = guide_next.group(1)
    return refs


def page_word_count(snapshot: str) -> int:
    match = re.search(r"正文字数\s*(\d+)", snapshot)
    if not match:
        match = re.search(r"正文字数(\d+)", snapshot)
    return int(match.group(1)) if match else 0


def draft_id_from_url(url: str) -> str:
    match = re.search(r"/publish/(\d+)", url)
    return match.group(1) if match else ""


def count_draft_matches(snapshot: str, chapter: Chapter) -> int:
    return snapshot.count(chapter.display_name)


def looks_like_login_wall(url: str, snapshot: str) -> bool:
    if "login" in url:
        return True
    login_markers = ("验证码登录", "扫码登录", "扫码成功", "登录/注册")
    return any(marker in snapshot for marker in login_markers)


def dismiss_known_overlays(browser: BrowserClient) -> None:
    for _ in range(5):
        snapshot = browser.snapshot()
        refs = parse_refs(snapshot)
        if "番茄原创平台全新上线" in snapshot and refs.get("experience"):
            print("关闭番茄后台首屏弹窗...", flush=True)
            browser.click(f"@{refs['experience']}")
            browser.wait_ms(1000)
            continue
        if is_editor_guide_overlay(snapshot) and refs.get("guide_next"):
            print("跳过番茄编辑页新手引导...", flush=True)
            browser.click(f"@{refs['guide_next']}")
            browser.wait_ms(1000)
            continue
        return


def is_editor_guide_overlay(snapshot: str) -> bool:
    guide_markers = (
        "这里可以设置分卷",
        "为你的创作之旅增加色彩和氛围",
        "1/3",
        "2/3",
        "3/3",
    )
    return any(marker in snapshot for marker in guide_markers)


def assert_not_login_wall(browser: BrowserClient, step: str) -> None:
    url = browser.get_url()
    snapshot = browser.snapshot()
    if looks_like_login_wall(url, snapshot):
        raise AuthError("页面仍停留在登录/扫码确认状态", step)


def ensure_logged_in(browser: BrowserClient, book: BookConfig, timeout_seconds: int) -> None:
    print("打开作者后台并检查登录状态...", flush=True)
    browser.open(book.login_url)
    deadline = time.monotonic() + timeout_seconds
    while True:
        current_url = browser.get_url()
        snapshot = browser.snapshot()
        if not looks_like_login_wall(current_url, snapshot):
            print("登录状态已确认。", flush=True)
            dismiss_known_overlays(browser)
            return
        if time.monotonic() >= deadline:
            raise AuthError("登录等待超时", "auth")
        print("检测到番茄登录页，请在 headed 浏览器中完成登录...")
        browser.wait_ms(5000)


def fill_title_fields(browser: BrowserClient, chapter: Chapter) -> None:
    dismiss_known_overlays(browser)
    snapshot = browser.snapshot()
    refs = parse_refs(snapshot)
    if not refs.get("chapter_no") or not refs.get("title"):
        raise BrowserError("找不到章节序号或标题输入框", "fill-title")
    browser.fill(f"@{refs['chapter_no']}", str(chapter.number))
    browser.fill(f"@{refs['title']}", chapter.title)


def paste_body(browser: BrowserClient, book: BookConfig, chapter: Chapter) -> tuple[int, str]:
    set_clipboard_text(chapter.body)
    attempts = [
        (book.editor_x, book.editor_y),
        (book.editor_x, 230),
        (260, 230),
    ]
    last_snapshot = ""
    for x, y in attempts:
        browser.mouse_click(x, y)
        try:
            browser.clipboard_paste()
        except BrowserError:
            browser.press("Control+v")
        browser.wait_ms(5000)
        snapshot = browser.snapshot()
        last_snapshot = snapshot
        count = page_word_count(snapshot)
        prefix = body_prefix(chapter.body)
        if count > 0 and prefix in normalize_for_match(snapshot):
            return count, snapshot
    raise BodyError("正文落点确认失败或网页字数仍为 0", "body")


def click_save(browser: BrowserClient) -> str:
    snapshot = browser.snapshot()
    refs = parse_refs(snapshot)
    if not refs.get("save"):
        raise SaveError("找不到存草稿按钮", "save")
    browser.click(f"@{refs['save']}")
    browser.wait_ms(5000)
    snapshot = browser.snapshot()
    if "已保存到云端" not in snapshot and "保存成功" not in snapshot:
        raise SaveError("未检测到保存成功状态", "save")
    return snapshot


def upload_one(
    browser: BrowserClient,
    book: BookConfig,
    chapter: Chapter,
    logger: RunLogger,
    screenshot_dir: Path,
) -> None:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    draft_id = ""
    edit_url = ""
    before_matches = 0
    page_count = 0
    failure_step = ""
    screenshot_path = ""
    try:
        print(f"CH-{chapter.number:04d} 进入草稿箱预读...", flush=True)
        browser.open(book.draft_box_url)
        browser.wait_load()
        assert_not_login_wall(browser, "draft-box-auth")
        dismiss_known_overlays(browser)
        before_snapshot = browser.snapshot()
        before_matches = count_draft_matches(before_snapshot, chapter)

        print(f"CH-{chapter.number:04d} 打开新建草稿...", flush=True)
        browser.open(book.new_draft_url)
        browser.wait_load()
        assert_not_login_wall(browser, "open-draft-auth")
        dismiss_known_overlays(browser)
        edit_url = browser.get_url()
        draft_id = draft_id_from_url(edit_url)
        if not draft_id:
            raise BrowserError("新建草稿页未生成 draft_id", "open-draft")

        print(f"CH-{chapter.number:04d} 填写章节号和标题...", flush=True)
        fill_title_fields(browser, chapter)
        print(f"CH-{chapter.number:04d} 粘贴正文并等待字数刷新...", flush=True)
        page_count, _ = paste_body(browser, book, chapter)
        print(f"CH-{chapter.number:04d} 保存草稿...", flush=True)
        click_save(browser)

        print(f"CH-{chapter.number:04d} 返回草稿箱回查...", flush=True)
        browser.open(book.draft_box_url)
        browser.wait_load()
        after_snapshot = browser.snapshot()
        after_matches = count_draft_matches(after_snapshot, chapter)
        if after_matches <= before_matches:
            raise SaveError("草稿箱回查未确认新增草稿", "draft-box-check")

        logger.write(
            {
                "event": "chapter_upload",
                "book_id": book.book_id,
                "book_name": book.book_name,
                "chapter_no": chapter.number,
                "title": chapter.title,
                "file_path": str(chapter.path),
                "draft_id": draft_id,
                "edit_url": edit_url,
                "status": "success",
                "final_url": browser.get_url(),
                "page_word_count": page_count,
                "local_word_count": chapter.local_word_count,
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "failure_step": "",
                "screenshot_path": "",
                "existing_matches_before": before_matches,
                "matches_after": after_matches,
            }
        )
        print(f"CH-{chapter.number:04d} 上传成功，网页字数 {page_count}。", flush=True)
    except UploadError as exc:
        failure_step = exc.step
        try:
            screenshot_path = browser.screenshot(
                screenshot_dir / f"failed-CH-{chapter.number:04d}-{failure_step}.png"
            )
        except UploadError:
            screenshot_path = ""
        logger.write(
            {
                "event": "chapter_upload",
                "book_id": book.book_id,
                "book_name": book.book_name,
                "chapter_no": chapter.number,
                "title": chapter.title,
                "file_path": str(chapter.path),
                "draft_id": draft_id,
                "edit_url": edit_url,
                "status": "failed",
                "final_url": safe_get_url(browser),
                "page_word_count": page_count,
                "local_word_count": chapter.local_word_count,
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "failure_step": failure_step,
                "screenshot_path": screenshot_path,
                "existing_matches_before": before_matches,
                "error": str(exc),
            }
        )
        raise


def safe_get_url(browser: BrowserClient) -> str:
    try:
        return browser.get_url()
    except UploadError:
        return ""


def run_upload(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    book = load_book_config(config_path, args.book)
    chapters = preflight_chapters(args.from_chapter, args.to_chapter, ROOT / "chapters")
    logger = RunLogger(Path(args.log_dir).resolve())
    screenshot_dir = Path(args.screenshot_dir).resolve()
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    logger.write(
        {
            "event": "batch_start",
            "book_id": book.book_id,
            "book_name": book.book_name,
            "from": args.from_chapter,
            "to": args.to_chapter,
            "headed": not args.headless,
            "close_all_allowed": True,
        }
    )

    browser = BrowserClient(book.session_name, logger, headed=not args.headless)
    original_clipboard = ""
    clipboard_saved = False
    restore_warning = ""
    try:
        if not args.headless:
            logger.write(
                {
                    "event": "browser_restart",
                    "reason": "proactive_headed_start",
                    "action": "agent-browser close --all",
                }
            )
            browser.close_all(check=False)
            time.sleep(1)
        ensure_logged_in(browser, book, args.login_timeout_seconds)
        if not args.no_clipboard_restore:
            print("保存原剪贴板内容...", flush=True)
            logger.write({"event": "clipboard_save_start"})
            original_clipboard = get_clipboard_text()
            clipboard_saved = True
            logger.write({"event": "clipboard_save_complete", "chars": len(original_clipboard)})
        for chapter in chapters:
            upload_one(browser, book, chapter, logger, screenshot_dir)
        logger.write({"event": "batch_complete", "status": "success"})
        print("批量上传完成。", flush=True)
        return EXIT_SUCCESS
    finally:
        if clipboard_saved and not args.no_clipboard_restore:
            try:
                set_clipboard_text(original_clipboard)
            except UploadError:
                restore_warning = "剪贴板恢复失败"
                print(restore_warning, file=sys.stderr)
                logger.write({"event": "clipboard_restore_failed"})
        if not args.keep_browser_on_error:
            try:
                browser.close_all(check=False)
            except UploadError:
                logger.write({"event": "browser_close_failed"})
        if restore_warning:
            logger.write({"event": "warning", "message": restore_warning})


def run_init_auth(args: argparse.Namespace) -> int:
    book = load_book_config(Path(args.config).resolve(), args.book)
    logger = RunLogger(Path(args.log_dir).resolve())
    browser = BrowserClient(book.session_name, logger, headed=not args.headless)
    try:
        if not args.headless:
            logger.write(
                {
                    "event": "browser_restart",
                    "reason": "proactive_headed_start",
                    "action": "agent-browser close --all",
                }
            )
            browser.close_all(check=False)
            time.sleep(1)
        if args.auth_mode == "session-name":
            ensure_logged_in(browser, book, args.login_timeout_seconds)
        elif args.auth_mode == "cdp-import":
            state_path = Path(args.state_path).resolve()
            browser.state_save_from_cdp(args.cdp_port, state_path)
            browser.state_load(state_path)
        elif args.auth_mode == "curl-cookie":
            curl_file = Path(args.curl_file).resolve()
            if not curl_file.exists():
                raise AuthImportError(f"cURL 文件不存在: {curl_file}", "auth-import")
            browser.open(book.login_url)
            browser.cookies_set_curl(curl_file)
            browser.open(book.login_url)
        elif args.auth_mode == "edge-auto-scan":
            cookie_header = edge_cookie_header(args.edge_profile, args.account_hint)
            auth_dir = ROOT / ".local" / "fanqie-auth"
            auth_dir.mkdir(parents=True, exist_ok=True)
            cookie_file = auth_dir / f"{book.key}-edge-cookie.curl"
            cookie_file.write_text(
                f"curl 'https://{FANQIE_DOMAIN}/' -H 'Cookie: {cookie_header}'\n",
                encoding="utf-8",
            )
            browser.open(book.login_url)
            browser.cookies_set_curl(cookie_file)
            browser.open(book.login_url)
        else:
            raise ConfigError(f"未知认证模式: {args.auth_mode}", "auth")
        logger.write({"event": "init_auth", "auth_mode": args.auth_mode, "status": "success"})
        return EXIT_SUCCESS
    finally:
        if not args.keep_browser_on_error:
            browser.close_all(check=False)


def edge_cookie_header(edge_profile: str | None, account_hint: str | None) -> str:
    edge_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data"
    if not edge_root.exists():
        raise AuthImportError("未找到 Microsoft Edge 用户数据目录", "edge-auto-scan")

    profiles = [path for path in edge_root.iterdir() if (path / "Network" / "Cookies").exists()]
    if edge_profile:
        profiles = [path for path in profiles if path.name == edge_profile]
        if not profiles:
            raise AuthImportError(f"未找到 Edge profile: {edge_profile}", "edge-auto-scan")
    elif len(profiles) != 1:
        names = ", ".join(path.name for path in profiles)
        raise AuthImportError(f"发现多个 Edge profile，请指定 --edge-profile。候选: {names}", "edge-auto-scan")

    profile = profiles[0]
    local_state = edge_root / "Local State"
    key = load_chromium_key(local_state)
    cookies_db = profile / "Network" / "Cookies"
    cookies = read_fanqie_cookies(cookies_db, key)
    if account_hint:
        hinted = [item for item in cookies if account_hint in item[0]]
        if hinted:
            cookies = hinted
    if not cookies:
        raise AuthImportError("未找到可导入的番茄 cookie", "edge-auto-scan")
    return "; ".join(f"{name}={value}" for name, value in cookies)


def load_chromium_key(local_state: Path) -> bytes:
    try:
        raw = json.loads(local_state.read_text(encoding="utf-8"))
        encrypted_key = base64.b64decode(raw["os_crypt"]["encrypted_key"])
    except (OSError, KeyError, ValueError) as exc:
        raise AuthImportError("读取 Edge Local State 失败", "edge-auto-scan") from exc
    if encrypted_key.startswith(b"DPAPI"):
        encrypted_key = encrypted_key[5:]
    return dpapi_unprotect(encrypted_key)


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def dpapi_unprotect(data: bytes) -> bytes:
    buffer = ctypes.create_string_buffer(data)
    in_blob = DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise AuthImportError("DPAPI 解密 Edge key 失败", "edge-auto-scan")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def read_fanqie_cookies(cookies_db: Path, key: bytes) -> list[tuple[str, str]]:
    uri = f"file:{cookies_db.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=1)
    except sqlite3.Error as exc:
        raise AuthImportError("读取 Edge Cookie 数据库失败，可能被 Edge 锁定", "edge-auto-scan") from exc
    try:
        rows = conn.execute(
            """
            SELECT name, encrypted_value, value
            FROM cookies
            WHERE host_key LIKE ?
            """,
            (f"%{FANQIE_DOMAIN}",),
        ).fetchall()
    except sqlite3.Error as exc:
        raise AuthImportError("查询 Edge Cookie 数据库失败", "edge-auto-scan") from exc
    finally:
        conn.close()

    cookies: list[tuple[str, str]] = []
    for name, encrypted_value, plain_value in rows:
        if plain_value:
            value = plain_value
        else:
            value = decrypt_chromium_cookie(bytes(encrypted_value), key)
        if value:
            cookies.append((str(name), value))
    return cookies


def decrypt_chromium_cookie(encrypted_value: bytes, key: bytes) -> str:
    if encrypted_value.startswith(b"v10") or encrypted_value.startswith(b"v11"):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:
            raise AuthImportError(
                "Edge 自动扫描需要 cryptography 才能解密新版 cookie",
                "edge-auto-scan",
            ) from exc
        nonce = encrypted_value[3:15]
        ciphertext = encrypted_value[15:]
        try:
            return AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as exc:  # noqa: BLE001 - decryption libraries raise several concrete types.
            raise AuthImportError("解密 Edge cookie 失败", "edge-auto-scan") from exc
    return dpapi_unprotect(encrypted_value).decode("utf-8")


def build_upload_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="上传本地章节到番茄作者后台草稿箱")
    parser.add_argument("--book", required=True, help="YAML 配置中的 book key")
    parser.add_argument("--from", dest="from_chapter", type=int, required=True, help="起始章节号")
    parser.add_argument("--to", dest="to_chapter", type=int, required=True, help="结束章节号")
    add_common_args(parser)
    parser.add_argument("--keep-browser-on-error", action="store_true", help="失败时保留浏览器现场")
    parser.add_argument("--no-clipboard-restore", action="store_true", help="调试用：不恢复原剪贴板")
    return parser


def build_init_auth_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="初始化番茄作者后台认证")
    parser.add_argument("command", choices=["init-auth"])
    parser.add_argument("--book", required=True, help="YAML 配置中的 book key")
    add_common_args(parser)
    parser.add_argument(
        "--auth-mode",
        required=True,
        choices=["session-name", "cdp-import", "curl-cookie", "edge-auto-scan"],
    )
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--curl-file")
    parser.add_argument("--edge-profile")
    parser.add_argument("--account-hint")
    parser.add_argument("--state-path", default=str(ROOT / ".local" / "fanqie-auth" / "fanqie-auth.json"))
    parser.add_argument("--keep-browser-on-error", action="store_true")
    return parser


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="YAML 配置路径")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="JSONL 日志目录")
    parser.add_argument(
        "--screenshot-dir",
        default=str(DEFAULT_LOG_DIR / "screenshots"),
        help="失败截图目录",
    )
    parser.add_argument("--headless", action="store_true", help="显式使用 headless 调试")
    parser.add_argument("--login-timeout-seconds", type=int, default=600)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] == "init-auth":
            parser = build_init_auth_parser()
            args = parser.parse_args(argv)
            return run_init_auth(args)
        parser = build_upload_parser()
        args = parser.parse_args(argv)
        return run_upload(args)
    except UploadError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("用户中断", file=sys.stderr)
        return EXIT_BROWSER


if __name__ == "__main__":
    sys.exit(main())
