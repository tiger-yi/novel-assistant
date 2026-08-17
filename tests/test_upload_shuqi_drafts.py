import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "upload_shuqi_drafts.py"
SPEC = importlib.util.spec_from_file_location("upload_shuqi_drafts", MODULE_PATH)
assert SPEC and SPEC.loader
shuqi = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = shuqi
SPEC.loader.exec_module(shuqi)


class FakeLogger:
    def __init__(self):
        self.events = []
        self.artifacts = {}

    def write(self, event):
        self.events.append(event)

    def write_artifact(self, name, content):
        self.artifacts[name] = content
        return Path(name)


class FakeBrowser:
    def __init__(self):
        self.logger = FakeLogger()
        self.state = "initial"
        self.opened = []

    def open(self, url, *, tolerate_timeout=False):
        self.opened.append(url)
        if len(self.opened) == 1:
            self.state = "login"
        elif "bookListManage" in url:
            self.state = "book_list"
        return True

    def get_url(self):
        return {
            "login": "https://write.shuqi.com/login",
            "author": "https://write.shuqi.com/author",
            "book_list": "https://write.shuqi.com/bookListManage/1",
            "draft": "https://write.shuqi.com/chapterInfo?tab=1&bookId=696136",
        }[self.state]

    def read(self):
        if self.state == "login":
            return "请输入手机号 登录"
        if self.state == "book_list":
            return "暴击返还收获成神 章节管理"
        return "草稿箱 新建草稿"

    def eval(self, script):
        if self.state == "draft" and "draft_selected" in script:
            return json.dumps(
                {
                    "draft_selected": True,
                    "has_draft_action": True,
                    "editor_present": False,
                    "tab_clicked": False,
                }
            )
        if self.state == "author" and "menuLabels" in script:
            self.state = "book_list"
            return "true"
        if self.state == "book_list" and "bookName" in script and "章节管理" in script:
            self.state = "draft"
            return "true"
        return "0"

    def wait_ms(self, _ms):
        if self.state == "login":
            self.state = "author"

    def snapshot(self, *, timeout=30):
        return 'tab "草稿箱" [selected]\nbutton "新建草稿"'


