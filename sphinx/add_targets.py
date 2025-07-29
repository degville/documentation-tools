import os
import re
import argparse

def generate_target_label(filename_no_ext, heading_text):
    """
    Generates a MyST-compatible target label from a filename and heading text.

    Args:
        filename_no_ext (str): The name of the markdown file without its extension.
        heading_text (str): The raw text of the heading.

    Returns:
        str: A formatted string to be used as an explicit target.
    """
    # Convert heading to lowercase
    processed_heading = heading_text.lower()
    
    # Replace spaces and other common separators with hyphens
    processed_heading = re.sub(r'[\s_]+', '-', processed_heading)
    
    # Remove any characters that are not alphanumeric or hyphens
    processed_heading = re.sub(r'[^a-z0-9-]', '', processed_heading)
    
    # Remove leading/trailing hyphens that might have been created
    processed_heading = processed_heading.strip('-')

    # Construct the final target label
    return f"(ref-{filename_no_ext}-{processed_heading})="

def process_markdown_file(filepath):
    """
    Reads a Markdown file, adds explicit targets before each heading,
    and overwrites the file with the new content.

    Args:
        filepath (str): The full path to the Markdown file.
    """
    try:
        filename = os.path.basename(filepath)
        filename_no_ext, _ = os.path.splitext(filename)
        
        print(f"Processing file: {filename}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        modified = False
        
        # Regex to find markdown headings (e.g., #, ##, ###)
        heading_pattern = re.compile(r'^(#+)\s+(.*)')

        for line in lines:
            match = heading_pattern.match(line)
            if match:
                # Extract the heading text (group 2 of the match)
                heading_text = match.group(2).strip()
                
                # Generate the target label
                target_label = generate_target_label(filename_no_ext, heading_text)
                
                # Add the target label on a new line directly before the heading
                new_lines.append(target_label + '\n')
                # The extra blank line that was here has been removed.
                modified = True
                print(f"  - Found heading: '{heading_text}' -> Added target: '{target_label}'")

            new_lines.append(line)

        # If modifications were made, write the new content back to the file
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  -> Successfully updated {filename}\n")
        else:
            print(f"  -> No headings found in {filename}. No changes made.\n")

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
    
    # Walk through the directory tree
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith('.md'):
                full_path = os.path.join(dirpath, filename)
                process_markdown_file(full_path)
    
    print("Script finished.")

if __name__ == '__main__':
    # --- Configuration ---
    # Set the root directory of your documentation here.
    # The script will search this directory and all its subdirectories.
    # Example: DOCS_ROOT_DIR = "./my-book/docs"
    DOCS_ROOT_DIR = "./docs" 
    # ---------------------

    # Set up argument parser to allow command-line override of the directory
    parser = argparse.ArgumentParser(
        description="A script to automatically insert explicit heading targets in MyST Markdown files."
    )
    parser.add_argument(
        "directory",
        nargs='?', # Makes the argument optional
        default=DOCS_ROOT_DIR,
        help=f"The root directory to scan for .md files. Defaults to '{DOCS_ROOT_DIR}' if not provided."
    )
    args = parser.parse_args()

    # It's always a good idea to have a backup of your files before running a script like this!
    # input("Press Enter to continue after backing up your files...")
    
    main(args.directory)

