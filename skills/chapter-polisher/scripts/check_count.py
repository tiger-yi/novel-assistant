import argparse
import sys
import os

def count_words(text):
    """Simple Chinese word count estimation"""
    # Remove whitespace and common markdown characters
    clean_text = text.replace(' ', '').replace('\n', '').replace('#', '').replace('*', '').replace('>', '')
    return len(clean_text)

def main():
    parser = argparse.ArgumentParser(description='Check word count of a chapter file')
    parser.add_argument('file_path', help='Path to the chapter file')
    parser.add_argument('--target', type=int, default=2000, help='Target word count (default: 2000)')
    parser.add_argument('--segments', action='store_true', help='Output paragraph-level word counts')
    
    args = parser.parse_args()
    
    try:
        with open(args.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        current_count = count_words(content)
        
        print(f"File: {os.path.basename(args.file_path)}")
        print(f"Total Word Count: {current_count}")
        print(f"Target Word Count: {args.target}")
        
        if args.segments:
            print("\n--- Segment Analysis ---")
            paragraphs = content.split('\n')
            segment_idx = 1
            temp_count = 0
            temp_content = []
            
            for p in paragraphs:
                p_count = count_words(p)
                if p_count == 0: continue
                
                temp_count += p_count
                temp_content.append(p)
                
                # Group paragraphs into segments of ~800 words
                if temp_count >= 800:
                    print(f"Segment {segment_idx}: {temp_count} words")
                    segment_idx += 1
                    temp_count = 0
                    temp_content = []
            
            if temp_count > 0:
                print(f"Segment {segment_idx}: {temp_count} words")

        if current_count < args.target:
            diff = args.target - current_count
            print(f"\n❌ Word count check failed! Need {diff} more words.")
            print(f"Status: INCOMPLETE")
        else:
            print(f"\n✅ Word count check passed!")
            print(f"Status: COMPLETE")
            
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
