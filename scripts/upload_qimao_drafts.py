"""Upload local chapters to Qimao writer drafts.

Draft-only helper. It must not publish, submit for review, click "next", or
perform any action outside creating and saving drafts.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import html
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by missing env.
    print(
        "缺少依赖 PyYAML。请先执行: python -m pip install -r requirements-dev.txt",
        file=sys.stderr,
    )
    raise SystemExit(8) from exc

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_ROOT = ROOT / ".local" / "qimao-upload-runs"
DEFAULT_PROFILE_DIR = ROOT / ".local" / "qimao-browser-profile"

EXIT_SUCCESS = 0
EXIT_PREFLIGHT = 1
EXIT_AUTH = 2
EXIT_BROWSER = 3
EXIT_SAVE = 5
EXIT_CONFIG = 6
EXIT_DEPENDENCY = 8

DANGEROUS_TEXT = ("发布", "提交", "审核", "签约", "下一步", "申请签约")
SAFE_CONFIRM_TEXT = ("我已阅读并知晓", "确定", "确认")

CONFIG_TEMPLATE = """# 保存为 .local/qimao-books/<book>.yaml
book_id: 13140402
book_title: 百炼拳帝
chapter_dir: chapters
filename_pattern: "CH-{chapter:04d}-*.txt"
browser_profile_dir: .local/qimao-browser-profile
# 可选：平台 URL 变化时再覆盖
# draft_url: "https://zuozhe.qimao.com/front/book-manage/draft?id={book_id}&title={book_title_url}"
# upload_url: "https://zuozhe.qimao.com/front/book-upload?id={book_id}&title={book_title_url}"
"""


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


class SaveError(UploadError):
    exit_code = EXIT_SAVE


@dataclass(frozen=True)
class BookConfig:
    book_id: str
    book_title: str
    chapter_dir: Path
    filename_pattern: str
    browser_profile_dir: Path
    draft_url: str
    upload_url: str


@dataclass(frozen=True)
class ChapterPlan:
    number: int
    title: str
    path: Path
    body: str

    @property
    def local_chars(self) -> int:
        return len(self.body)


class RunLogger:
    def __init__(self, root: Path, book: BookConfig, from_chapter: int, to_chapter: int) -> None:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_book = re.sub(r"[^\w.-]+", "_", book.book_title, flags=re.UNICODE).strip("_")
        self.root = root / f"{stamp}-{book.book_id}-{safe_book}-{from_chapter}-{to_chapter}"
        self.chapters = self.root / "chapters"
        self.screenshots = self.root / "screenshots"
        self.html = self.root / "html"
        self.chapters.mkdir(parents=True, exist_ok=True)
        self.screenshots.mkdir(parents=True, exist_ok=True)
        self.html.mkdir(parents=True, exist_ok=True)
        self.run_path = self.root / "run.json"
        self.run_events: list[dict[str, Any]] = []

    def event(self, name: str, **payload: Any) -> None:
        item = {
            "event": name,
            "at": dt.datetime.now(dt.timezone.utc).isoformat(),
            **payload,
        }
        self.run_events.append(item)
        self.run_path.write_text(
            json.dumps({"events": self.run_events}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def chapter_result(self, chapter: ChapterPlan, payload: dict[str, Any]) -> None:
        path = self.chapters / f"{chapter.number:04d}.json"
        data = {
            "chapter": chapter.number,
            "title": chapter.title,
            "file_path": str(chapter.path),
            "local_chars": chapter.local_chars,
            **payload,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_urls(book_id: str, book_title: str, draft_url: str | None, upload_url: str | None) -> tuple[str, str]:
    encoded_title = quote(book_title)
    values = {
        "book_id": book_id,
        "book_title": book_title,
        "book_title_url": encoded_title,
    }
    draft = draft_url or "https://zuozhe.qimao.com/front/book-manage/draft?id={book_id}&title={book_title_url}"
    upload = upload_url or "https://zuozhe.qimao.com/front/book-upload?id={book_id}&title={book_title_url}"
    return draft.format(**values), upload.format(**values)


def load_config(path: Path) -> BookConfig:
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}", "config")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("配置文件必须是 YAML mapping", "config")
    missing = [field for field in ("book_id", "book_title") if not raw.get(field)]
    if missing:
        raise ConfigError(f"配置缺少字段: {', '.join(missing)}", "config")
    book_id = str(raw["book_id"])
    book_title = str(raw["book_title"])
    draft_url, upload_url = build_urls(
        book_id,
        book_title,
        raw.get("draft_url"),
        raw.get("upload_url"),
    )
    return BookConfig(
        book_id=book_id,
        book_title=book_title,
        chapter_dir=resolve_project_path(raw.get("chapter_dir", "chapters")),
        filename_pattern=str(raw.get("filename_pattern", "CH-{chapter:04d}-*.txt")),
        browser_profile_dir=resolve_project_path(raw.get("browser_profile_dir", str(DEFAULT_PROFILE_DIR))),
        draft_url=draft_url,
        upload_url=upload_url,
    )


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_chapters(book: BookConfig, from_chapter: int, to_chapter: int) -> list[ChapterPlan]:
    if from_chapter <= 0 or to_chapter <= 0 or from_chapter > to_chapter:
        raise PreflightError("章节范围无效，必须满足 1 <= from <= to", "preflight")
    if not book.chapter_dir.exists():
        raise PreflightError(f"章节目录不存在: {book.chapter_dir}", "preflight")

    plans: list[ChapterPlan] = []
    for number in range(from_chapter, to_chapter + 1):
        try:
            pattern = book.filename_pattern.format(chapter=number)
        except Exception as exc:
            raise PreflightError(f"filename_pattern 无法格式化: {book.filename_pattern}", "preflight") from exc
        matches = sorted(book.chapter_dir.glob(pattern))
        if not matches:
            raise PreflightError(f"缺少章节文件: {pattern}", "preflight")
        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise PreflightError(f"章节文件重复匹配: {names}", "preflight")
        path = matches[0]
        title = parse_title(path.name, number)
        body = path.read_text(encoding="utf-8-sig")
        if not body.strip():
            raise PreflightError(f"章节正文为空: {path}", "preflight")
        plans.append(ChapterPlan(number=number, title=title, path=path, body=body))
    return plans


def parse_title(filename: str, number: int) -> str:
    match = re.fullmatch(rf"CH-{number:04d}-(.+)\.txt", filename)
    if not match:
        raise PreflightError(f"无法从文件名解析标题: {filename}", "preflight")
    return match.group(1)


def print_plan(book: BookConfig, chapters: list[ChapterPlan], config_path: Path, args: argparse.Namespace) -> None:
    print("上传计划")
    print(f"配置: {config_path}")
    print(f"书籍: {book.book_title} ({book.book_id})")
    print(f"章节目录: {book.chapter_dir}")
    print(f"范围: {args.from_chapter}..{args.to_chapter}")
    print(f"浏览器: {args.browser}, headed: True, profile: {book.browser_profile_dir}")
    for chapter in chapters:
        print(f"CH-{chapter.number:04d} {chapter.title} | {chapter.local_chars} chars | {chapter.path}")


def require_confirmation(args: argparse.Namespace) -> None:
    if args.yes or args.dry_run:
        return
    answer = input("确认开始真实上传草稿？输入 YES 继续: ")
    if answer.strip().upper() != "YES":
        raise PreflightError("用户未确认上传", "confirm")


def check_browser_install_hint(browser: str) -> None:
    if browser in {"msedge", "chrome"}:
        return
    if browser == "chromium":
        return
    raise ConfigError("--browser 仅支持 msedge|chromium|chrome", "config")


async def ensure_login(page: Page, book: BookConfig, timeout_seconds: int) -> None:
    deadline = None if timeout_seconds == 0 else time.monotonic() + timeout_seconds
    await page.goto("https://zuozhe.qimao.com/front/book-manage", wait_until="domcontentloaded")
    while True:
        try:
            await page.goto(book.draft_url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=15000)
            if await target_page_ready(page):
                return
        except Exception:
            pass
        if deadline is not None and time.monotonic() >= deadline:
            raise AuthError("登录监听超时，未进入目标草稿箱", "login")
        print("等待登录成功：请在打开的七猫浏览器窗口中完成登录/验证码/弹窗处理。")
        await asyncio.sleep(5)


async def target_page_ready(page: Page) -> bool:
    text = await visible_text(page)
    if any(marker in text for marker in ("登录", "验证码登录", "扫码")) and "草稿" not in text:
        return False
    return "草稿" in text or "新建草稿" in text or "作品管理" in text


async def visible_text(page: Page) -> str:
    try:
        return await page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""


async def upload_batch(book: BookConfig, chapters: list[ChapterPlan], args: argparse.Namespace, logger: RunLogger) -> None:
    async_playwright, _, _ = load_playwright()
    async with async_playwright() as p:
        launcher = p.chromium
        launch_kwargs: dict[str, Any] = {}
        if args.browser in {"msedge", "chrome"}:
            launch_kwargs["channel"] = args.browser
        context = await launcher.launch_persistent_context(
            user_data_dir=str(book.browser_profile_dir),
            headless=False,
            accept_downloads=False,
            **launch_kwargs,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await ensure_login(page, book, args.login_timeout)
            for chapter in chapters:
                await upload_one(context, page, book, chapter, args, logger)
                if args.chapter_delay > 0:
                    await asyncio.sleep(args.chapter_delay)
        finally:
            await context.close()


async def upload_one(
    context: "BrowserContext",
    page: "Page",
    book: BookConfig,
    chapter: ChapterPlan,
    args: argparse.Namespace,
    logger: RunLogger,
) -> None:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        print(f"上传 CH-{chapter.number:04d} {chapter.title}")
        await page.goto(book.upload_url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle", timeout=20000)
        await fill_inputs(page, chapter)
        await paste_body(context, page, chapter.body)
        await save_draft(page)
        draft_count = await verify_draft_box(page, book, chapter)
        logger.chapter_result(
            chapter,
            {
                "status": "success",
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "draft_box_word_count": draft_count,
                "url": page.url,
            },
        )
    except Exception as exc:
        await save_failure_artifacts(page, chapter, logger, exc)
        logger.chapter_result(
            chapter,
            {
                "status": "failed",
                "started_at": started_at,
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "url": page.url,
                "error": str(exc),
                "step": getattr(exc, "step", "unknown"),
            },
        )
        if isinstance(exc, UploadError):
            raise
        raise SaveError(str(exc), "upload") from exc


async def fill_inputs(page: Page, chapter: ChapterPlan) -> None:
    await fill_first_visible(page, "input:not([readonly])[maxlength='5']", str(chapter.number), "章节序号")
    await fill_first_visible(
        page,
        "textarea[placeholder*='章节名称'], input[placeholder*='章节名称']",
        chapter.title,
        "章节标题",
    )


async def fill_first_visible(page: Page, selector: str, value: str, label: str) -> None:
    locators = page.locator(selector)
    count = await locators.count()
    for index in range(count):
        item = locators.nth(index)
        try:
            if await item.is_visible(timeout=500):
                await item.fill(value, timeout=10000)
                return
        except Exception:
            continue
    raise SaveError(f"找不到可编辑的{label}字段: {selector}", "fill-fields")


async def paste_body(context: BrowserContext, page: Page, body: str) -> None:
    await context.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://zuozhe.qimao.com")
    await page.evaluate("(text) => navigator.clipboard.writeText(text)", body)
    editor = await first_visible_locator(page, "[contenteditable='true'][placeholder*='请输入文字']")
    if editor is None:
        editor = await first_visible_locator(page, "[contenteditable='true']")
    if editor is None:
        raise SaveError("找不到正文编辑器", "body")
    await editor.click(timeout=10000)
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Control+V")
    await page.wait_for_timeout(1000)
    if not await editor_contains_body(page, body):
        raise SaveError("正文编辑器未检测到本地正文前缀", "body")


async def editor_contains_body(page: Page, body: str) -> bool:
    editor = await first_visible_locator(page, "[contenteditable='true'][placeholder*='请输入文字']")
    if editor is None:
        editor = await first_visible_locator(page, "[contenteditable='true']")
    if editor is None:
        return False
    text = await editor.inner_text(timeout=5000)
    return normalize_text(body)[:24] in normalize_text(text)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value)


async def first_visible_locator(page: Page, selector: str) -> Any:
    locators = page.locator(selector)
    count = await locators.count()
    for index in range(count):
        item = locators.nth(index)
        try:
            if await item.is_visible(timeout=500):
                return item
        except Exception:
            continue
    return None


async def save_draft(page: Page) -> None:
    await click_by_text(page, "存为草稿")
    await page.wait_for_timeout(1000)
    await handle_safe_popups(page)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if "book-manage/draft" in page.url:
            await page.wait_for_load_state("networkidle", timeout=20000)
            return
        await handle_safe_popups(page)
        await page.wait_for_timeout(1000)
    raise SaveError("存为草稿后未等到平台自动跳转草稿箱", "save")


async def handle_safe_popups(page: Page) -> None:
    for _ in range(5):
        clicked = False
        for text in SAFE_CONFIRM_TEXT:
            locator = page.get_by_text(text, exact=True)
            if await locator.count() > 0 and await locator.first.is_visible(timeout=1000):
                if text == "我已阅读并知晓":
                    await wait_confirm_ready(locator.first, timeout_ms=20000)
                await locator.first.click()
                await page.wait_for_timeout(1000)
                clicked = True
                break
        if not clicked:
            return


async def verify_draft_box(page: Page, book: BookConfig, chapter: ChapterPlan) -> int:
    deadline = time.monotonic() + 20
    while True:
        if "book-manage/draft" not in page.url:
            raise SaveError("保存后未停留在草稿箱，拒绝主动跳转回查", "draft-box")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle", timeout=20000)
        text = await visible_text(page)
        if chapter.title in text and f"第{chapter.number}章" in text:
            count = extract_positive_word_count(text, chapter)
            if count > 0:
                return count
        if time.monotonic() >= deadline:
            raise SaveError("草稿箱未找到目标章节标题/序号", "draft-box")
        await asyncio.sleep(2)


async def wait_confirm_ready(locator: Any, timeout_ms: int) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        try:
            text = await locator.inner_text(timeout=1000)
            disabled = await locator.evaluate(
                "el => Boolean(el.disabled || el.getAttribute('disabled') || el.className.includes('disabled'))"
            )
            has_countdown = bool(re.search(r"\d", text))
            if not disabled and not has_countdown:
                return
        except Exception:
            pass
        await asyncio.sleep(1)
    raise SaveError("我已阅读并知晓倒计时未归零或按钮不可点击", "save-confirm")


def extract_positive_word_count(text: str, chapter: ChapterPlan) -> int:
    title_index = text.find(chapter.title)
    window = text[max(0, title_index - 80) : title_index + 160] if title_index >= 0 else text
    numbers = [int(item) for item in re.findall(r"\b([1-9]\d{1,5})\b", window)]
    return max(numbers) if numbers else 0


async def click_by_text(page: Page, text: str) -> None:
    if is_dangerous_text(text):
        raise SaveError(f"拒绝点击危险操作: {text}", "danger-guard")
    locator = page.get_by_text(text, exact=True)
    if await locator.count() == 0:
        locator = page.get_by_text(text)
    await locator.first.click(timeout=10000)


def is_dangerous_text(text: str) -> bool:
    return any(word in text for word in DANGEROUS_TEXT)


async def save_failure_artifacts(page: Page, chapter: ChapterPlan, logger: RunLogger, exc: Exception) -> None:
    screenshot_path = logger.screenshots / f"{chapter.number:04d}-failure.png"
    html_path = logger.html / f"{chapter.number:04d}-failure.html"
    try:
        await page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception:
        screenshot_path = Path("")
    try:
        content = await page.content()
        html_path.write_text(content, encoding="utf-8")
    except Exception:
        html_path = Path("")
    logger.event(
        "chapter_failed",
        chapter=chapter.number,
        title=chapter.title,
        url=page.url,
        error=str(exc),
        screenshot=str(screenshot_path) if screenshot_path else "",
        html=str(html_path) if html_path else "",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="七猫作家专区草稿上传脚本，只保存草稿，明确禁止发布/提交审核/下一步。",
        epilog=(
            "依赖安装: python -m pip install -r requirements-dev.txt && "
            "python -m playwright install msedge"
        ),
    )
    parser.add_argument("--config", help="YAML 配置路径，例如 .local/qimao-books/bailian.yaml")
    parser.add_argument("--from", "--from-chapter", dest="from_chapter", type=int, help="起始章节号，闭区间")
    parser.add_argument("--to", "--to-chapter", dest="to_chapter", type=int, help="结束章节号，闭区间")
    parser.add_argument("--browser", choices=["msedge", "chromium", "chrome"], default="msedge")
    parser.add_argument("--login-timeout", type=int, default=600, help="登录监听秒数，0 表示无限等待")
    parser.add_argument("--chapter-delay", type=float, default=2.0, help="每章完成后的等待秒数")
    parser.add_argument("--dry-run", action="store_true", help="只预检和打印计划，不启动浏览器")
    parser.add_argument("--yes", action="store_true", help="跳过真实上传前 YES 确认")
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
        check_browser_install_hint(args.browser)
        config_path = resolve_project_path(args.config)
        book = load_config(config_path)
        chapters = load_chapters(book, args.from_chapter, args.to_chapter)
        print_plan(book, chapters, config_path, args)
        if args.dry_run:
            return EXIT_SUCCESS
        require_confirmation(args)
        logger = RunLogger(DEFAULT_LOG_ROOT, book, args.from_chapter, args.to_chapter)
        logger.event(
            "run_start",
            book_id=book.book_id,
            book_title=book.book_title,
            from_chapter=args.from_chapter,
            to_chapter=args.to_chapter,
            browser=args.browser,
        )
        try:
            asyncio.run(upload_batch(book, chapters, args, logger))
        except UploadError:
            logger.event("run_complete", status="failed")
            print(f"失败。日志目录: {logger.root}", file=sys.stderr)
            raise
        logger.event("run_complete", status="success")
        print(f"完成。日志目录: {logger.root}")
        return EXIT_SUCCESS
    except UploadError as exc:
        print(f"失败[{exc.step}]: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        if exc.__class__.__module__.startswith("playwright."):
            print(
                f"浏览器启动或运行失败: {exc}\n"
                "如未安装浏览器，请执行: python -m playwright install msedge",
                file=sys.stderr,
            )
            return EXIT_DEPENDENCY
        raise
    except KeyboardInterrupt:
        print("用户中断", file=sys.stderr)
        return EXIT_BROWSER


def load_playwright() -> tuple[Any, Any, Any]:
    try:
        from playwright.async_api import (
            Error as PlaywrightError,
            TimeoutError as PlaywrightTimeoutError,
            async_playwright,
        )
    except ModuleNotFoundError as exc:
        print(
            "缺少依赖 playwright。请先执行:\n"
            "python -m pip install -r requirements-dev.txt\n"
            "python -m playwright install msedge",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_DEPENDENCY) from exc
    return async_playwright, PlaywrightError, PlaywrightTimeoutError


if __name__ == "__main__":
    raise SystemExit(main())
