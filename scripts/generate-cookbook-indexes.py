#!/usr/bin/env python3
"""
Generate cookbook index markdown files based on navigation structure.

This script creates auto-populated markdown files by scanning .nav.yml files
and extracting metadata from referenced markdown files.
"""

import os
import sys
import yaml
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

# Regex for robust frontmatter parsing
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# Common acronyms to preserve
ACRONYMS = {'API', 'SDK', 'CLI', 'AI', 'ML', 'CPU', 'GPU', 'EVM', 'PVM', 'NFT', 'DApp'}

# Auto-generation markers
AUTO_START = "<!-- START OF AUTOMATICALLY GENERATED CONTENT -->"
AUTO_END = "<!-- END OF AUTOMATICALLY GENERATED CONTENT -->"


@lru_cache(maxsize=4096)
def extract_frontmatter(file_path: str) -> Dict[str, str]:
    """
    Robustly parse YAML frontmatter at the top of a markdown file.
    Tolerates UTF-8 BOM, CRLF, and missing trailing newline.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Dictionary containing title, tools, and description
    """
    try:
        with open(file_path, 'rb') as fb:
            raw = fb.read()

        # Strip BOM if present
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]

        text = raw.decode('utf-8', errors='replace')
        lines = text.splitlines()

        if not lines or lines[0].strip() != '---':
            return {}

        # Collect YAML block until the next '---' on its own line
        yaml_lines = []
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                break
            yaml_lines.append(lines[i])
        else:
            # No closing fence
            return {}

        frontmatter = yaml.safe_load('\n'.join(yaml_lines)) or {}
        tools = frontmatter.get('tools', '')
        if isinstance(tools, list):
            tools = ', '.join(str(t) for t in tools)

        return {
            'title': str(frontmatter.get('title') or '').strip(),
            'tools': str(tools or '').strip(),
            'description': str(frontmatter.get('description') or '').strip(),
        }
    except Exception as e:
        print(f"⚠️  Error reading frontmatter from {file_path}: {e}")
        return {}


