import os
import re

def slugify(text):
    """Converts heading text into a Markdown-style anchor slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def resolve_dest_path(root_dir, current_file, url_path):
    """Resolves relative and absolute internal paths."""
    if not url_path:  # Internal link within the same file (e.g., '#anchor')
        return current_file
    if url_path.startswith('/'):
        return os.path.normpath(os.path.join(root_dir, url_path.lstrip('/')))
    else:
        return os.path.normpath(os.path.join(os.path.dirname(current_file), url_path))

def process_links_for_targets():
    root_dir = os.path.abspath('.')
    link_pattern = re.compile(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)')
    heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$')

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            
            filepath = os.path.join(subdir, file)
            
            # Read the current file to find links
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines):
                matches = link_pattern.finditer(line)
                for match in matches:
                    link_text = match.group(1)
                    url = match.group(2)
                    link_syntax = match.group(0)
                    
                    # Ignore external links and mailto
                    if url.startswith(('http://', 'https://', 'mailto:')):
                        continue

                    # Parse URL into path and anchor
                    parts = url.split('#', 1)
                    url_path = parts[0]
                    anchor = parts[1] if len(parts) > 1 else None

                    # Resolve destination file
                    dest_path = resolve_dest_path(root_dir, filepath, url_path)
                    
                    status_prefix = f"{os.path.relpath(filepath, root_dir)}:{line_idx + 1} - {link_syntax}"

                    # Fallback: If path doesn't exist, try adding .md
                    if not os.path.exists(dest_path) and not dest_path.endswith('.md'):
                        if os.path.exists(dest_path + '.md'):
                            dest_path += '.md'

                    if not os.path.exists(dest_path):
                        print(f"{status_prefix} - error: destination file not found")
                        continue

                    # Check if the resolved path is a directory instead of a file
                    if os.path.isdir(dest_path):
                        if os.path.isfile(os.path.join(dest_path, 'index.md')):
                            dest_path = os.path.join(dest_path, 'index.md')
                        elif os.path.isfile(os.path.join(dest_path, 'README.md')):
                            dest_path = os.path.join(dest_path, 'README.md')
                        elif os.path.isfile(os.path.join(dest_path, 'readme.md')):
                            dest_path = os.path.join(dest_path, 'readme.md')
                        else:
                            print(f"{status_prefix} - error: destination is a directory, but no index.md or README.md found")
                            continue

                    # Read destination file
                    with open(dest_path, 'r', encoding='utf-8') as df:
                        dest_lines = df.readlines()

                    target_idx = -1
                    target_heading_text = ""
                    
                    # Find the target heading
                    for d_idx, d_line in enumerate(dest_lines):
                        heading_match = heading_pattern.match(d_line)
                        if heading_match:
                            h_text = heading_match.group(2).strip()
                            if anchor:
                                if slugify(h_text) == anchor:
                                    target_idx = d_idx
                                    target_heading_text = h_text
                                    break
                            else:
                                # No anchor, grab the very first heading
                                target_idx = d_idx
                                target_heading_text = h_text
                                break
                    
                    if target_idx == -1:
                        print(f"{status_prefix} - error: heading/anchor not found")
                        continue

                    # Create the expected reference string fallback
                    dest_filename = os.path.splitext(os.path.basename(dest_path))[0].replace(' ', '-')
                    expected_ref = f"ref-{dest_filename}_{slugify(target_heading_text)}"
                    ref_line = f"({expected_ref})=\n"

                    # Check if ANY reference already exists on the line above
                    existing_ref_match = None
                    if target_idx > 0:
                        # Matches any string formatted as (something)=
                        existing_ref_match = re.match(r'^\(([^)]+)\)=$', dest_lines[target_idx - 1].strip())
                    
                    if existing_ref_match:
                        existing_ref = existing_ref_match.group(1)
                        print(f"{status_prefix} - exists {existing_ref}")
                    else:
                        # Insert the newly generated reference
                        dest_lines.insert(target_idx, ref_line)
                        with open(dest_path, 'w', encoding='utf-8') as df:
                            df.writelines(dest_lines)
                        print(f"{status_prefix} - created {expected_ref}")

if __name__ == "__main__":
    process_links_for_targets()
