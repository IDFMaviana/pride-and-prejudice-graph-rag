import re
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import paths

def roman_to_int(s):
    #Converts a Roman numeral string to an integer.
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    # Convert to uppercase to handle any case variations like 'i' or 'v'
    s = s.upper()
    num = 0
    for i in range(len(s)):
        if i > 0 and roman_map[s[i]] > roman_map[s[i-1]]:
            num += roman_map[s[i]] - 2 * roman_map[s[i-1]]
        else:
            num += roman_map[s[i]]
    return num

def split_book_into_chapters(input_path, output_dir):
    #Reads a book's text, splits it by chapters, and saves each chapter into a separate file.
   
    print(f"Reading input file: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            book_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Ignores case and handles zero or more periods.
    pattern = re.compile(r'(Chapter [IVXLCDM]+\.*)', re.IGNORECASE)

    parts = pattern.split(book_content)
    
    if len(parts) <= 1:
        print("No chapters were found with the pattern.",sep = "\n")
        return

    chapter_count = 0
    for i in range(1, len(parts), 2):
        try:
            chapter_title = parts[i].strip()
            chapter_content = parts[i+1].strip()

            # Clean the title from periods and split to get the numeral
            roman_numeral = re.sub(r'[.\s]', '', chapter_title.split(' ')[-1])
            chapter_number = roman_to_int(roman_numeral)

            filename = f"Chapter_{chapter_number}.txt"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                # We save the original title as it appeared in the text
                f.write(chapter_title + "\n\n" + chapter_content)
            
            chapter_count += 1
        except (IndexError, KeyError) as e:
            print(f"Warning: Could not process part '{parts[i]}'. Error: {e}")
            
    print(f"Process complete. {chapter_count} chapters were saved.",sep = "\n")


split_book_into_chapters(paths.BOOK_DIR, paths.PRE_PROCESSED_DIR)