# documentation-tools
Assorted scripts and tools for processing documentation

- `sphinx/add_targets.py` parses a set of Markdown documentation, identifies all headings, and adds a unique Sphinx MyST reference on the preceding line.
- `sphinx/convert_links.py` parses a set of Markdown documentation, identifies all local Markdown links, checks the destination of the link for a MyST reference, and if one exists replaces the link with a reference.
- `processing/interface-headings.py` edit the second line of all Markdown files in a directory to be a top-level heading with a title based on the filename.
