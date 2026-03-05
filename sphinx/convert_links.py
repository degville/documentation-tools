import os
import re

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def resolve_dest_path(root_dir, current_file, url_path):
    if not url_path:
        return current_file
    if url_path.startswith('/'):
        return os.path.normpath(os.path.join(root_dir, url_path.lstrip('/')))
    else:
        return os.path.normpath(os.path.join(os.path.dirname(current_file), url_path))

def replace_links_with_myst():
    root_dir = os.path.abspath('.')
    link_pattern = re.compile(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)')
    heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$')
    # Updated to capture ANY reference string inside the parentheses
    ref_pattern = re.compile(r'^\(([^)]+)\)=$')

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            
            filepath = os.path.join(subdir, file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            file_modified = False
            
            # We iterate backwards through lines so modifications don't mess up our line indices
            for line_idx in range(len(lines) - 1, -1, -1):
                line = lines[line_idx]
                
                # Find all links on the current line
                matches = list(link_pattern.finditer(line))
                
                # Process matches backwards so character replacement indices remain stable
                for match in reversed(matches):
                    link_text = match.group(1)
                    url = match.group(2)
                    link_syntax = match.group(0)
                    start_char, end_char = match.span()

                    if url.startswith(('http://', 'https://', 'mailto:')):
                        continue

                    parts = url.split('#', 1)
                    url_path = parts[0]
                    anchor = parts[1] if len(parts) > 1 else None
                    dest_path = resolve_dest_path(root_dir, filepath, url_path)
                    status_prefix = f"{os.path.relpath(filepath, root_dir)}:{line_idx + 1} - {link_syntax}"

                    # Fallback: If path doesn't exist, try adding .md
                    if not os.path.exists(dest_path) and not dest_path.endswith('.md'):
                        if os.path.exists(dest_path + '.md'):
                            dest_path += '.md'

                    if not os.path.exists(dest_path):
                        print(f"{status_prefix} - error: destination file not found during replacement")
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

                    with open(dest_path, 'r', encoding='utf-8') as df:
                        dest_lines = df.readlines()

                    target_idx = -1
                    
                    for d_idx, d_line in enumerate(dest_lines):
                        heading_match = heading_pattern.match(d_line)
                        if heading_match:
                            h_text = heading_match.group(2).strip()
                            if anchor:
                                if slugify(h_text) == anchor:
                                    target_idx = d_idx
                                    break
                            else:
                                target_idx = d_idx
                                break
                    
                    if target_idx == -1 or target_idx == 0:
                        print(f"{status_prefix} - error: target or reference missing")
                        continue

                    # Look at the line immediately preceding the target heading
                    ref_match = ref_pattern.match(dest_lines[target_idx - 1].strip())
                    if ref_match:
                        ref_string = ref_match.group(1)
                        # Construct MyST syntax: {ref}`Link Text <ref-string>`
                        myst_link = f"{{ref}}`{link_text} <{ref_string}>`"
                        
                        # Replace the string in the current line
                        line = line[:start_char] + myst_link + line[end_char:]
                        lines[line_idx] = line
                        file_modified = True
                        print(f"{status_prefix} - replaced {ref_string}")
                    else:
                        print(f"{status_prefix} - error: reference tag missing above heading")

            if file_modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

if __name__ == "__main__":
    replace_links_with_myst()
