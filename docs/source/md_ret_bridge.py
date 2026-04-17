import os
from pathlib import Path

# --- Configurable paths ---
# Path to your original Markdown repo
SOURCE_MD_ROOT = Path("/home/ahmed-yousri/Workspace/code-Kingdom/aCupOfTea")

# Path to Sphinx docs source directory
SPHINX_SOURCE_ROOT = Path("/home/ahmed-yousri/Workspace/code-Kingdom/aCupOfTea/docs/source")

# Directories to process (relative to SOURCE_MD_ROOT)
TARGET_DIRS = ["tips", 'programming', 'journal', 'fields']  # Add any top-level directories you want

# Template for each .rst file
RST_TEMPLATE = """{title}
{underline}

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. include::
    {rel_md_path}
   :parser: myst_parser.sphinx_
"""

# --- Helper functions ---
def create_rst_for_md(md_path: Path, rst_path: Path):
    """Create a .rst wrapper for a Markdown file"""
    title = md_path.stem.replace("_", " ").title()
    underline = "=" * len(title)

    # Compute relative path from rst file to the original Markdown
    rel_md_path = os.path.relpath(md_path, rst_path.parent)

    content = RST_TEMPLATE.format(title=title, underline=underline, rel_md_path=rel_md_path.replace("\\", "/"))

    rst_path.parent.mkdir(parents=True, exist_ok=True)
    rst_path.write_text(content, encoding="utf-8")
    print(f"Created {rst_path}")

def create_index_rst(folder_path: Path):
    """Create index.rst for a folder listing both .rst files and sub-directories"""
    # 1. Get sub-directories that contain an index.rst (or will soon)
    subdirs = sorted([
        d.name for d in folder_path.iterdir() 
        if d.is_dir() and not d.name.startswith('.')
    ])

    # 2. Get .rst files (excluding index.rst itself)
    rst_files = sorted([
        f.stem for f in folder_path.glob("*.rst") 
        if f.name != "index.rst"
    ])

    # If there's nothing to show, we still create an index if it's a target dir
    # to maintain Sphinx tree integrity, or we return if truly empty.
    if not subdirs and not rst_files:
        return

    index_path = folder_path / "index.rst"
    title = folder_path.name.replace("_", " ").title()
    underline = "=" * len(title)
    
    content = f"{title}\n{underline}\n\n.. toctree::\n   :maxdepth: 2\n\n"
    
    # Add sub-directories first (links to their index.rst)
    for d in subdirs:
        content += f"   {d}/index\n"
        
    # Add individual rst files
    for f in rst_files:
        content += f"   {f}\n"

    index_path.write_text(content, encoding="utf-8")
    print(f"Created index: {index_path}")

# --- Revised Main Loop ---
# We use top-down=False or process indices after the walk to ensure 
# children exist before the parent index tries to map them.
for top_dir in TARGET_DIRS:
    md_dir = SOURCE_MD_ROOT / top_dir
    if not md_dir.exists():
        continue

    # Walk and create .rst wrappers first
    for root, dirs, files in os.walk(md_dir):
        rel_root = Path(root).relative_to(SOURCE_MD_ROOT)
        target_root = SPHINX_SOURCE_ROOT / rel_root
        
        for f in files:
            if f.endswith(".md"):
                md_path = Path(root) / f
                rst_path = target_root / f"{md_path.stem}.rst"
                create_rst_for_md(md_path, rst_path)

    # Walk again (bottom-up) to create indices 
    # This ensures child folders have their index.rst before the parent looks for them
    for root, dirs, files in os.walk(SPHINX_SOURCE_ROOT / top_dir, topdown=False):
        create_index_rst(Path(root))

# --- Main script ---
for top_dir in TARGET_DIRS:
    md_dir = SOURCE_MD_ROOT / top_dir
    if not md_dir.exists():
        print(f"Skipping missing directory: {md_dir}")
        continue

    for root, dirs, files in os.walk(md_dir):
        rel_root = Path(root).relative_to(SOURCE_MD_ROOT)
        target_root = SPHINX_SOURCE_ROOT / rel_root

        # Process Markdown files
        for f in files:
            if f.endswith(".md"):
                md_path = Path(root) / f
                rst_path = target_root / f"{md_path.stem}.rst"
                create_rst_for_md(md_path, rst_path)

        # Create index.rst in this folder
        create_index_rst(target_root)