def load_nav_file(nav_path: str) -> List[Dict]:
    """
    Load and parse a .nav.yml file.
    
    Args:
        nav_path: Path to the .nav.yml file
        
    Returns:
        List of navigation items
    """
    try:
        with open(nav_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Allow either {'nav': [...]} or [...] at top-level
        if isinstance(data, dict) and 'nav' in data and isinstance(data['nav'], list):
            return data['nav']
        if isinstance(data, list):
            return data
        
        print(f"⚠️  Unexpected nav structure in {nav_path} (got {type(data).__name__})")
        return []
    
    except Exception as e:
        print(f"❌ Error loading nav file {nav_path}: {e}")
        return []


def resolve_path(base_path: str, nav_path: str, workspace_root: str) -> str:
    """
    Resolve navigation path relative to workspace root with security validation.
    
    Args:
        base_path: Base directory where nav file is located
        nav_path: Path from navigation file
        workspace_root: Root directory of workspace
        
    Returns:
        Resolved absolute path
        
    Raises:
        ValueError: If the resolved path would escape the workspace root
    """
    # Normalize the nav_path to prevent path traversal
    nav_path = os.path.normpath(nav_path)
    
    if nav_path.startswith('/'):
        # Absolute path from content root (polkadot-docs), not workspace root
        # Find the content directory by looking for polkadot-docs
        content_root = None
        current = base_path
        while current and current != workspace_root:
            if os.path.basename(current) == 'polkadot-docs':
                content_root = current
                break
            current = os.path.dirname(current)
        
        if not content_root:
            # Fallback to workspace root if we can't find polkadot-docs
            content_root = workspace_root
        
        resolved_path = os.path.join(content_root, nav_path.lstrip('/'))
    else:
        # Relative path from base directory
        resolved_path = os.path.join(base_path, nav_path)
    
    # Resolve to absolute path and validate it's within workspace
    resolved_path = Path(resolved_path).resolve()
    workspace_root_path = Path(workspace_root).resolve()
    
    # Check if the resolved path is within the workspace root
    try:
        resolved_path.relative_to(workspace_root_path)
    except ValueError:
        raise ValueError(f"Path traversal detected: {nav_path} resolves outside workspace root")
    
    return str(resolved_path)


def to_site_path(abs_path: str, workspace_root: str) -> str:
    """
    Convert absolute path to site-relative path for MkDocs.
    
    Args:
        abs_path: Absolute file path
        workspace_root: Root directory of workspace
        
    Returns:
        Site-relative path with leading slash
    """
    rel = os.path.relpath(abs_path, workspace_root).replace('\\', '/')
    if rel.endswith('.md'):
        rel = rel[:-3]  # strip .md suffix only
    if not rel.startswith('/'):
        rel = '/' + rel
    return rel


def create_markdown_link(title: str, abs_path: str, workspace_root: str) -> str:
    """
    Create a markdown link for MkDocs Material.
    
    Args:
        title: Link text
        abs_path: Absolute path to target file
        workspace_root: Root directory of workspace
        
    Returns:
        Formatted markdown link
    """
    try:
        return f"[{title}]({to_site_path(abs_path, workspace_root)})"
    except Exception:
        return title


def escape_table_cell(text: str) -> str:
    """
    Escape special characters in table cell content to prevent markdown corruption.
    
    Args:
        text: The content to escape
        
    Returns:
        Escaped content safe for use in markdown tables
    """
    s = str(text or '')
    s = s.replace('|', r'\|').replace('`', r'\`').replace('\n', ' ')
    return s.strip()


def format_tools(tools_csv: str) -> str:
    """
    Format tools string with proper capitalization and normalized delimiters.
    
    Args:
        tools_csv: Comma or semicolon-separated string of tools
        
    Returns:
        Formatted tools string
    """
    if not tools_csv:
        return 'N/A'
    
    # Accept semicolons as well as commas
    raw_parts = re.split(r'[;,]', tools_csv)
    parts = [re.sub(r'\s+', ' ', p).strip() for p in raw_parts if p.strip()]
    
    out = []
    for t in parts:
        if t.upper() in ACRONYMS:
            out.append(t.upper())
        elif t.islower() and ' ' not in t:
            out.append(t.capitalize())
        else:
            out.append(t)
    
    return ', '.join(out) if out else 'N/A'


def make_table_row(md_path: str, workspace_root: str) -> Optional[str]:
    """
    Create a table row from a markdown file's frontmatter.
    
    Args:
        md_path: Path to the markdown file
        workspace_root: Root directory of workspace
        
    Returns:
        Formatted table row or None if missing required fields
    """
    fm = extract_frontmatter(md_path)
    title = fm.get('title', '')
    desc = fm.get('description', '')
    tools = format_tools(fm.get('tools', ''))
    
    if not title or not desc:
        return None
        
    link_title = create_markdown_link(title, md_path, workspace_root)
    return f"| {escape_table_cell(link_title)} | {escape_table_cell(tools)} | {escape_table_cell(desc)} |"


def format_tools(tools_csv: str) -> str:
    """
    Format tools string with smart capitalization.
    
    Args:
        tools_csv: Comma-separated tools string
        
    Returns:
        Formatted tools string
    """
    parts = [t.strip() for t in tools_csv.split(',') if t.strip()]
    out = []
    for t in parts:
        if t.upper() in ACRONYMS:
            out.append(t.upper())
        elif t.islower() and ' ' not in t:
            out.append(t.capitalize())
        else:
            out.append(t)
    return ', '.join(out) if out else 'N/A'


def find_workspace_root(start: str) -> Optional[str]:
    """
    Find workspace root by looking for mkdocs.yml.
    
    Args:
        start: Starting directory to search from
        
    Returns:
        Path to workspace root or None if not found
    """
    p = Path(start).resolve()
    for cur in [p, Path(__file__).resolve().parent]:
        q = cur
        while True:
            if (q / 'mkdocs.yml').exists():
                return str(q)
            if q.parent == q:
                break
            q = q.parent
    return None


def process_nav_items(nav_items: List[Dict], base_path: str, workspace_root: str, 
                     content_dir: str) -> List[str]:
    """
    Process navigation items and generate markdown content.
    
    Args:
        nav_items: List of navigation items from .nav.yml
        base_path: Base directory where nav file is located
        workspace_root: Root directory of workspace
        content_dir: Directory being scanned for content
        
    Returns:
        List of markdown lines
    """
    content_lines = []
    
    for item in nav_items:
        if isinstance(item, dict):
            for title, path in item.items():
                # Skip index.md entries (including subdirectories)
                if os.path.basename(path) == 'index.md':
                    continue
                
                # Resolve the full path with security validation
                try:
                    resolved_path = resolve_path(base_path, path, workspace_root)
                except ValueError as e:
                    print(f"⚠️  Security warning - skipping unsafe path: {e}")
                    continue
                
                if os.path.isdir(resolved_path):
                    # It's a directory - create subsection
                    content_lines.append(f"## {title}")
                    content_lines.append("")
                    
                    # Look for .nav.yml in this directory
                    sub_nav_path = os.path.join(resolved_path, '.nav.yml')
                    if os.path.exists(sub_nav_path):
                        sub_nav_items = load_nav_file(sub_nav_path)
                        sub_content = process_nav_items(sub_nav_items, resolved_path, 
                                                      workspace_root, content_dir)
                        content_lines.extend(sub_content)
                    else:
                        # No nav file, scan for markdown files directly
                        md_files = [f for f in sorted(os.listdir(resolved_path)) 
                                  if f.endswith('.md') and f != 'index.md']
                        
                        if md_files:
                            table_rows = []
                            
                            for md_file in sorted(md_files):
                                md_path = os.path.join(resolved_path, md_file)
                                frontmatter = extract_frontmatter(md_path)
                                
                                title = frontmatter.get('title', '').strip()
                                tools = frontmatter.get('tools', '').strip()
                                description = frontmatter.get('description', '').strip()
                                
                                if not title:
                                    print(f"⚠️  No title found in frontmatter for {md_path} - skipping")
                                    continue
                                    
                                if not description:
                                    print(f"⚠️  No description found in frontmatter for {md_path} - skipping")
                                    continue
                                
                                if not tools:
                                    print(f"⚠️  No tools found in frontmatter for {md_path}")
                                    tools = 'N/A'
                                else:
                                    tools = format_tools(tools)
                                
                                link_title = create_markdown_link(title, md_path, workspace_root)
                                table_rows.append(f"| {escape_table_cell(link_title)} | {escape_table_cell(tools)} | {escape_table_cell(description)} |")
                            
                            if table_rows:
                                content_lines.append("| Title | Tools | Description |")
                                content_lines.append("|-------|-------|-------------|")
                                content_lines.extend(table_rows)
                    
                    content_lines.append("")
                
                elif os.path.isfile(resolved_path) and resolved_path.endswith('.md'):
                    # It's a markdown file - add to current section
                    frontmatter = extract_frontmatter(resolved_path)
                    
                    if frontmatter.get('title'):
                        # This should be part of a table, but we need context of which section
                        # For now, we'll handle this in the main processing loop
                        pass
                    else:
                        print(f"⚠️  No title found in frontmatter for {resolved_path}")
                
                else:
                    # If directory not found, try looking for a .md file with the same name
                    # Handle both cases: path ending with / and without /
                    base_path = resolved_path.rstrip('/')
                    md_file_path = base_path + '.md'
                    
                    if os.path.isfile(md_file_path):
                        frontmatter = extract_frontmatter(md_file_path)
                        
                        title_fm = frontmatter.get('title', '').strip()
                        tools = frontmatter.get('tools', '').strip()
                        description = frontmatter.get('description', '').strip()
                        
                        if title_fm and description:
                            if not tools:
                                print(f"⚠️  No tools found in frontmatter for {md_file_path}")
                                tools = 'N/A'
                            else:
                                tools = format_tools(tools)
                            
                            # Create section for single file
                            content_lines.append(f"## {title}")
                            content_lines.append("")
                            content_lines.append("| Title | Tools | Description |")
                            content_lines.append("|-------|-------|-------------|")
                            
                            link_title = create_markdown_link(title_fm, md_file_path, workspace_root)
                            content_lines.append(f"| {escape_table_cell(link_title)} | {escape_table_cell(tools)} | {escape_table_cell(description)} |")
                            content_lines.append("")
                        else:
                            if not title_fm:
                                print(f"⚠️  No title found in frontmatter for {md_file_path} - skipping")
                            if not description:
                                print(f"⚠️  No description found in frontmatter for {md_file_path} - skipping")
                    else:
                        print(f"⚠️  Referenced path not found: {resolved_path} (also tried {md_file_path})")
    
    return content_lines


def extract_manual_content(index_path: str) -> List[str]:
    """
    Extract manual content from existing index.md file (everything before auto-generated marker).
    
    Args:
        index_path: Path to existing index.md file
        
    Returns:
        List of lines containing manual content
    """
    if not os.path.exists(index_path):
        return ["# Index", "", ""]
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove trailing newlines and convert to list of strings
        lines = [line.rstrip('\n') for line in lines]
        
        # Look for the auto-generated content marker
        manual_content = []
        
        for line in lines:
            if line.strip() == AUTO_START:
                break
            manual_content.append(line)
        
        # Ensure we end with proper spacing
        while manual_content and manual_content[-1] == "":
            manual_content.pop()
        
        if manual_content:
            manual_content.extend(["", ""])
        else:
            # Fallback if no manual content found
            manual_content = ["# Index", "", ""]
            
        return manual_content
        
    except Exception as e:
        print(f"⚠️  Error reading existing index file: {e}")
        return ["# Index", "", ""]


def generate_index_content(target_dir: str, content_dir: str, workspace_root: str) -> str:
    """
    Generate the complete index markdown content, preserving manual content.
    
    Args:
        target_dir: Directory where index.md will be created
        content_dir: Directory to scan for content
        workspace_root: Root directory of workspace
        
    Returns:
        Generated markdown content
    """
    # Check for existing index.md and preserve manual content
    index_path = os.path.join(target_dir, 'index.md')
    content_lines = extract_manual_content(index_path)
    
    # Look for .nav.yml in target directory first
    nav_path = os.path.join(target_dir, '.nav.yml')
    
    if os.path.exists(nav_path):
        print(f"📖 Processing navigation file: {nav_path}")
        nav_items = load_nav_file(nav_path)
        
        # Create sections based on nav items
        current_section_items = []
        
        for item in nav_items:
            if isinstance(item, dict):
                for title, path in item.items():
                    # Skip index.md entries (including subdirectories)
                    if os.path.basename(path) == 'index.md':
                        continue
                    
                    try:
                        resolved_path = resolve_path(target_dir, path, workspace_root)
                    except ValueError as e:
                        print(f"⚠️  Security warning - skipping unsafe path: {e}")
                        continue
                    
                    if os.path.isdir(resolved_path):
                        # Create section header
                        content_lines.append(f"## {title}")
                        content_lines.append("")
                        
                        # Look for .nav.yml in subdirectory
                        sub_nav_path = os.path.join(resolved_path, '.nav.yml')
                        if os.path.exists(sub_nav_path):
                            sub_nav_items = load_nav_file(sub_nav_path)
                            
                            # Create table for this section
                            if sub_nav_items:
                                table_rows = []
                                
                                for sub_item in sub_nav_items:
                                    if isinstance(sub_item, dict):
                                        for sub_title, sub_path in sub_item.items():
                                            if os.path.basename(sub_path) == 'index.md':
                                                continue
                                                
                                            try:
                                                sub_resolved_path = resolve_path(resolved_path, sub_path, workspace_root)
                                            except ValueError as e:
                                                print(f"⚠️  Security warning - skipping unsafe path: {e}")
                                                continue
                                            
                                            if os.path.isfile(sub_resolved_path) and sub_resolved_path.endswith('.md'):
                                                frontmatter = extract_frontmatter(sub_resolved_path)
                                                
                                                title = frontmatter.get('title', '').strip()
                                                description = frontmatter.get('description', '').strip()
                                                tools = frontmatter.get('tools', '').strip()
                                                
                                                if not title:
                                                    print(f"⚠️  No title found in frontmatter for {sub_resolved_path} - skipping")
                                                    continue
                                                    
                                                if not description:
                                                    print(f"⚠️  No description found in frontmatter for {sub_resolved_path} - skipping")
                                                    continue
                                                
                                                if not tools:
                                                    print(f"⚠️  No tools found in frontmatter for {sub_resolved_path}")
                                                    tools = 'N/A'
                                                else:
                                                    tools = format_tools(tools)
                                                
                                                link_title = create_markdown_link(title, sub_resolved_path, workspace_root)
                                                table_rows.append(f"| {escape_table_cell(link_title)} | {escape_table_cell(tools)} | {escape_table_cell(description)} |")
                                
                                if table_rows:
                                    content_lines.append("| Title | Tools | Description |")
                                    content_lines.append("|-------|-------|-------------|")
                                    content_lines.extend(table_rows)
                                else:
                                    # Remove the section header if no valid entries
                                    # Safer approach: slice back to before we added the header
                                    if len(content_lines) >= 2 and content_lines[-1] == "" and content_lines[-2].startswith(f"## {title}"):
                                        content_lines = content_lines[:-2]
                        
                        content_lines.append("")
                    
                    elif os.path.isfile(resolved_path) and resolved_path.endswith('.md'):
                        # Handle direct markdown file references
                        frontmatter = extract_frontmatter(resolved_path)
                        if not frontmatter.get('title'):
                            print(f"⚠️  No title found in frontmatter for {resolved_path}")
                    
                    else:
                        # Try adding .md extension
                        md_path = resolved_path.rstrip('/') + '.md'
                        
                        if os.path.isfile(md_path):
                            frontmatter = extract_frontmatter(md_path)
                            
                            title_fm = frontmatter.get('title', '').strip()
                            tools = frontmatter.get('tools', '').strip()
                            description = frontmatter.get('description', '').strip()
                            
                            if title_fm and description:
                                # Create section for single file
                                content_lines.append(f"## {title}")
                                content_lines.append("")
                                content_lines.append("| Title | Tools | Description |")
                                content_lines.append("|-------|-------|-------------|")
                                
                                if not tools:
                                    tools = 'N/A'
                                else:
                                    tools = format_tools(tools)
                                
                                link_title = create_markdown_link(title_fm, md_path, workspace_root)
                                content_lines.append(f"| {escape_table_cell(link_title)} | {escape_table_cell(tools)} | {escape_table_cell(description)} |")
                                content_lines.append("")
                            else:
                                if not title_fm:
                                    print(f"⚠️  No title found in frontmatter for {md_path} - skipping")
                                if not description:
                                    print(f"⚠️  No description found in frontmatter for {md_path} - skipping")
    
    else:
        print(f"📂 No .nav.yml found in {target_dir}, scanning subdirectories...")
        
        # Look for .nav.yml files in subdirectories
        for item in sorted(os.listdir(target_dir)):
            item_path = os.path.join(target_dir, item)
            if os.path.isdir(item_path):
                sub_nav_path = os.path.join(item_path, '.nav.yml')
                if os.path.exists(sub_nav_path):
                    sub_nav_items = load_nav_file(sub_nav_path)
                    if sub_nav_items and len(sub_nav_items) > 0:
                        # Use the first item's title or folder name
                        first_item = sub_nav_items[0]
                        if isinstance(first_item, dict):
                            section_title = list(first_item.keys())[0] if first_item else item.replace('-', ' ').title()
                        else:
                            section_title = item.replace('-', ' ').title()
                        
                        content_lines.append(f"## {section_title}")
                        content_lines.append("")
                        
                        # Process items in this nav file
                        section_start_index = len(content_lines) - 2  # Remember where section started
                        sub_content = process_nav_items(sub_nav_items, item_path, workspace_root, content_dir)
                        content_lines.extend(sub_content)
                        
                        # Check if section ended up empty (only contains header and empty line)
                        if len(content_lines) == section_start_index + 2:
                            # Remove empty section
                            content_lines = content_lines[:section_start_index]
    
    # Stitch final content deterministically: manual → marker → auto → end marker
    index_path = os.path.join(target_dir, 'index.md')
    manual = extract_manual_content(index_path)
    
    # Build final content explicitly
    out: List[str] = []
    out.extend(manual)
    
    # Only add auto-generated content if we have content beyond manual
    auto_content = content_lines[len(manual):]
    if auto_content:
        out.append(AUTO_START)
        out.append("")
        out.extend(auto_content)
        if auto_content and auto_content[-1] != "":
            out.append("")
        out.append(AUTO_END)
    
    return '\n'.join(out)


def main():
    """Main function to generate cookbook indexes."""
    if len(sys.argv) != 3:
        print("Usage: python generate-cookbook-indexes.py <target_dir> <content_dir>")
        print("  target_dir: Directory where index.md will be created")
        print("  content_dir: Directory to scan for content")
        sys.exit(1)
    
    target_dir = os.path.abspath(sys.argv[1])
    content_dir = os.path.abspath(sys.argv[2])
    
    # Find workspace root (preferring target_dir as starting point)
    workspace_root = find_workspace_root(target_dir)
    
    if not workspace_root:
        print("❌ Could not find workspace root (no mkdocs.yml found)")
        sys.exit(1)
    
    print(f"🚀 Generating cookbook index")
    print(f"📁 Target directory: {target_dir}")
    print(f"📂 Content directory: {content_dir}")
    print(f"🌍 Workspace root: {workspace_root}")
    
    # Validate directories
    if not os.path.exists(target_dir):
        print(f"❌ Target directory does not exist: {target_dir}")
        sys.exit(1)
    
    if not os.path.exists(content_dir):
        print(f"❌ Content directory does not exist: {content_dir}")
        sys.exit(1)
    
    # Generate content
    try:
        content = generate_index_content(target_dir, content_dir, workspace_root)
        
        # Write to index.md
        index_path = os.path.join(target_dir, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully generated {index_path}")
        
    except Exception as e:
        print(f"❌ Error generating index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
