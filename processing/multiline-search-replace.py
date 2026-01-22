import os

# --- CONFIGURATION ---
TARGET_DIRECTORY = './docs'  # Path to your directory
IS_DRY_RUN = True            # Set to False to actually write changes

# Define the MULTILINE block you want to find
SEARCH_TEXT = """## Old Header
This is the old paragraph that spans
multiple lines and needs to be replaced."""

# Define the MULTILINE block to replace it with
REPLACE_TEXT = """## New Header
This is the updated content that is 
much better and cleaner."""
# ---------------------

def batch_replace_markdown(directory, search, replace, dry_run=True):
    files_modified = 0
    errors = 0

    print(f"--- Starting Scan in '{directory}' ---")
    if dry_run:
        print(">>> DRY RUN MODE: No files will be modified. <<<\n")

    # Walk through directory recursively
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                
                try:
                    # Read the file
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if the exact search text exists in the file
                    if search in content:
                        print(f"Match found in: {filepath}")
                        
                        if not dry_run:
                            # Perform replacement
                            new_content = content.replace(search, replace)
                            
                            # Write changes back
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"  -> Replaced and saved.")
                        else:
                            print(f"  -> [Dry Run] Would replace content here.")
                        
                        files_modified += 1
                        
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    errors += 1

    print("\n--- Summary ---")
    print(f"Files matched/modified: {files_modified}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    # Ensure the directory exists before running
    if os.path.exists(TARGET_DIRECTORY):
        batch_replace_markdown(TARGET_DIRECTORY, SEARCH_TEXT, REPLACE_TEXT, IS_DRY_RUN)
    else:
        print(f"Directory not found: {TARGET_DIRECTORY}")
