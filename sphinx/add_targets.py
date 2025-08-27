import os
import re
import argparse

def generate_target_label(filename_no_ext, heading_text):
    """
    Generates a MyST-compatible target label from a filename and heading text,
    always using the 'ref-' prefix.

    Args:
        filename_no_ext (str): The name of the markdown file without its extension.
        heading_text (str): The raw text of the heading.

    Returns:
        str: A formatted string to be used as an explicit target.
    """
    processed_heading = heading_text.lower()
    processed_heading = re.sub(r'[\s_]+', '-', processed_heading)
    processed_heading = re.sub(r'[^a-z0-9-]', '', processed_heading)
    processed_heading = processed_heading.strip('-')
    return f"(ref-{filename_no_ext}-{processed_heading})="

def process_markdown_file(filepath, level1_only):
    """
    Reads a Markdown file, adds explicit targets before headings if one
    doesn't already exist, and overwrites the file with the new content.

    Args:
        filepath (str): The full path to the Markdown file.
        level1_only (bool): If True, only process level-one headings.
    """
    try:
        filename = os.path.basename(filepath)
        filename_no_ext, _ = os.path.splitext(filename)
        
        print(f"Processing file: {filename}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        modified = False
        
        # --- UPDATED LOGIC: Choose the correct regex pattern ---
        if level1_only:
            # This pattern only matches headings starting with a single '#'
            heading_pattern = re.compile(r'^#\s+(.*)')
            print("  (Mode: Level 1 headings only)")
        else:
            # This pattern matches any heading level
            heading_pattern = re.compile(r'^(#+)\s+(.*)')
        
        # This general pattern correctly identifies any existing target
        existing_target_pattern = re.compile(r'^\([^)]+\)=$')

        for i, current_line in enumerate(lines):
            heading_match = heading_pattern.match(current_line)
            
            # If the current line is not a heading we're interested in, just add it
            if not heading_match:
                new_lines.append(current_line)
                continue

            # Check if the previous line already contains an explicit target
            has_existing_target = False
            if i > 0:
                previous_line = lines[i-1].strip()
                if existing_target_pattern.match(previous_line):
                    has_existing_target = True
            
            # The heading text is group 1 for the H1-only pattern, and group 2 for the general pattern
            heading_text = (heading_match.group(1) if level1_only else heading_match.group(2)).strip()

            if has_existing_target:
                print(f"  - Found existing target for heading: '{heading_text}' -> Skipping.")
                new_lines.append(current_line)
            else:
                print(f"  - Found heading: '{heading_text}' -> Adding new target.")
                target_label = generate_target_label(filename_no_ext, heading_text)
                new_lines.append(target_label + '\n')
                new_lines.append(current_line)
                modified = True

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  -> Successfully updated {filename}\n")
        else:
            print(f"  -> No new targets needed in {filename}.\n")

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

def main(root_directory, level1_only):
    """
    Walks through a directory and processes all Markdown (.md) files.

    Args:
        root_directory (str): The path to the directory containing documentation.
        level1_only (bool): If True, only process level-one headings.
    """
    if not os.path.isdir(root_directory):
        print(f"Error: Directory '{root_directory}' not found.")
        return

    print(f"Starting to scan for Markdown files in '{root_directory}'...\n")
    
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith('.md'):
                full_path = os.path.join(dirpath, filename)
                process_markdown_file(full_path, level1_only)
    
    print("Script finished.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A script to automatically insert explicit heading targets in MyST Markdown files."
    )
    parser.add_argument(
        "directory",
        nargs='?',
        default=".",
        help="The root directory to scan for .md files. Defaults to the current directory."
    )
    # --- NEW COMMAND-LINE FLAG ---
    parser.add_argument(
        '--level1',
        action='store_true',
        help='Only add targets to level 1 headings (e.g., # Heading).'
    )
    args = parser.parse_args()
    
    main(args.directory, args.level1)

