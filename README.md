# documentation-tools
Assorted scripts and tools for processing documentation

- `sphinx/add_targets.py` parses a set of Markdown documentation, identifies all headings, and adds a unique Sphinx MyST reference on the preceding line.
- `sphinx/convert_links.py` parses a set of Markdown documentation, identifies all local Markdown links, checks the destination of the link for a MyST reference, and if one exists replaces the link with a reference.
- `processing/interface-headings.py` edit the second line of all Markdown files in a directory to be a top-level heading with a title based on the filename.
- `processing/multiline-search-replace.py` convenience script to search and replace one or more lines in a directory of text files, with dry run option.
- `processing/link-repair.py` builds a table of known links and their references, identifies null links, and then offers suggests from the table to replace them.
