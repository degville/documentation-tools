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

def process_markdown_file(filepath):
    """
    Reads a Markdown file, adds explicit targets before each heading if one
    doesn't already exist, and overwrites the file with the new content.

    Args:
        filepath (str): The full path to the Markdown file.
    """
    try:
        filename = os.path.basename(filepath)
        filename_no_ext, _ = os.path.splitext(filename)
        
        print(f"Processing file: {filename}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # We must process the file content as a single list of lines to correctly
        # handle the lookbehind check for existing targets.
        output_lines = []
        modified = False
        
        heading_pattern = re.compile(r'^(#+)\s+(.*)')
        # --- UPDATED LOGIC ---
        # This regex is now more general. It will match any valid explicit target
        # of the format `(some-label)=`, not just ones starting with `ref-`.
        existing_target_pattern = re.compile(r'^\([^)]+\)=$')

        # Keep track of the previous line to check for existing targets.
        previous_line = ""
        for current_line in lines:
            heading_match = heading_pattern.match(current_line)
            
            if not heading_match:
                output_lines.append(current_line)
                previous_line = current_line
                continue

            # This is a heading line. Check the previous line for a target.
            heading_text = heading_match.group(2).strip()
            
            if existing_target_pattern.match(previous_line.strip()):
                # A valid target already exists. Do nothing.
                print(f"  - Found existing target for heading: '{heading_text}' -> Skipping.")
                output_lines.append(current_line)
            else:
                # No existing target. Generate and insert a new one.
                print(f"  - Found heading: '{heading_text}' -> Adding new target.")
                target_label = generate_target_label(filename_no_ext, heading_text)
                output_lines.append(target_label + '\n')
                output_lines.append(current_line)
                modified = True
            
            previous_line = current_line

        # If modifications were made, write the new content back to the file
        if modified:
            # We need to reconstruct the file content.
            # Using a temporary list and then writing is safer.
            final_content = "".join(output_lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"  -> Successfully updated {filename}\n")
        else:
            print(f"  -> No new targets needed in {filename}.\n")

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")

def main(root_directory):
    """
    Walks through a directory and processes all Markdown (.md) files.

    Args:
        root_directory (str): The path to the directory containing documentation.
    """
    if not os.path.isdir(root_directory):
        print(f"Error: Directory '{root_directory}' not found.")
        return

    print(f"Starting to scan for Markdown files in '{root_directory}'...\n")
    
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith('.md'):
                full_path = os.path.join(dirpath, filename)
                # I've simplified the logic to process one file at a time
                # as the original implementation was slightly flawed.
                # This new approach is more robust.
                
                # To do this correctly, we need to read all lines, process them,
                # and then write back.
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_lines = []
                modified = False
                
                for i, line in enumerate(lines):
                    heading_match = re.match(r'^(#+)\s+(.*)', line)
                    if heading_match:
                        # Check if previous line exists and if it's a target
                        if i > 0 and re.match(r'^\([^)]+\)=$', lines[i-1].strip()):
                            # Already has a target, do nothing
                            pass
                        else:
                            # Add a new target
                            filename_no_ext, _ = os.path.splitext(os.path.basename(full_path))
                            heading_text = heading_match.group(2).strip()
                            target_label = generate_target_label(filename_no_ext, heading_text)
                            new_lines.append(target_label + '\n')
                            modified = True
                    new_lines.append(line)

                if modified:
                    print(f"Updating file: {full_path}")
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)

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
    args = parser.parse_args()
    
    # I've simplified the main loop to be more direct and correct.
    # The original main function was calling a processing function that had a slightly
    # different logic. This consolidated version is clearer.
    root_dir = args.directory
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
    else:
        print(f"Starting to scan for Markdown files in '{root_dir}'...\n")
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith('.md'):
                    process_markdown_file(os.path.join(dirpath, filename))
        print("\nScript finished.")

