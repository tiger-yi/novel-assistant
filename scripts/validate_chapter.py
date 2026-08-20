import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts.check_count import DEFAULT_MAX_WORDS, DEFAULT_MIN_WORDS, count_words
except ModuleNotFoundError:
    from check_count import DEFAULT_MAX_WORDS, DEFAULT_MIN_WORDS, count_words


BLACKLIST_HEADING = "### 黑名单词"
BLACKLIST_ITEM = re.compile(r"^\s*[*+-]\s+(.+?)\s*$")
MARKDOWN_BLOCKS = (
    re.compile(r"^\s*#{1,6}\s+"),
    re.compile(r"^\s*(?:[-+*]\s+|\d+\.\s+)"),
    re.compile(r"^\s*\|.*\|\s*$"),
)
FORBIDDEN_SYMBOLS = ("【", "】", "[", "]", "（", "）", "《", "》", "**")
CHAPTER_FORMAT_INV = "INV-CHAPTER-001"
HARNESS_IDENTIFIER = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:CH|ARC|HOOK|SEED|EVT|TX|CHAR|ITEM|LOC|FAC|GOAL|MS)"
    r"-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Za-z0-9])",
    re.IGNORECASE,
)
BARE_ALPHANUMERIC_CODE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?=[A-Za-z0-9-]*[A-Za-z])(?=[A-Za-z0-9-]*\d)"
    r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*(?![A-Za-z0-9])",
    re.IGNORECASE,
)
CHAPTER_STRUCTURE_REFERENCE = re.compile(
    r"第(?:[0-9零〇一二三四五六七八九十百千万两]+|[XxNn])章|"
    r"上一章|上章|本章|下一章|下章|前文|后文"
)
QUOTED_TEXT = re.compile(r"[\u201c\u201d\u300c\u300d\u2018\u2019\"']")


def load_blacklist(style_path):
    lines = Path(style_path).read_text(encoding="utf-8").splitlines()
    in_blacklist = False
    found_heading = False
    terms = []

    for line in lines:
        stripped = line.strip()
        if stripped == BLACKLIST_HEADING:
            in_blacklist = True
            found_heading = True
            continue
        if in_blacklist and re.match(r"^#{1,3}\s+", stripped):
            break
        if not in_blacklist:
            continue
        match = BLACKLIST_ITEM.match(line)
        if match:
            terms.append(match.group(1).strip(" `"))

    if not found_heading or not terms:
        raise ValueError("style guide blacklist section is missing or empty")
    return terms


def find_presentation_errors(text):
    errors = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for symbol in FORBIDDEN_SYMBOLS:
            if symbol in line:
                errors.append(
                    f"{CHAPTER_FORMAT_INV}: forbidden symbol found "
                    f"at line {line_number}: {symbol}"
                )
        if any(pattern.search(line) for pattern in MARKDOWN_BLOCKS):
            errors.append(
                f"{CHAPTER_FORMAT_INV}: Markdown block found at line {line_number}"
            )

        known_spans = []
        for match in HARNESS_IDENTIFIER.finditer(line):
            known_spans.append(match.span())
            errors.append(
                f"{CHAPTER_FORMAT_INV}: narrative-layer identifier found "
                f"at line {line_number}: {match.group(0)}"
            )
        for match in BARE_ALPHANUMERIC_CODE.finditer(line):
            if any(
                match.start() < end and match.end() > start
                for start, end in known_spans
            ):
                continue
            errors.append(
                f"{CHAPTER_FORMAT_INV}: bare alphanumeric code found "
                f"at line {line_number}: {match.group(0)}"
            )
        for match in CHAPTER_STRUCTURE_REFERENCE.finditer(line):
            errors.append(
                f"{CHAPTER_FORMAT_INV}: chapter structure reference found "
                f"at line {line_number}: {match.group(0)}"
            )
    return errors


def find_quoted_lines(text):
    """Return (line_number, snippet, quote_char) for every line containing a
    quotation mark. The Agent must semantically audit each result line."""
    results = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        matches = QUOTED_TEXT.findall(line)
        if not matches:
            continue
        results.append(
            {
                "line": line_number,
                "quote": matches[0],
                "text": line.strip()[:200],
            }
        )
    return results


def validate_chapter(
    chapter_path,
    style_path,
    target=DEFAULT_MIN_WORDS,
    max_words=DEFAULT_MAX_WORDS,
):
    chapter_path = Path(chapter_path)
    text = chapter_path.read_text(encoding="utf-8")
    quoted_lines = find_quoted_lines(text)
    errors = []

    current_count = count_words(text)
    if current_count < target:
        errors.append(f"word count {current_count} is below target {target}")
    if max_words is not None and current_count > max_words:
        errors.append(f"word count {current_count} is above maximum {max_words}")
    errors.extend(find_presentation_errors(text))

    for term in load_blacklist(style_path):
        if term in text:
            errors.append(f"blacklisted term found: {term}")

    return errors


def main(argv=None):
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Validate a novel chapter")
    parser.add_argument("chapter_file", type=Path)
    parser.add_argument(
        "--style",
        type=Path,
        default=repo_root / "writespec" / "style-guide.md",
        help="Style guide containing the blacklist section",
    )
    parser.add_argument("--target", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument(
        "--report-quotes",
        action="store_true",
        help="Enumerate quoted lines as JSON for Agent semantic audit",
    )
    args = parser.parse_args(argv)

    if args.report_quotes:
        text = Path(args.chapter_file).read_text(encoding="utf-8")
        print(json.dumps(find_quoted_lines(text), ensure_ascii=False))
        return 0

    if args.target < 0 or (args.max is not None and args.max < args.target):
        parser.error("--target must be non-negative and --max must be >= --target")

    try:
        errors = validate_chapter(
            args.chapter_file,
            args.style,
            target=args.target,
            max_words=args.max,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[FAIL] cannot validate chapter: {exc}")
        return 1

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] Chapter validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