class ShuqiUploaderTest(unittest.TestCase):
    def setUp(self):
        self.book = shuqi.BookConfig(
            book_id="696136",
            book_name="暴击返还收获成神",
            chapter_dir=ROOT / "chapters",
            filename_pattern="CH-{chapter:04d}-*.txt",
            session="shuqi-test",
            back="/bookListManage/1",
            draft_url="https://write.shuqi.com/chapterInfo?tab=1&bookId=696136",
            upload_url="https://write.shuqi.com/bookEdit/696136?type=draft",
        )

    def test_login_listener_consumes_author_redirect_then_enters_draft_box(self):
        browser = FakeBrowser()

        shuqi.ensure_login(browser, self.book, timeout_seconds=10)

        self.assertEqual(["https://write.shuqi.com/author"], browser.opened)
        self.assertIn(
            "login_author_redirect_detected",
            [event["event"] for event in browser.logger.events],
        )
        self.assertIn("login_complete", [event["event"] for event in browser.logger.events])
        self.assertIn("login_book_list_detected", [event["event"] for event in browser.logger.events])

    def test_open_disables_output_capture_to_avoid_daemon_pipe_hang(self):
        browser = object.__new__(shuqi.BrowserClient)
        browser.run = mock.Mock(return_value=None)

        self.assertTrue(browser.open(self.book.draft_url))

        browser.run.assert_called_once_with(
            ["open", self.book.draft_url],
            timeout=60,
            headed=True,
            capture_output=False,
        )

    def test_open_tolerates_agent_browser_navigation_timeout(self):
        browser = object.__new__(shuqi.BrowserClient)
        browser.logger = FakeLogger()
        browser.run = mock.Mock(
            side_effect=shuqi.UploadError(
                "Operation timed out. The page may still be loading or the element may not exist.",
                "agent-browser",
            )
        )

        opened = browser.open(self.book.draft_url, tolerate_timeout=True)

        self.assertFalse(opened)
        self.assertEqual("open_timeout_tolerated", browser.logger.events[-1]["event"])

    @mock.patch.object(shuqi.subprocess, "Popen")
    def test_headed_client_uses_same_daemon_configuration_for_every_command(self, popen):
        process = popen.return_value
        process.poll.return_value = 0
        process.communicate.return_value = ("https://write.shuqi.com/author\n", "")
        browser = object.__new__(shuqi.BrowserClient)
        browser.session = "shuqi-test"
        browser.headed = True
        browser.logger = FakeLogger()
        browser.executable = "agent-browser.exe"

        browser.run(["get", "url"])

        self.assertEqual(
            [
                "agent-browser.exe",
                "--headed",
                "--session",
                "shuqi-test",
                "--restore",
                "--restore-save",
                "auto",
                "get",
                "url",
            ],
            popen.call_args.args[0],
        )

    @mock.patch.object(shuqi.subprocess, "run")
    def test_close_saves_named_persistent_session(self, run):
        run.return_value.returncode = 0
        browser = object.__new__(shuqi.BrowserClient)
        browser.session = "shuqi-test"
        browser.headed = True
        browser.logger = FakeLogger()
        browser.executable = "agent-browser.exe"

        browser.close()

        self.assertEqual(
            [
                "agent-browser.exe",
                "--headed",
                "--session",
                "shuqi-test",
                "--restore",
                "--restore-save",
                "auto",
                "close",
            ],
            run.call_args.args[0],
        )

    @mock.patch.object(shuqi.subprocess, "Popen")
    def test_non_capture_command_preserves_stderr_without_using_pipe(self, popen):
        def start_process(_args, **kwargs):
            if hasattr(kwargs["stderr"], "write"):
                kwargs["stderr"].write(b"daemon configuration conflict")
                kwargs["stderr"].flush()
            process = mock.Mock()
            process.poll.return_value = 1
            process.communicate.return_value = (None, None)
            return process

        popen.side_effect = start_process
        browser = object.__new__(shuqi.BrowserClient)
        browser.session = "shuqi-test"
        browser.headed = True
        browser.logger = FakeLogger()
        browser.executable = "agent-browser.exe"

        result = browser.run(["open", self.book.draft_url], capture_output=False, check=False)

        self.assertNotEqual(shuqi.subprocess.PIPE, popen.call_args.kwargs["stderr"])
        self.assertEqual("daemon configuration conflict", result.stderr)

    def test_eval_command_label_never_contains_script_body(self):
        self.assertEqual("eval <script>", shuqi.console_command_label(["eval", "line1\nline2"]))

    @mock.patch.object(shuqi.subprocess, "Popen")
    @mock.patch("builtins.print")
    def test_routine_browser_commands_do_not_flood_console(self, print_mock, popen):
        process = popen.return_value
        process.poll.return_value = 0
        process.communicate.return_value = ("0\n", "")
        browser = object.__new__(shuqi.BrowserClient)
        browser.session = "shuqi-test"
        browser.headed = True
        browser.logger = FakeLogger()
        browser.executable = "agent-browser.exe"

        browser.run(["eval", "line1\nline2"])

        print_mock.assert_not_called()

    def test_new_draft_uses_semantic_click_when_snapshot_times_out(self):
        browser = mock.Mock()
        browser.snapshot.side_effect = shuqi.BrowserTimeoutError(
            "snapshot timeout", "agent-browser"
        )

        click_new_draft = getattr(shuqi, "click_new_draft", None)
        self.assertIsNotNone(click_new_draft)
        click_new_draft(browser)

        browser.click_text_exact.assert_called_once_with("新建草稿")
        browser.snapshot.assert_not_called()
        browser.open.assert_not_called()
        browser.eval.assert_called_once()
        eval_call = next(call for call in browser.method_calls if call[0] == "eval")
        self.assertLess(
            browser.method_calls.index(mock.call.wait_ms(1500)),
            browser.method_calls.index(eval_call),
        )

    def test_exact_text_click_uses_agent_browser_find_without_snapshot(self):
        browser = object.__new__(shuqi.BrowserClient)
        browser.run = mock.Mock(return_value=None)

        browser.click_text_exact("新建草稿")

        browser.run.assert_called_once_with(
            ["find", "text", "新建草稿", "click", "--exact"], timeout=30
        )

    def test_parse_refs_accepts_current_create_chapter_label_and_mixed_ref_attributes(self):
        snapshot = (
            '- tab "草稿箱" [selected, ref=e7]\n'
            '- generic "创建章节" [ref=e20] clickable [onclick]'
        )

        refs = shuqi.parse_refs(snapshot)

        self.assertEqual("@e7", refs["draft_tab"])
        self.assertEqual("@e20", refs["new_draft"])

    def test_wait_for_draft_box_clicks_tab_until_selected_even_on_tab_1_route(self):
        browser = mock.Mock()
        browser.snapshot.side_effect = shuqi.BrowserTimeoutError(
            "snapshot timeout", "agent-browser"
        )
        browser.eval.side_effect = [
            json.dumps(
                json.dumps(
                    {
                        "draft_selected": False,
                        "has_draft_action": True,
                        "editor_present": False,
                        "tab_clicked": True,
                    }
                )
            ),
            json.dumps(
                json.dumps(
                    {
                        "draft_selected": True,
                        "has_draft_action": True,
                        "editor_present": False,
                        "tab_clicked": False,
                    }
                )
            ),
        ]
        browser.read.return_value = "草稿箱 共4篇草稿 第4章 分粮立规矩 创建章节"

        text = shuqi.wait_for_draft_box(browser, timeout_seconds=10)

        self.assertIn("第4章 分粮立规矩", text)
        browser.snapshot.assert_not_called()
        self.assertEqual(2, browser.eval.call_count)
        browser.wait_ms.assert_called_once_with(1000)

    def test_dismiss_overlays_clicks_explicit_dialog_button_ref(self):
        browser = mock.Mock()
        browser.snapshot.side_effect = [
            '- dialog "新增错别字纠错功能我知道了" [ref=e1]\n  - button "我知道了" [ref=e5]',
            '- textbox "请输入内容" [ref=e19]',
        ]

        shuqi.dismiss_overlays(browser)

        browser.click.assert_called_once_with("@e5")
        browser.eval.assert_not_called()

    def test_dismiss_overlays_can_skip_slow_snapshot_during_login(self):
        browser = mock.Mock()
        browser.eval.return_value = "0"

        shuqi.dismiss_overlays(browser, snapshot_first=False)

        browser.snapshot.assert_not_called()
        browser.eval.assert_called_once()

    @mock.patch.object(shuqi, "set_clipboard_text")
    @mock.patch.object(
        shuqi,
        "wait_for_editor",
        return_value={"chapter_no": "@e15", "title": "@e16", "body": "@e17"},
    )
    def test_fill_editor_uses_targeted_state_when_full_page_read_would_timeout(
        self, _wait_for_editor, _set_clipboard_text
    ):
        browser = mock.Mock()
        browser.read.side_effect = shuqi.BrowserTimeoutError("read timeout", "agent-browser")
        browser.eval.return_value = (
            '{"prefix_present": true, "word_count": 4, "cloud_saved": true, "editor_chars": 4}'
        )
        chapter = shuqi.Chapter(4, "分粮立规矩", ROOT / "chapter.txt", "正文内容")

        count = shuqi.fill_editor(browser, chapter)

        self.assertEqual(4, count)
        browser.eval.assert_called_once()
        browser.read.assert_not_called()
        browser.wait_ms.assert_not_called()

    def test_read_editor_state_accepts_agent_browser_string_result(self):
        browser = mock.Mock()
        browser.eval.return_value = json.dumps(
            json.dumps(
                {
                    "prefix_present": True,
                    "word_count": 2690,
                    "cloud_saved": True,
                    "editor_chars": 2690,
                }
            )
        )

        state = shuqi.read_editor_state(browser, "正文前缀")

        self.assertEqual(
            {
                "prefix_present": True,
                "word_count": 2690,
                "cloud_saved": True,
                "editor_chars": 2690,
            },
            state,
        )

    def test_save_does_not_treat_existing_cloud_autosave_as_draft_confirmation(self):
        browser = mock.Mock()
        browser.snapshot.side_effect = [
            '- generic [ref=e1] clickable [onclick]\n- generic "存为草稿" [ref=e2] clickable [onclick]',
            '- generic [ref=e1] clickable [onclick]\n- generic "存为草稿" [ref=e2] clickable [onclick]',
        ]

        shuqi.click_save_and_return(browser, self.book)

        self.assertEqual([mock.call("@e2"), mock.call("@e1")], browser.click.call_args_list)
        browser.eval.assert_not_called()
        browser.wait_ms.assert_called_once_with(3000)
        browser.wait_load.assert_called_once_with()

    @mock.patch.object(shuqi, "enter_draft_box")
    def test_wait_for_saved_chapter_refreshes_until_target_row_appears(self, enter_draft_box):
        browser = mock.Mock()
        chapter = shuqi.Chapter(3, "守住这片地", ROOT / "chapter.txt", "正文")
        enter_draft_box.side_effect = [
            "草稿箱 暂无信息",
            "草稿箱 第3章 守住这片地 2690",
        ]

        text = shuqi.wait_for_saved_chapter(browser, self.book, chapter, timeout_seconds=10)

        self.assertIn(chapter.display_name, text)
        browser.wait_ms.assert_called_once_with(2000)
        browser.open.assert_called_once_with(self.book.draft_url, tolerate_timeout=True)

    def test_main_logs_upload_error_details(self):
        logger = FakeLogger()
        browser = mock.Mock()
        browser.debug_snapshot.return_value = "final snapshot"
        chapter = shuqi.Chapter(3, "立威", ROOT / "chapter.txt", "正文")
        error = shuqi.BodyError("正文落点验证失败", "body")

        with (
            mock.patch.object(shuqi, "resolve_project_path", return_value=ROOT / "book.yaml"),
            mock.patch.object(shuqi, "load_config", return_value=self.book),
            mock.patch.object(shuqi, "load_chapters", return_value=[chapter]),
            mock.patch.object(shuqi, "RunLogger", return_value=logger),
            mock.patch.object(shuqi, "BrowserClient", return_value=browser),
            mock.patch.object(shuqi, "ensure_login"),
            mock.patch.object(shuqi, "upload_one", side_effect=error),
        ):
            exit_code = shuqi.main(
                ["--config", "book.yaml", "--from", "3", "--to", "3", "--yes"]
            )

        self.assertEqual(error.exit_code, exit_code)
        run_complete = next(event for event in logger.events if event["event"] == "run_complete")
        self.assertEqual(
            {
                "event": "run_complete",
                "status": "failed",
                "step": "body",
                "error": "正文落点验证失败",
            },
            run_complete,
        )
        self.assertEqual("final snapshot", logger.artifacts["final-snapshot.txt"])
        self.assertLess(
            browser.method_calls.index(mock.call.debug_snapshot()),
            browser.method_calls.index(mock.call.close()),
        )

    def test_final_snapshot_falls_back_to_url_and_page_text(self):
        logger = FakeLogger()
        browser = mock.Mock()
        browser.debug_snapshot.side_effect = shuqi.BrowserTimeoutError(
            "snapshot timeout", "agent-browser"
        )
        browser.get_url.return_value = "https://write.shuqi.com/chapterInfo?tab=1"
        browser.read.return_value = "草稿箱 暂无信息 创建章节"

        shuqi.capture_final_snapshot(browser, logger)

        artifact = logger.artifacts["final-snapshot.txt"]
        self.assertIn("snapshot timeout", artifact)
        self.assertIn("https://write.shuqi.com/chapterInfo?tab=1", artifact)
        self.assertIn("草稿箱 暂无信息 创建章节", artifact)
        self.assertTrue(logger.events[-1]["fallback"])

    def test_enter_draft_box_reuses_current_draft_page(self):
        browser = mock.Mock()
        browser.get_url.return_value = "https://write.shuqi.com/chapterInfo?tab=1&bookId=696136"
        browser.snapshot.return_value = 'tab "草稿箱" [selected]\nbutton "新建草稿"'
        browser.eval.return_value = json.dumps(
            {
                "draft_selected": True,
                "has_draft_action": True,
                "editor_present": False,
                "tab_clicked": False,
            }
        )
        browser.read.return_value = "共3篇草稿 第3章 守住这片地"

        text = shuqi.enter_draft_box(browser, self.book)

        self.assertIn("第3章 守住这片地", text)
        browser.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
