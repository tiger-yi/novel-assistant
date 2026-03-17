import sys
import os

def read_file(path):
    print(f"\n--- FILE: {path} ---")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"[ERROR] File not found: {path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python load_context.py <chapter_file_path>")
        sys.exit(1)

    chapter_path = sys.argv[1]
    
    # Read Chapter
    read_file(chapter_path)

    # Read World Bible Files
    world_dir = "world"
    bible_files = [
        "characters.toml",
        "timeline.md",
        "inventory.md",
        "geography.md",
        "power.md"
    ]

    for bf in bible_files:
        read_file(os.path.join(world_dir, bf))

    # Read Skill References
    ref_dir = os.path.join(".trae", "skills", "chapter-polisher", "references")
    ref_files = [
        "narrative-refactor.md",
        "physical-descriptor.md",
        "world_validation_examples.md"
    ]

    for rf in ref_files:
        read_file(os.path.join(ref_dir, rf))

if __name__ == "__main__":
    main()
