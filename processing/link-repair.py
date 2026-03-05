import os
import re
import collections

# Regex to find [Text](Link)
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def normalize_text(text):
    """Lowercases and removes non-alphanumeric chars for flexible matching."""
    return re.sub(r'\W+', '', text.lower())

def resolve_path(target_path, current_file_dir):
    """
    Checks if a target exists relative to the current file or project root.
    Handles MyST-style root links (starting with /) and directory indexes.
    """
    if not target_path or target_path == "/":
        return False

    # External links and anchors are assumed valid for this filesystem check
    if target_path.startswith(('http', 'mailto:', '#')):
        return True

    clean_path = target_path.split('#')[0]
    is_myst_root = clean_path.startswith('/')
    internal_path = clean_path.lstrip('/') if is_myst_root else clean_path

    potential_locations = []
    if is_myst_root:
        potential_locations.append(internal_path)
    else:
        # Check relative to file, then relative to root
        potential_locations.append(os.path.normpath(os.path.join(current_file_dir, internal_path)))
        potential_locations.append(internal_path)

    for loc in potential_locations:
        if os.path.exists(loc): return True
        if os.path.exists(loc + ".md"): return True
        if os.path.isdir(loc):
            if any(os.path.exists(os.path.join(loc, f)) for f in ["index.md", "README.md"]):
                return True
    return False

def get_md_files():
    """Recursively finds all markdown files from the current directory."""
    md_files = []
    exclude = {'.git', '_build', 'venv', 'node_modules', '.tox', 'site-packages', 'env'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.normpath(os.path.join(root, file)))
    return md_files

def run_repair_tool():
    link_library = collections.defaultdict(set)
    md_files = get_md_files()
    stats = {"files_modified": 0, "links_fixed": 0}
    
    print(f"--- Phase 1: Harvesting verified links from {len(md_files)} files ---")
    for filepath in md_files:
        current_dir = os.path.dirname(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = LINK_REGEX.findall(content)
                for text, target in matches:
                    if target != "/" and resolve_path(target, current_dir):
                        link_library[normalize_text(text)].add(target)
        except (UnicodeDecodeError, PermissionError):
            continue

    print("--- Phase 2: Validating and repairing broken links ---\n")
    for filepath in md_files:
        current_dir = os.path.dirname(filepath)
        file_content_changed = False
        new_lines = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            continue

        for i, line in enumerate(lines):
            line_num = i + 1
            
            def replace_match(match):
                nonlocal file_content_changed
                original_full = match.group(0)
                text = match.group(1)
                target = match.group(2)
                
                if resolve_path(target, current_dir):
                    return original_full

                print(f"\n[BROKEN] File: {filepath} | Line: {line_num}")
                print(f"Link: {original_full}")
                
                norm = normalize_text(text)
                options = sorted(list(link_library.get(norm, [])))
                
                while True: # Input validation loop
                    print("\nVerified Suggestions:")
                    for idx, opt in enumerate(options, 1):
                        suffix = " (Press Enter for this)" if idx == 1 else ""
                        print(f"  {idx}) Use: ({opt}){suffix}")
                    
                    remove_idx = str(len(options) + 1)
                    skip_idx = str(len(options) + 2)
                    print(f"  {remove_idx}) Remove link syntax")
                    print(f"  {skip_idx}) Skip / Ignore")
                    
                    choice = input("\nSelect # or type custom path: ").strip()
                    
                    # 1. Handle Default/Enter
                    if choice == "":
                        if options:
                            stats["links_fixed"] += 1
                            file_content_changed = True
                            return f"[{text}]({options[0]})"
                        print("!! No suggestions available. Please enter a path or select an option.")
                        continue

                    # 2. Handle Numeric Menu
                    if choice.isdigit():
                        c_int = int(choice)
                        if 1 <= c_int <= len(options):
                            stats["links_fixed"] += 1
                            file_content_changed = True
                            return f"[{text}]({options[c_int-1]})"
                        elif choice == remove_idx:
                            stats["links_fixed"] += 1
                            file_content_changed = True
                            return text
                        elif choice == skip_idx:
                            return original_full
                    
                    # 3. Handle Manual Path Entry with Validation
                    if resolve_path(choice, current_dir):
                        link_library[norm].add(choice)
                        stats["links_fixed"] += 1
                        file_content_changed = True
                        print(f"✓ Path verified and added to library.")
                        return f"[{text}]({choice})"
                    else:
                        print(f"✗ ERROR: Path '{choice}' could not be resolved. Please try again.")

            new_line = LINK_REGEX.sub(replace_match, line)
            new_lines.append(new_line)

        if file_content_changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            stats["files_modified"] += 1
            print(f">>> SAVED: {filepath}")

    print("\n" + "="*30)
    print("REPAIR SUMMARY")
    print(f"Files Modified: {stats['files_modified']}")
    print(f"Links Repaired: {stats['links_fixed']}")
    print("="*30)

if __name__ == "__main__":
    run_repair_tool()
