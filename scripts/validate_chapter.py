import argparse
import re
import sys
from pathlib import Path

try:
    from scripts.check_count import count_words
except ModuleNotFoundError:
    from check_count import count_words


BLACKLIST_HEADING = "### 黑名单词"
BLACKLIST_ITEM = re.compile(r"^\s*[*+-]\s+(.+?)\s*$")
MARKDOWN_BLOCKS = (
    re.compile(r"^\s*#{1,6}\s+"),
    re.compile(r"^\s*(?:[-+*]\s+|\d+\.\s+)"),
    re.compile(r"^\s*\|.*\|\s*$"),
)
FORBIDDEN_SYMBOLS = ("【", "】", "[", "]", "（", "）", "**")


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


def validate_chapter(chapter_path, style_path, target=2000):
    chapter_path = Path(chapter_path)
    text = chapter_path.read_text(encoding="utf-8")
    errors = []

    current_count = count_words(text)
    if current_count < target:
        errors.append(f"word count {current_count} is below target {target}")

    for symbol in FORBIDDEN_SYMBOLS:
        if symbol in text:
            errors.append(f"forbidden symbol found: {symbol}")

    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in MARKDOWN_BLOCKS):
            errors.append(f"Markdown block found at line {line_number}")

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
    parser.add_argument("--target", type=int, default=2000)
    args = parser.parse_args(argv)

    try:
        errors = validate_chapter(args.chapter_file, args.style, args.target)
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
