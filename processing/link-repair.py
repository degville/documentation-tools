import os
import re
import collections

# Regex to find [Text](Link)
LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

def normalize_text(text):
    """Lowercases and removes non-alphanumeric chars for flexible matching."""
    return re.sub(r'\W+', '', text.lower())

def get_md_files():
    """Recursively finds all markdown files from the current directory."""
    md_files = []
    exclude = {'.git', '_build', 'venv', 'node_modules', '.tox', 'site-packages'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def run_repair_tool():
    # Phase 1: Harvesting
    link_library = collections.defaultdict(set)
    md_files = get_md_files()
    
    print(f"--- Phase 1: Scanning {len(md_files)} files for valid targets ---")
    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = LINK_REGEX.findall(content)
                for text, target in matches:
                    if target != "/":
                        link_library[normalize_text(text)].add(target)
        except (UnicodeDecodeError, PermissionError):
            continue

    # Phase 2: Identification and Repair
    print("--- Phase 2: Identifying root links and resolving ---\n")
    for filepath in md_files:
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
                original_full = match.group(0) # [Text](/)
                text = match.group(1)          # Text
                target = match.group(2)        # /
                
                if target != "/":
                    return original_full

                print(f"\n[FOUND] File: {filepath} | Line: {line_num}")
                print(f"Context: {original_full}")
                
                norm = normalize_text(text)
                options = sorted(list(link_library.get(norm, [])))
                
                # Menu Construction
                print("Options:")
                for idx, opt in enumerate(options, 1):
                    suffix = " (Press Enter for this)" if idx == 1 else ""
                    print(f"  {idx}) Use: ({opt}){suffix}")
                
                # Dynamic indices for special actions
                remove_idx = str(len(options) + 1)
                skip_idx = str(len(options) + 2)
                
                print(f"  {remove_idx}) Remove link syntax (Keep text only)")
                print(f"  {skip_idx}) Skip / Ignore")
                print(f"  *) Or just type a custom path/URL and press Enter")
                
                choice = input("\nSelect # or type path [Default=1]: ").strip()
                
                # 1. Handle Default (Enter key)
                if choice == "":
                    if options:
                        file_content_changed = True
                        return f"[{text}]({options[0]})"
                    else:
                        print("No suggestions available. Skipping.")
                        return original_full

                # 2. Handle Numeric selection
                if choice.isdigit():
                    c_int = int(choice)
                    if 1 <= c_int <= len(options):
                        file_content_changed = True
                        return f"[{text}]({options[c_int-1]})"
                    elif choice == remove_idx:
                        file_content_changed = True
                        return text
                    elif choice == skip_idx:
                        return original_full
                
                # 3. Handle Custom Path Input (Anything else)
                file_content_changed = True
                print(f"Applying custom path: {choice}")
                return f"[{text}]({choice})"

            new_line = LINK_REGEX.sub(replace_match, line)
            new_lines.append(new_line)

        if file_content_changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f">>> SAVED: {filepath}")

if __name__ == "__main__":
    run_repair_tool()
