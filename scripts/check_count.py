import argparse
import os
import sys
import unicodedata


DEFAULT_MIN_WORDS = 2300
DEFAULT_MAX_WORDS = 2800


def count_words(text):
    """Count letters and numbers while excluding layout and punctuation."""
    excluded_categories = {"C", "P", "S", "Z"}
    return sum(
        1
        for character in text
        if unicodedata.category(character)[0] not in excluded_categories
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check word count of a chapter file')
    parser.add_argument('file_path', help='Path to the chapter file')
    parser.add_argument(
        '--target',
        type=int,
        default=DEFAULT_MIN_WORDS,
        help=f'Minimum word count (default: {DEFAULT_MIN_WORDS})',
    )
    parser.add_argument(
        '--max',
        type=int,
        default=DEFAULT_MAX_WORDS,
        help=f'Maximum word count (default: {DEFAULT_MAX_WORDS})',
    )
    parser.add_argument('--segments', action='store_true', help='Output paragraph-level word counts')

    args = parser.parse_args(argv)

    if args.target < 0 or (args.max is not None and args.max < args.target):
        parser.error('--target must be non-negative and --max must be >= --target')

    try:
        with open(args.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        current_count = count_words(content)

        print(f"File: {os.path.basename(args.file_path)}")
        print(f"Total Word Count: {current_count}")
        if args.max is None:
            print(f"Target Word Count: >= {args.target}")
        else:
            print(f"Target Word Count: {args.target}-{args.max}")

        if args.segments:
            print("\n--- Segment Analysis ---")
            paragraphs = content.split('\n')
            segment_idx = 1
            temp_count = 0

            for p in paragraphs:
                p_count = count_words(p)
                if p_count == 0:
                    continue

                temp_count += p_count

                # Group paragraphs into segments of ~800 words
                if temp_count >= 800:
                    print(f"Segment {segment_idx}: {temp_count} words")
                    segment_idx += 1
                    temp_count = 0

            if temp_count > 0:
                print(f"Segment {segment_idx}: {temp_count} words")

        if current_count < args.target:
            diff = args.target - current_count
            print(f"\n[FAIL] Word count too low! Need {diff} more words.")
            print(f"Status: INCOMPLETE")
            return 1
        if args.max is not None and current_count > args.max:
            diff = current_count - args.max
            print(f"\n[FAIL] Word count too high! Need to trim {diff} words.")
            print(f"Status: TOO_LONG")
            return 1

        print(f"\n[PASS] Word count within target range!")
        print(f"Status: COMPLETE")
        return 0

    except (OSError, UnicodeError) as e:
        print(f"Error reading file: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
