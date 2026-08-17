"""Upload local chapters to Shuqi writer drafts.

Draft-only helper. It must not publish chapters.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by missing env.
    print(
        "缺少依赖 PyYAML。请先执行: python -m pip install -r requirements-dev.txt",
        file=sys.stderr,
    )
    raise SystemExit(8) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_ROOT = ROOT / ".local" / "shuqi-upload-runs"
AUTHOR_HOME_URL = "https://write.shuqi.com/author"

EXIT_SUCCESS = 0
EXIT_PREFLIGHT = 1
EXIT_AUTH = 2
EXIT_BROWSER = 3
EXIT_BODY = 4
EXIT_SAVE = 5
EXIT_CONFIG = 6
EXIT_DEPENDENCY = 8

DANGEROUS_TEXT = ("发布", "提交", "审核", "签约", "申请签约")

CONFIG_TEMPLATE = """# 保存为 .local/shuqi-books/<book>.yaml
book_id: 696136
book_name: 暴击返还收获成神
chapter_dir: chapters
filename_pattern: "CH-{chapter:04d}-*.txt"
session: shuqi-writer
back: "/bookListManage/1"
# 可选：平台 URL 变化时再覆盖
# draft_url: "https://write.shuqi.com/chapterInfo?tab=1&bookId={book_id}&bookName={book_name_url}&back={back}"
# upload_url: "https://write.shuqi.com/bookEdit/{book_id}?type=draft"
"""


class UploadError(Exception):
    exit_code = EXIT_BROWSER

    def __init__(self, message: str, step: str = "unknown") -> None:
        super().__init__(message)
        self.step = step


class BrowserTimeoutError(UploadError):
    pass


class ConfigError(UploadError):
    exit_code = EXIT_CONFIG


class PreflightError(UploadError):
    exit_code = EXIT_PREFLIGHT


class AuthError(UploadError):
    exit_code = EXIT_AUTH


class BodyError(UploadError):
    exit_code = EXIT_BODY


class SaveError(UploadError):
    exit_code = EXIT_SAVE


@dataclass(frozen=True)
class BookConfig:
    book_id: str
    book_name: str
    chapter_dir: Path
    filename_pattern: str
    session: str
    back: str
    draft_url: str
    upload_url: str


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    path: Path
    body: str

    @property
    def display_name(self) -> str:
        return f"第{self.number}章 {self.title}"


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def text(self) -> str:
        return f"{self.stdout}\n{self.stderr}".strip()


def now_local() -> str:
    return dt.datetime.now().strftime("%H:%M:%S")


def console_command_label(command: list[str]) -> str:
    if not command:
        return "<empty>"
    if command[0] == "eval":
        return "eval <script>"
    if command[0] == "wait" and len(command) > 1 and command[1].isdigit():
        return f"wait {command[1]}ms"
    return " ".join(command[:2]).replace("\r", " ").replace("\n", " ")


def console_command_visible(command: list[str]) -> bool:
    return bool(command) and command[0] in {"open", "fill", "click", "clipboard"}


class RunLogger:
    def __init__(self, log_root: Path, book: BookConfig, from_chapter: int, to_chapter: int) -> None:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_book = re.sub(r"[^\w.-]+", "_", book.book_name, flags=re.UNICODE).strip("_")
        self.root = log_root / f"{stamp}-{book.book_id}-{safe_book}-{from_chapter}-{to_chapter}"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "run.jsonl"

    def write(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("at", dt.datetime.now(dt.timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_artifact(self, name: str, content: str) -> Path:
        target = self.root / name
        target.write_text(content, encoding="utf-8")
        return target


class BrowserClient:
    def __init__(self, session: str, headed: bool, logger: RunLogger) -> None:
        self.session = session
        self.headed = headed
        self.logger = logger
        self.executable = resolve_agent_browser()

    def _session_args(self) -> list[str]:
        args = [self.executable]
        if self.headed:
            args.append("--headed")
        args.extend(["--session", self.session, "--restore", "--restore-save", "auto"])
        return args

    def _close_session(self, event: str, label: str, timeout: int = 5) -> None:
        args = [*self._session_args(), "close"]
        self.logger.write({"event": event, "session": self.session, "timeout": timeout, "argv": args})
        print(f"[{now_local()}] {label}: {self.session}", flush=True)
        try:
            completed = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self.logger.write(
                {
                    "event": f"{event}_timeout",
                    "session": self.session,
                    "timeout": timeout,
                    "message": str(exc),
                }
            )
            print(f"[{now_local()}] 关闭会话超时，继续执行: {self.session}", flush=True)
            return
        except OSError as exc:
            self.logger.write(
                {
                    "event": f"{event}_failed",
                    "session": self.session,
                    "message": str(exc),
                }
            )
            print(f"[{now_local()}] 关闭会话失败，继续执行: {exc}", flush=True)
            return
        self.logger.write({"event": f"{event}_done", "session": self.session, "returncode": completed.returncode})

    def run(
        self,
        command: list[str],
        *,
        timeout: int = 30,
        headed: bool = False,
        check: bool = True,
        capture_output: bool = True,
    ) -> CommandResult:
        args = self._session_args()
        args.extend(command)
        started = time.monotonic()
        command_label = console_command_label(command)
        console_visible = console_command_visible(command)
        self.logger.write(
            {
                "event": "agent_browser_start",
                "command": command,
                "timeout": timeout,
                "headed": self.headed,
                "session": self.session,
                "argv": args,
            }
        )
        if console_visible:
            print(f"[{now_local()}] agent-browser start: {command_label} (timeout={timeout}s)", flush=True)
        stdout_file = tempfile.TemporaryFile() if not capture_output else None
        stderr_file = tempfile.TemporaryFile() if not capture_output else None

        def collect_output(stdout: str | None, stderr: str | None) -> tuple[str, str]:
            if stdout_file is not None:
                stdout_file.seek(0)
                stdout = stdout_file.read().decode("utf-8", errors="replace")
            if stderr_file is not None:
                stderr_file.seek(0)
                stderr = stderr_file.read().decode("utf-8", errors="replace")
            return stdout or "", stderr or ""

        def close_output_files() -> None:
            if stdout_file is not None:
                stdout_file.close()
            if stderr_file is not None:
                stderr_file.close()

        try:
            process = subprocess.Popen(
                args,
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE if capture_output else stdout_file,
                stderr=subprocess.PIPE if capture_output else stderr_file,
            )
        except FileNotFoundError as exc:
            close_output_files()
            raise UploadError("agent-browser 未安装或不在 PATH 中", "agent-browser") from exc

        while True:
            returncode = process.poll()
            elapsed = time.monotonic() - started
            if returncode is not None:
                stdout, stderr = process.communicate()
                break
            if elapsed >= timeout:
                process.kill()
                stdout, stderr = process.communicate()
                stdout, stderr = collect_output(stdout, stderr)
                close_output_files()
                self.logger.write(
                    {
                        "event": "agent_browser_timeout",
                        "command": command,
                        "elapsed_seconds": round(elapsed, 1),
                        "stdout_tail": (stdout or "")[-300:],
                        "stderr_tail": (stderr or "")[-300:],
                    }
                )
                print(f"[{now_local()}] agent-browser timeout: {command_label} after {elapsed:.1f}s", flush=True)
                raise BrowserTimeoutError(f"agent-browser 命令超时: {' '.join(command)}", "agent-browser")
            if int(elapsed) > 0 and int(elapsed) % 5 == 0:
                self.logger.write(
                    {
                        "event": "agent_browser_waiting",
                        "command": command,
                        "elapsed_seconds": round(elapsed, 1),
                    }
                )
                if console_visible:
                    print(f"[{now_local()}] agent-browser waiting: {command_label} {elapsed:.1f}s", flush=True)
                time.sleep(1.1)
            else:
                time.sleep(0.2)

        stdout, stderr = collect_output(stdout, stderr)
        close_output_files()
        completed = subprocess.CompletedProcess(args, returncode, stdout, stderr)
        result = CommandResult(args, completed.returncode, completed.stdout or "", completed.stderr or "")
        self.logger.write(
            {
                "event": "agent_browser_done",
                "command": command,
                "returncode": result.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 1),
                "stdout_tail": result.stdout[-300:],
                "stderr_tail": result.stderr[-300:],
            }
        )
        if console_visible or result.returncode != 0:
            print(
                f"[{now_local()}] agent-browser done: {command_label} rc={result.returncode} elapsed={time.monotonic() - started:.1f}s",
                flush=True,
            )
        if check and result.returncode != 0:
            raise UploadError(result.text or f"agent-browser 失败: {' '.join(command)}", "agent-browser")
        return result

    def open(self, url: str, *, tolerate_timeout: bool = False) -> bool:
        print(f"打开页面: {url}", flush=True)
        try:
            # Windows 上 daemon 启动后继承管道会导致 open 一直不退出。
            self.run(["open", url], timeout=60, headed=True, capture_output=False)
            return True
        except BrowserTimeoutError:
            if not tolerate_timeout:
                raise
            self.logger.write({"event": "open_timeout_tolerated", "url": url})
            print(f"[{now_local()}] open 超时，继续检查当前页面: {url}", flush=True)
            return False
        except UploadError as exc:
            message = str(exc).lower()
            navigation_timed_out = exc.step == "agent-browser" and "operation timed out" in message
            if not tolerate_timeout or not navigation_timed_out:
                raise
            self.logger.write(
                {
                    "event": "open_timeout_tolerated",
                    "url": url,
                    "source": "agent-browser",
                    "message": str(exc),
                }
            )
            print(f"[{now_local()}] agent-browser open 超时，继续检查当前页面: {url}", flush=True)
            return False

    def wait_load(self) -> None:
        self.run(["wait", "--load", "networkidle"], timeout=45)

    def wait_ms(self, ms: int) -> None:
        self.run(["wait", str(ms)], timeout=max(5, ms // 1000 + 5))

    def snapshot(self, *, timeout: int = 30) -> str:
        return self.run(["snapshot", "-i", "-c"], timeout=timeout).stdout

    def debug_snapshot(self) -> str:
        return self.run(["snapshot"], timeout=30).stdout

    def read(self, *, timeout: int = 30) -> str:
        return self.run(["read"], timeout=timeout).stdout

    def get_url(self) -> str:
        return self.run(["get", "url"], timeout=15).stdout.strip()

    def fill(self, ref: str, value: str) -> None:
        self.run(["fill", ref, value], timeout=30)

    def click(self, ref: str) -> None:
        self.run(["click", ref], timeout=30)

    def click_text_exact(self, text: str) -> None:
        self.run(["find", "text", text, "click", "--exact"], timeout=30)

    def press(self, key: str) -> None:
        self.run(["press", key], timeout=20)

    def clipboard_paste(self) -> None:
        self.run(["clipboard", "paste"], timeout=30)

    def eval(self, script: str) -> str:
        return self.run(["eval", script], timeout=30).stdout

    def close(self) -> None:
        self._close_session("agent_browser_close_final", "关闭浏览器会话")


def resolve_agent_browser() -> str:
    for candidate in ("agent-browser.cmd", "agent-browser.exe", "agent-browser"):
        path = shutil.which(candidate)
        if path:
            direct = direct_agent_browser_exe(Path(path))
            return str(direct or path)
    raise UploadError("agent-browser 未安装或不在 PATH 中", "agent-browser")


def direct_agent_browser_exe(path: Path) -> Path | None:
    exe = path.parent / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe"
    return exe if exe.exists() else None


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def build_urls(
    book_id: str,
    book_name: str,
    back: str,
    draft_url: str | None,
    upload_url: str | None,
) -> tuple[str, str]:
    values = {
        "book_id": book_id,
        "book_name": book_name,
        "book_name_url": quote(book_name),
        "back": back,
    }
    draft = draft_url or "https://write.shuqi.com/chapterInfo?tab=1&bookId={book_id}&bookName={book_name_url}&back={back}"
    upload = upload_url or "https://write.shuqi.com/bookEdit/{book_id}?type=draft"
    return draft.format(**values), upload.format(**values)


def load_config(path: Path) -> BookConfig:
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}", "config")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("配置文件必须是 YAML mapping", "config")
    missing = [field for field in ("book_id", "book_name") if not raw.get(field)]
    if missing:
        raise ConfigError(f"配置缺少字段: {', '.join(missing)}", "config")
    book_id = str(raw["book_id"])
    book_name = str(raw["book_name"])
    back = str(raw.get("back", "/bookListManage/1"))
    draft_url, upload_url = build_urls(book_id, book_name, back, raw.get("draft_url"), raw.get("upload_url"))
    return BookConfig(
        book_id=book_id,
        book_name=book_name,
        chapter_dir=resolve_project_path(raw.get("chapter_dir", "chapters")),
        filename_pattern=str(raw.get("filename_pattern", "CH-{chapter:04d}-*.txt")),
        session=str(raw.get("session", "shuqi-writer")),
        back=back,
        draft_url=draft_url,
        upload_url=upload_url,
    )


def load_chapters(book: BookConfig, from_chapter: int, to_chapter: int) -> list[Chapter]:
    if from_chapter <= 0 or to_chapter < from_chapter:
        raise PreflightError("章节范围无效，必须满足 1 <= from <= to", "preflight")
    chapters: list[Chapter] = []
    for number in range(from_chapter, to_chapter + 1):
        try:
            pattern = book.filename_pattern.format(chapter=number)
        except Exception as exc:
            raise PreflightError(f"filename_pattern 无法格式化: {book.filename_pattern}", "preflight") from exc
        matches = sorted(book.chapter_dir.glob(pattern))
        if not matches:
            raise PreflightError(f"缺少章节文件: {pattern}", "preflight")
        if len(matches) > 1:
            raise PreflightError(f"章节文件重复匹配: {', '.join(path.name for path in matches)}", "preflight")
        match = re.fullmatch(rf"CH-{number:04d}-(.+)\.txt", matches[0].name)
        if not match:
            raise PreflightError(f"无法从文件名解析章节标题: {matches[0].name}", "preflight")
        body = matches[0].read_text(encoding="utf-8-sig")
        if not body.strip():
            raise PreflightError(f"章节正文为空: {matches[0]}", "preflight")
        chapters.append(Chapter(number, match.group(1), matches[0], body))
    return chapters


def looks_like_login(text: str, url: str) -> bool:
    markers = ("请输入手机号", "请输入密码", "验证码", "登 录", "登录")
    return "login" in url or any(marker in text for marker in markers)


def safe_get_url(browser: BrowserClient) -> str:
    try:
        return browser.get_url()
    except UploadError:
        return ""


def safe_read(browser: BrowserClient, *, timeout: int | None = None) -> str:
    try:
        return browser.read() if timeout is None else browser.read(timeout=timeout)
    except UploadError:
        return ""


OVERLAY_DISMISS_LABELS = frozenset(("Close", "快来体验吧", "我知道了", "知道了", "关闭", "确定"))


def overlay_dismiss_ref(snapshot: str) -> str | None:
    for line in snapshot.splitlines():
        match = re.search(r'^\s*-\s+button\s+"([^"]+)"[^\n]*\[ref=(e\d+)\]', line)
        if match and match.group(1).strip() in OVERLAY_DISMISS_LABELS:
            return f"@{match.group(2)}"
    return None


def dismiss_overlays(browser: BrowserClient, *, snapshot_first: bool = True) -> None:
    script = r"""
