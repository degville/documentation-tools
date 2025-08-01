import os
import re
import argparse
from urllib.parse import urlparse

def normalize_heading_to_anchor(heading_text):
    """
    Converts a heading string to a Markdown anchor format.
    This logic must be consistent with how Markdown processors generate anchors
    and how the first script generated the target labels.

    Args:
        heading_text (str): The raw text of the heading.

    Returns:
        str: A normalized string suitable for use as an HTML anchor.
    """
    processed_heading = heading_text.lower()
    # Replace spaces and underscores with hyphens
    processed_heading = re.sub(r'[\s_]+', '-', processed_heading)
    # Remove any characters that are not alphanumeric or hyphens
    processed_heading = re.sub(r'[^a-z0-9-]', '', processed_heading)
    # Remove leading/trailing hyphens
    return processed_heading.strip('-')

def find_target_in_file(target_filepath, heading_anchor, cache):
    """
    Finds the explicit MyST target label in a file.
    - If heading_anchor is provided, it looks for the target above that specific heading.
    - If heading_anchor is None or empty, it looks for the target above the *first level-1 heading*.

    Args:
        target_filepath (str): The path to the file to search in.
        heading_anchor (str or None): The anchor of the heading, or None to find the first H1.
        cache (dict): A cache to store results of previous lookups.

    Returns:
        str or None: The found reference label (e.g., 'ref-doc-my-heading-title') or None if not found.
    """
    abs_target_filepath = os.path.abspath(target_filepath)
    # Use a special key for H1 lookups to avoid cache collisions with specific anchor lookups.
    cache_key = (abs_target_filepath, heading_anchor if heading_anchor else "__FIRST_H1__")

    if cache_key in cache:
        return cache[cache_key]

    if not os.path.exists(abs_target_filepath):
        # This warning is now more informative.
        # print(f"    [Warning] Target file for link not found: {target_filepath}")
        cache[cache_key] = None
        return None

    try:
        with open(abs_target_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"    [Error] Could not read target file {target_filepath}: {e}")
        cache[cache_key] = None
        return None

    target_pattern = re.compile(r'^\((ref-[^)]+)\)=$')
    h1_heading_pattern = re.compile(r'^#\s+(.*)')
    any_heading_pattern = re.compile(r'^(#+)\s+(.*)')
    
    prev_line = ""
    for line in lines:
        if heading_anchor:
            heading_match = any_heading_pattern.match(line)
            if heading_match:
                current_heading_text = heading_match.group(2).strip()
                current_anchor = normalize_heading_to_anchor(current_heading_text)
                if current_anchor == heading_anchor:
                    target_match = target_pattern.match(prev_line.strip())
                    if target_match:
                        ref_label = target_match.group(1)
                        cache[cache_key] = ref_label
                        return ref_label
                    else: break 
        else:
            heading_match = h1_heading_pattern.match(line)
            if heading_match:
                target_match = target_pattern.match(prev_line.strip())
                if target_match:
                    ref_label = target_match.group(1)
                    cache[cache_key] = ref_label
                    return ref_label
                else: break
        
        prev_line = line

    cache[cache_key] = None
    return None

def process_markdown_file(filepath, cache, root_dir):
    """
    Reads a Markdown file, finds all internal links, and replaces them
    with MyST cross-references where possible.

    Args:
        filepath (str): The path to the Markdown file to process.
        cache (dict): The cache for storing reference lookups.
        root_dir (str): The absolute path to the documentation root directory.
    """
    try:
        source_dir = os.path.dirname(filepath)
        print(f"Scanning file: {os.path.basename(filepath)}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        link_pattern = re.compile(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)')

        def replace_link_match(match):
            link_text = match.group(1)
            destination = match.group(2)
            
            parsed_url = urlparse(destination)
            
            # Ignore external links (http, https, mailto, etc.)
            if parsed_url.scheme:
                return match.group(0)
            
            link_path = parsed_url.path
            # Ignore anchor-only links like [#my-anchor]
            if not link_path:
                return match.group(0)

            # --- NEW PATH RESOLUTION LOGIC ---
            if link_path.startswith('/'):
                # Path is relative to the documentation root.
                # Remove the leading '/' before joining with the root directory.
                base_path = os.path.join(root_dir, link_path.lstrip('/\\'))
            else:
                # Path is relative to the current file's directory.
                base_path = os.path.join(source_dir, link_path)

            # Add .md extension if it's not present.
            if not base_path.lower().endswith('.md'):
                target_filepath = f"{base_path}.md"
            else:
                target_filepath = base_path
            
            # Normalize path for the current OS (e.g., handles slashes).
            target_filepath = os.path.normpath(target_filepath)
            # --- END NEW LOGIC ---

            heading_anchor = parsed_url.fragment
            
            ref_label = find_target_in_file(target_filepath, heading_anchor, cache)
            
            if ref_label:
                new_link = f"{{ref}}`{ref_label}`"
                print(f"  - Replacing '[{link_text}]({destination})' with '{new_link}'")
                return new_link
            else:
                print(f"  - No target found for link to '{destination}' in resolved path '{target_filepath}'. Keeping original.")
                return match.group(0)

        new_content = link_pattern.sub(replace_link_match, content)

        if new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  -> Successfully updated {os.path.basename(filepath)}\n")
        else:
            print(f"  -> No replaceable links found in {os.path.basename(filepath)}.\n")

    except Exception as e:
        print(f"An unexpected error occurred while processing {filepath}: {e}")

def main(root_directory):
    """
    Main execution function. Walks through a directory and processes all Markdown files.
    """
    abs_root_dir = os.path.abspath(root_directory)
    if not os.path.isdir(abs_root_dir):
        print(f"Error: Directory '{root_directory}' not found.")
        return

    print(f"Starting to convert Markdown links to MyST references in '{abs_root_dir}'...\n")
    
    ref_cache = {}
    
    markdown_files_to_process = []
    for dirpath, _, filenames in os.walk(abs_root_dir):
        for filename in filenames:
            if filename.endswith('.md'):
                markdown_files_to_process.append(os.path.join(dirpath, filename))

    for filepath in markdown_files_to_process:
        process_markdown_file(filepath, ref_cache, abs_root_dir)
    
    print("Script finished.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A script to convert internal Markdown links to MyST cross-references using explicit targets."
    )
    parser.add_argument(
        "directory",
        nargs='?',
        default=".",
        help="The root directory of the documentation to scan for .md files. Defaults to the current directory."
    )
    args = parser.parse_args()
    
    main(args.directory)

