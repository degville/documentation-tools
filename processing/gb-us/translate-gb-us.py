import os
import re
import argparse
import urllib.request
from pathlib import Path

def load_dictionary(source_path):
    """
    Parses the dictionary file from either a local file path or a web URL.
    Expects lines in the format: 'us_word': 'gb_word',
    """
    us_to_gb = {}
    gb_to_us = {}
    
    # 1. Determine if the source is a URL or a local file
    if source_path.startswith('http://') or source_path.startswith('https://'):
        print(f"Downloading dictionary from URL: {source_path}...")
        # A basic User-Agent header helps prevent some servers from blocking the request
        req = urllib.request.Request(source_path, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            lines = response.read().decode('utf-8').splitlines()
    else:
        print(f"Loading dictionary from local file: {source_path}...")
        with open(source_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
    # 2. Parse the lines
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.endswith(','):
            line = line[:-1]
            
        parts = line.split(':', 1)
        if len(parts) == 2:
            us_word = parts[0].strip().strip("'\"").lower()
            gb_word = parts[1].strip().strip("'\"").lower()
            
            us_to_gb[us_word] = gb_word
            gb_to_us[gb_word] = us_word
            
    return us_to_gb, gb_to_us

def create_replacement_function(mapping_dict):
    """
    Returns a regex replacement function that preserves the original case.
    """
    def replace_match(match):
        word = match.group(0)
        lower_word = word.lower()
        replacement = mapping_dict.get(lower_word, word)
        
        if word.isupper() and len(word) > 1:
            return replacement.upper()
        elif word.istitle():
            return replacement.capitalize()
        else:
            return replacement
            
    return replace_match

def process_directory(directory, mapping_dict):
    """
    Recursively scans for .md files and replaces words in-place.
    """
    if not mapping_dict:
        print("Dictionary is empty. Exiting.")
        return

    # Compile a single regex pattern for all words
    escaped_words = [re.escape(w) for w in mapping_dict.keys()]
    pattern = re.compile(r'\b(' + '|'.join(escaped_words) + r')\b', re.IGNORECASE)
    replace_func = create_replacement_function(mapping_dict)
    
    md_files = list(Path(directory).rglob('*.md'))
    
    if not md_files:
        print(f"No Markdown files found in '{directory}'.")
        return

    files_modified = 0

    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        new_content, num_subs = pattern.subn(replace_func, content)
        
        if num_subs > 0:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Updated {num_subs} word(s) in: {filepath}")
            files_modified += 1
            
    print(f"\nFinished processing. Modified {files_modified} out of {len(md_files)} files.")

def main():
    parser = argparse.ArgumentParser(description="Convert between US and UK spelling in Markdown files.")
    parser.add_argument("directory", help="The target directory containing .md files to scan.")
    parser.add_argument("--dict", default="us-gb-dict.txt", help="Path or URL to the dictionary file.")
    parser.add_argument("--mode", choices=['to-us', 'to-gb'], default='to-us', 
                        help="Direction of conversion. 'to-us' (GB->US) is default.")
    
    args = parser.parse_args()

    # Verify local files exist (skip check if it's a URL)
    if not args.dict.startswith('http') and not os.path.exists(args.dict):
        print(f"Error: Local dictionary file '{args.dict}' not found.")
        return
        
    if not os.path.exists(args.directory):
        print(f"Error: Target directory '{args.directory}' not found.")
        return

    # Load the dictionary with error handling for web requests
    try:
        us_to_gb, gb_to_us = load_dictionary(args.dict)
    except Exception as e:
        print(f"Error loading dictionary: {e}")
        return
    
    if args.mode == 'to-us':
        print("Mode: British to American (Default)")
        mapping_dict = gb_to_us
    else:
        print("Mode: American to British")
        mapping_dict = us_to_gb
        
    print(f"Loaded {len(mapping_dict)} translation pairs.")
    print(f"Scanning directory: {args.directory}...\n")
    
    process_directory(args.directory, mapping_dict)

if __name__ == "__main__":
    main()