(() => {
  const labels = new Set(['Close', '快来体验吧', '我知道了', '知道了', '关闭', '确定']);
  const nodes = Array.from(document.querySelectorAll('.correctTipModalWrapper button, .ant-modal-wrap button, button, .ant-modal-close, [role="button"], .ant-btn'));
  let clicked = 0;
  for (const node of nodes) {
    const text = (node.innerText || node.textContent || node.getAttribute('aria-label') || '').trim();
    if (!labels.has(text)) continue;
    const rect = node.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    node.click();
    clicked += 1;
    break;
  }
  return clicked;
})()
"""
    clicked_snapshot_ref = False
    for _ in range(3):
        ref = None
        if snapshot_first:
            try:
                ref = overlay_dismiss_ref(browser.snapshot())
            except UploadError:
                pass
        if ref:
            try:
                browser.click(ref)
            except UploadError:
                pass
            else:
                clicked_snapshot_ref = True
                browser.wait_ms(800)
                continue
        if clicked_snapshot_ref:
            return
        try:
            clicked = browser.eval(script).strip()
        except UploadError:
            return
        if clicked not in {"1", "1\n"}:
            return
        browser.wait_ms(800)


def click_author_book_list(browser: BrowserClient) -> None:
    script = r"""
(() => {
  const textOf = n => (n.innerText || n.textContent || '').trim();
  const visible = n => {
    const rect = n.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const routeLinks = Array.from(document.querySelectorAll('a[href*="bookListManage"]'));
  for (const link of routeLinks) {
    if (!visible(link)) continue;
    link.click();
    return true;
  }
  const menuLabels = new Set(['书籍管理', '作品管理', '我的作品']);
  const nodes = Array.from(document.querySelectorAll('a, button, [role="button"], li, div, span'));
  for (const node of nodes) {
    if (!menuLabels.has(textOf(node)) || !visible(node)) continue;
    node.click();
    return true;
  }
  return false;
})()
"""
    clicked = browser.eval(script).strip()
    if "true" not in clicked:
        raise UploadError("作者首页找不到书籍管理入口", "author-route")
    browser.wait_ms(1500)


def click_book_chapter_manage(browser: BrowserClient, book: BookConfig) -> None:
    script = rf"""
(() => {{
  const bookName = {json.dumps(book.book_name, ensure_ascii=False)};
  const textOf = n => (n.innerText || n.textContent || '').trim();
  const bookNodes = Array.from(document.querySelectorAll('*')).filter(n => textOf(n) === bookName);
  for (const bookNode of bookNodes) {{
    let root = bookNode;
    for (let depth = 0; root && depth < 10; depth += 1, root = root.parentElement) {{
      const buttons = Array.from(root.querySelectorAll('button, a, [role="button"], span, div'))
        .filter(n => textOf(n) === '章节管理');
      for (const button of buttons) {{
        const rect = button.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        button.click();
        return true;
      }}
    }}
  }}
  const candidates = Array.from(document.querySelectorAll('button, a, [role="button"]'))
    .filter(n => textOf(n) === '章节管理');
  if (candidates.length === 1) {{
    candidates[0].click();
    return true;
  }}
  return false;
}})()
"""
    clicked = browser.eval(script).strip()
    if "true" not in clicked:
        raise UploadError(f"书籍管理页找不到《{book.book_name}》的章节管理按钮", "book-list")
    browser.wait_ms(1500)


def enter_draft_box(browser: BrowserClient, book: BookConfig, timeout_seconds: int = 45) -> str:
    if "chapterInfo" in safe_get_url(browser):
        try:
            return wait_for_draft_box(browser, timeout_seconds=3)
        except UploadError:
            pass
    browser.open(book.draft_url, tolerate_timeout=True)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        dismiss_overlays(browser)
        url = safe_get_url(browser)
        text = safe_read(browser)
        if looks_like_login(text, url):
            raise AuthError("页面停留在登录状态", "auth")
        if "chapterInfo" in url:
            return wait_for_draft_box(browser)
        if "/author" in url:
            click_author_book_list(browser)
            continue
        if "bookListManage" in url or (book.book_name in text and "章节管理" in text):
            click_book_chapter_manage(browser, book)
            continue
        browser.wait_ms(1500)
    raise UploadError("未能进入草稿箱", "draft-box")


def ensure_login(browser: BrowserClient, book: BookConfig, timeout_seconds: int) -> None:
    print("打开书旗作者首页并监听登录状态...", flush=True)
    browser.open(AUTHOR_HOME_URL, tolerate_timeout=True)
    deadline = None if timeout_seconds == 0 else time.monotonic() + timeout_seconds
    last_url = ""
    login_prompted = False
    while True:
        dismiss_overlays(browser, snapshot_first=False)
        url = safe_get_url(browser)
        text = safe_read(browser)
        if url != last_url:
            browser.logger.write({"event": "login_page_changed", "url": url})
            print(f"[{now_local()}] 登录监听页面: {url or '<无法读取>'}", flush=True)
            last_url = url

        if "chapterInfo" in url:
            wait_for_draft_box(browser)
            browser.logger.write({"event": "login_complete", "url": url})
            print("登录状态已确认，已进入草稿箱。", flush=True)
            return

        if "/author" in url:
            browser.logger.write({"event": "login_author_redirect_detected", "url": url})
            print("检测到登录后跳转作者首页，正在点击书籍管理入口...", flush=True)
            click_author_book_list(browser)
            login_prompted = False
            continue

        if "bookListManage" in url or (book.book_name in text and "章节管理" in text):
            browser.logger.write({"event": "login_book_list_detected", "url": url})
            print(f"已进入书籍管理页，正在打开《{book.book_name}》章节管理...", flush=True)
            click_book_chapter_manage(browser, book)
            continue

        if looks_like_login(text, url):
            if not login_prompted:
                print("等待登录：请在 headed 浏览器窗口中完成书旗登录/验证码。", flush=True)
                login_prompted = True
        elif url:
            browser.logger.write({"event": "login_unknown_page", "url": url})

        if deadline is not None and time.monotonic() >= deadline:
            raise AuthError("登录等待超时", "auth")
        browser.wait_ms(2000)


def parse_refs(snapshot: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    for line in snapshot.splitlines():
        ref = re.search(r"\bref=(e\d+)\b", line)
        if not ref:
            continue
        ref_value = f"@{ref.group(1)}"
        if 'tab "草稿箱"' in line:
            refs["draft_tab"] = ref_value
        elif "新建草稿" in line or "创建章节" in line:
            refs["new_draft"] = ref_value
        elif 'textbox "请输入标题"' in line:
            refs["title"] = ref_value
        elif 'textbox "请输入内容"' in line:
            refs["body"] = ref_value
        elif "存为草稿" in line:
            refs["save"] = ref_value
        elif "发布" in line:
            refs["publish"] = ref_value
        elif line.strip().startswith("- generic") and "clickable" in line and "back" not in refs:
            refs["back"] = ref_value
    textbox_refs = re.findall(r"textbox[^\n]*\bref=(e\d+)\b", snapshot)
    if textbox_refs:
        refs.setdefault("chapter_no", f"@{textbox_refs[0]}")
    return refs


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text)


def page_word_count(text: str) -> int:
    match = re.search(r"当前字数\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def read_editor_state(browser: BrowserClient, prefix: str) -> dict[str, object]:
    script = rf"""
(() => {{
  const prefix = {json.dumps(prefix, ensure_ascii=False)};
  const visible = node => {{
    const rect = node.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }};
  const labelOf = node => [
    node.getAttribute('placeholder'),
    node.getAttribute('data-placeholder'),
    node.getAttribute('aria-label'),
  ].filter(Boolean).join(' ');
  const candidates = Array.from(document.querySelectorAll('[contenteditable="true"], textarea'))
    .filter(visible);
  const editor = candidates.find(node => labelOf(node).includes('请输入内容'))
    || candidates.find(node => !labelOf(node).includes('作者说'));
  const editorText = editor
    ? (editor.innerText || editor.textContent || editor.value || '').replace(/\s+/g, '')
    : '';
  const pageText = document.body ? (document.body.innerText || '') : '';
  const countMatch = pageText.match(/当前字数\s*[:：]?\s*([\d,]+)/);
  return JSON.stringify({{
    prefix_present: editorText.includes(prefix),
    word_count: countMatch ? Number(countMatch[1].replace(/,/g, '')) : 0,
    cloud_saved: pageText.includes('已保存到云端'),
    editor_chars: editorText.length,
  }});
}})()
    """
    try:
        state = json.loads(browser.eval(script).strip())
        if isinstance(state, str):
            state = json.loads(state)
        if not isinstance(state, dict):
            raise ValueError("editor state is not an object")
        return {
            "prefix_present": bool(state.get("prefix_present")),
            "word_count": int(state.get("word_count", 0)),
            "cloud_saved": bool(state.get("cloud_saved")),
            "editor_chars": int(state.get("editor_chars", 0)),
        }
    except (UploadError, json.JSONDecodeError, TypeError, ValueError):
        return {"prefix_present": False, "word_count": 0, "cloud_saved": False, "editor_chars": 0}


def has_duplicate(text: str, chapter: Chapter) -> bool:
    return chapter.display_name in text


def read_draft_box_state(browser: BrowserClient) -> dict[str, bool]:
    script = r"""
(() => {
  const visible = node => {
    const rect = node.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const textOf = node => (node.innerText || node.textContent || '').trim();
  const nodes = Array.from(document.querySelectorAll('[role="tab"], .ant-tabs-tab, .ant-tabs-tab-btn, button, a, div, span'));
  const label = nodes.find(node => visible(node) && textOf(node) === '草稿箱');
  const tab = label
    ? (label.closest('[role="tab"], .ant-tabs-tab, li') || label)
    : null;
  const selected = tab
    ? [tab, tab.parentElement].filter(Boolean).some(node =>
        node.getAttribute('aria-selected') === 'true'
        || Array.from(node.classList || []).some(name => /(?:active|selected|current)/i.test(name)))
    : false;
  const hasAction = nodes.some(node =>
    visible(node) && ['新建草稿', '创建章节'].includes(textOf(node)));
  const editors = Array.from(document.querySelectorAll('[contenteditable="true"], textarea'));
  const editorPresent = editors.some(node => {
    if (!visible(node)) return false;
    const labelText = [
      node.getAttribute('placeholder'),
      node.getAttribute('data-placeholder'),
      node.getAttribute('aria-label'),
    ].filter(Boolean).join(' ');
    return labelText.includes('请输入内容');
  });
  let tabClicked = false;
  if (tab && !selected) {
    tab.click();
    tabClicked = true;
  }
  return JSON.stringify({
    draft_selected: selected,
    has_draft_action: hasAction,
    editor_present: editorPresent,
    tab_clicked: tabClicked,
  });
})()
"""
    try:
        state = json.loads(browser.eval(script).strip())
        if isinstance(state, str):
            state = json.loads(state)
        if not isinstance(state, dict):
            raise ValueError("draft box state is not an object")
        return {
            "draft_selected": bool(state.get("draft_selected")),
            "has_draft_action": bool(state.get("has_draft_action")),
            "editor_present": bool(state.get("editor_present")),
            "tab_clicked": bool(state.get("tab_clicked")),
        }
    except (UploadError, json.JSONDecodeError, TypeError, ValueError):
        return {
            "draft_selected": False,
            "has_draft_action": False,
            "editor_present": False,
            "tab_clicked": False,
        }


def wait_for_draft_box(browser: BrowserClient, timeout_seconds: int = 30) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        state = read_draft_box_state(browser)
        if (
            state["draft_selected"]
            and state["has_draft_action"]
            and not state["editor_present"]
        ):
            return browser.read()
        browser.wait_ms(1000 if state["tab_clicked"] else 1500)
    raise UploadError("未进入草稿箱列表，拒绝继续新建草稿", "draft-box")


def wait_for_editor(browser: BrowserClient, timeout_seconds: int = 30) -> dict[str, str]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        snapshot = browser.snapshot()
        refs = parse_refs(snapshot)
        if all(name in refs for name in ("chapter_no", "title", "body")):
            return refs
        browser.wait_ms(1500)
    raise UploadError("找不到编辑字段: chapter_no, title, body", "fill")


def click_new_draft(browser: BrowserClient) -> None:
    browser.click_text_exact("新建草稿")
    browser.wait_ms(1500)
    dismiss_overlays(browser, snapshot_first=False)


def set_clipboard_text(text: str) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    cf_unicode_text = 13
    gmem_moveable = 0x0002
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p

    data = (text + "\0").encode("utf-16-le")
    if not user32.OpenClipboard(None):
        raise BodyError("打开剪贴板失败", "clipboard")
    handle = None
    try:
        if not user32.EmptyClipboard():
            raise BodyError("清空剪贴板失败", "clipboard")
        handle = kernel32.GlobalAlloc(gmem_moveable, len(data))
        if not handle:
            raise BodyError("分配剪贴板内存失败", "clipboard")
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            raise BodyError("锁定剪贴板内存失败", "clipboard")
        try:
            ctypes.memmove(ptr, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(cf_unicode_text, handle):
            raise BodyError("写入剪贴板失败", "clipboard")
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def fill_editor(browser: BrowserClient, chapter: Chapter) -> int:
    refs = wait_for_editor(browser)
    if "publish" in refs:
        print("检测到发布按钮，已启用危险操作保护：不会点击。", flush=True)
    browser.fill(refs["chapter_no"], str(chapter.number))
    browser.fill(refs["title"], chapter.title)
    set_clipboard_text(chapter.body)
    browser.click(refs["body"])
    browser.press("Control+a")
    browser.clipboard_paste()
    deadline = time.monotonic() + 30
    prefix = normalized(chapter.body)[:24]
    state: dict[str, object] = {}
    while time.monotonic() < deadline:
        state = read_editor_state(browser, prefix)
        count = int(state["word_count"])
        if count > 0 and state["prefix_present"] and state["cloud_saved"]:
            return count
        browser.wait_ms(2000)
    raise BodyError(
        "正文落点验证失败: "
        f"前缀命中={bool(state.get('prefix_present'))}, "
        f"网页字数={int(state.get('word_count', 0))}, "
        f"云端状态={bool(state.get('cloud_saved'))}, "
        f"编辑器字符={int(state.get('editor_chars', 0))}",
        "body",
    )


def click_save_and_return(browser: BrowserClient, book: BookConfig) -> None:
    refs = parse_refs(browser.snapshot())
    save_ref = refs.get("save")
    if not save_ref:
        raise SaveError("找不到存为草稿按钮", "save")
    if any(word in "存为草稿" for word in DANGEROUS_TEXT):
        raise SaveError("拒绝点击危险操作", "save")
    browser.click(save_ref)
    browser.wait_ms(3000)
    refs = parse_refs(browser.snapshot())
    if refs.get("back"):
        browser.click(refs["back"])
        browser.wait_load()


def wait_for_saved_chapter(
    browser: BrowserClient,
    book: BookConfig,
    chapter: Chapter,
    timeout_seconds: int = 60,
) -> str:
    deadline = time.monotonic() + timeout_seconds
    refresh = False
    while time.monotonic() < deadline:
        if refresh:
            browser.open(book.draft_url, tolerate_timeout=True)
        text = enter_draft_box(browser, book)
        if has_duplicate(text, chapter):
            return text
        browser.logger.write(
            {
                "event": "draft_verification_retry",
                "chapter": chapter.number,
                "title": chapter.title,
            }
        )
        browser.wait_ms(2000)
        refresh = True
    raise SaveError("草稿箱未找到保存后的章节", "draft-box")


def upload_one(
    browser: BrowserClient,
    book: BookConfig,
    chapter: Chapter,
    logger: RunLogger,
    skip_existing: bool,
) -> None:
    before_text = enter_draft_box(browser, book)
    if has_duplicate(before_text, chapter) and skip_existing:
        logger.write({"event": "chapter_skipped_duplicate", "chapter": chapter.number, "title": chapter.title})
        print(f"跳过已存在草稿: {chapter.display_name}", flush=True)
        return
    click_new_draft(browser)
    count = fill_editor(browser, chapter)
    click_save_and_return(browser, book)
    wait_for_saved_chapter(browser, book, chapter)
    logger.write({"event": "chapter_uploaded", "chapter": chapter.number, "title": chapter.title, "word_count": count})
    print(f"完成: {chapter.display_name}，网页字数 {count}", flush=True)


def capture_final_snapshot(browser: BrowserClient, logger: RunLogger) -> None:
    try:
        snapshot = browser.debug_snapshot()
        path = logger.write_artifact("final-snapshot.txt", snapshot)
        logger.write({"event": "final_snapshot_saved", "path": str(path), "fallback": False})
    except Exception as exc:
        try:
            url = safe_get_url(browser)
            text = safe_read(browser, timeout=5)
            fallback = (
                f"snapshot_error: {exc}\n"
                f"url: {url or '<unavailable>'}\n\n"
                f"page_text:\n{text or '<unavailable>'}\n"
            )
            path = logger.write_artifact("final-snapshot.txt", fallback)
            logger.write(
                {
                    "event": "final_snapshot_saved",
                    "path": str(path),
                    "fallback": True,
                    "snapshot_error": str(exc),
                }
            )
        except Exception as fallback_exc:
            logger.write(
                {
                    "event": "final_snapshot_failed",
                    "error": str(fallback_exc),
                    "snapshot_error": str(exc),
                }
            )


def print_plan(book: BookConfig, chapters: list[Chapter], config_path: Path, args: argparse.Namespace) -> None:
    print("上传计划")
    print(f"配置: {config_path}")
    print(f"书籍: {book.book_name} ({book.book_id})")
    print(f"章节目录: {book.chapter_dir}")
    print(f"文件模式: {book.filename_pattern}")
    print(f"范围: {args.from_chapter}..{args.to_chapter}")
    print(f"会话: {args.session or book.session}, headed: {not args.headless}, restore: True")
    print(f"登录监听: {args.login_timeout} 秒")
    for chapter in chapters:
        print(f"- {chapter.display_name}: {chapter.path}")


def require_confirmation(args: argparse.Namespace) -> None:
    if args.yes or args.dry_run:
        return
    answer = input("确认开始真实上传草稿？输入 YES 继续: ")
    if answer.strip().upper() != "YES":
        raise PreflightError("用户未确认上传", "confirm")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="书旗创作平台草稿上传脚本，只保存草稿，不发布。")
    parser.add_argument("--config", help="YAML 配置路径，例如 .local/shuqi-books/baoji.yaml")
    parser.add_argument("--from", "--from-chapter", dest="from_chapter", type=int, help="起始章节号，闭区间")
    parser.add_argument("--to", "--to-chapter", dest="to_chapter", type=int, help="结束章节号，闭区间")
    parser.add_argument("--session", help="覆盖配置中的 agent-browser 会话名")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--login-timeout", type=int, default=600, help="登录监听秒数，0 表示无限等待")
    parser.add_argument("--chapter-delay", type=float, default=2.0, help="每章完成后的等待秒数")
    parser.add_argument("--allow-duplicate", action="store_true", help="允许已有同名草稿时继续新建")
    parser.add_argument("--dry-run", action="store_true", help="只预检和打印计划，不启动浏览器")
    parser.add_argument("--yes", action="store_true", help="跳过真实上传前 YES 确认")
    parser.add_argument("--keep-browser", action="store_true", help="完成或失败后保留浏览器窗口")
    parser.add_argument("--print-config-template", action="store_true", help="输出 YAML 配置模板后退出")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.print_config_template:
        print(CONFIG_TEMPLATE)
        return EXIT_SUCCESS
    try:
        if not args.config or args.from_chapter is None or args.to_chapter is None:
            parser.error("--config、--from/--from-chapter、--to/--to-chapter 必填，除非使用 --print-config-template")
        config_path = resolve_project_path(args.config)
        book = load_config(config_path)
        if args.session:
            book = BookConfig(
                book_id=book.book_id,
                book_name=book.book_name,
                chapter_dir=book.chapter_dir,
                filename_pattern=book.filename_pattern,
                session=args.session,
                back=book.back,
                draft_url=book.draft_url,
                upload_url=book.upload_url,
            )
        chapters = load_chapters(book, args.from_chapter, args.to_chapter)
        print_plan(book, chapters, config_path, args)
        if args.dry_run:
            return EXIT_SUCCESS
        require_confirmation(args)
        logger = RunLogger(DEFAULT_LOG_ROOT, book, args.from_chapter, args.to_chapter)
        logger.write(
            {
                "event": "run_start",
                "book_id": book.book_id,
                "book_name": book.book_name,
                "from": args.from_chapter,
                "to": args.to_chapter,
                "session": book.session,
                "restore": True,
            }
        )
        browser = BrowserClient(book.session, not args.headless, logger)
        try:
            ensure_login(browser, book, args.login_timeout)
            for chapter in chapters:
                upload_one(browser, book, chapter, logger, skip_existing=not args.allow_duplicate)
                if args.chapter_delay > 0:
                    browser.wait_ms(int(args.chapter_delay * 1000))
            logger.write({"event": "run_complete", "status": "success"})
        except UploadError as exc:
            logger.write(
                {
                    "event": "run_complete",
                    "status": "failed",
                    "step": exc.step,
                    "error": str(exc),
                }
            )
            raise
        finally:
            capture_final_snapshot(browser, logger)
            if not args.keep_browser:
                browser.close()
        print(f"日志: {logger.path}")
        return EXIT_SUCCESS
    except UploadError as exc:
        print(f"失败[{exc.step}]: {exc}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("用户中断", file=sys.stderr)
        return EXIT_BROWSER


if __name__ == "__main__":
    raise SystemExit(main())
