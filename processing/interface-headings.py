import os
import glob

def update_markdown_files():
    """
    Finds all '*-interface.md' files in the current directory
    and replaces their second line with a formatted title.
    """
    # Use glob to find all files matching the pattern
    target_files = glob.glob('*-interface.md')

    if not target_files:
        print("No matching Markdown files found (e.g., 'xilinx-dma-interface.md').")
        return

    for filepath in target_files:
        try:
            # --- Extract the 'something' part from the filename ---
            # Get just the filename from the path
            filename = os.path.basename(filepath)
            # Remove the suffix to get the base name
            base_name = filename.replace('-interface.md', '')

            # --- Construct the new second line ---
            new_second_line = f"# The {base_name} interface\n"

            # --- Read the existing file content ---
            with open(filepath, 'r') as file:
                lines = file.readlines()

            # --- Replace the second line ---
            if len(lines) >= 2:
                print(f"Updating file: {filename}")
                print(f"  - Old line 2: {lines[1].strip()}")
                lines[1] = new_second_line
                print(f"  + New line 2: {new_second_line.strip()}")
            else:
                # If there's no second line, we can't replace it.
                print(f"Skipping {filename}: File has fewer than two lines.")
                continue

            # --- Write the modified content back to the file ---
            with open(filepath, 'w') as file:
                file.writelines(lines)

            print(f"Successfully processed {filename}.\n")

        except Exception as e:
            print(f"An error occurred while processing {filepath}: {e}\n")

if __name__ == "__main__":
    # To make this script runnable, you can create a sample file.
    # For example, create a file named 'xilinx-dma-interface.md'
    # with the following content and then run this script.
    #
    # Line 1: Some introductory text.
    # Line 2: This is the line to be replaced.
    # Line 3: More content here.
    #
    update_markdown_files()
