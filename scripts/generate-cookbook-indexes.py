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

# Configure custom logging with emojis
class EmojiFormatter(logging.Formatter):
    """Custom formatter that uses emojis instead of log level names."""
    
    EMOJI_MAP = {
        logging.INFO: '📝',
        logging.WARNING: '⚠️',
        logging.ERROR: '❌',
        logging.DEBUG: '🔍'
    }
    
    def format(self, record):
        emoji = self.EMOJI_MAP.get(record.levelno, '📝')
        return f"{emoji} {record.getMessage()}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handler with emoji formatter
handler = logging.StreamHandler()
handler.setFormatter(EmojiFormatter())
logger.addHandler(handler)

# Prevent duplicate logs
logger.propagate = False

# Global variables for path shortening
_workspace_root = None
_docs_dir = None

def shorten_path(file_path: str) -> str:
    """
    Convert absolute path to a shorter relative path from docs directory.
    
    Args:
        file_path: Absolute file path
        
    Returns:
        Shortened path relative to docs directory
    """
    global _workspace_root, _docs_dir
    if not _workspace_root or not _docs_dir:
        return file_path
    
    try:
        # Try to make relative to docs directory first
        docs_path = os.path.join(_workspace_root, _docs_dir)
        if file_path.startswith(docs_path):
            rel_path = os.path.relpath(file_path, docs_path)
            if rel_path == '.':
                return _docs_dir
            return f"{_docs_dir}/{rel_path}"
        
        # Fallback to workspace relative
        if file_path.startswith(_workspace_root):
            return os.path.relpath(file_path, _workspace_root)
        
        # If all else fails, just return the filename
        return os.path.basename(file_path)
    except:
        return os.path.basename(file_path)

# Common acronyms to preserve
ACRONYMS = {'API', 'SDK', 'CLI', 'AI', 'ML', 'CPU', 'GPU', 'EVM', 'PVM', 'NFT', 'DApp'}

# Auto-generation markers
AUTO_START = "<!-- START OF AUTOMATICALLY GENERATED CONTENT -->"
AUTO_END = "<!-- END OF AUTOMATICALLY GENERATED CONTENT -->"


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
        logger.warning(f"Error reading frontmatter from {shorten_path(file_path)}: {e}")
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
        
        logger.warning(f"Unexpected nav structure in {shorten_path(nav_path)} (got {type(data).__name__})")
        return []
    
    except Exception as e:
        logger.error(f"Error loading nav file {shorten_path(nav_path)}: {e}")
        return []


def resolve_path(base_path: str, nav_path: str, workspace_root: str, content_root: str = None) -> str:
    """
    Resolve a path from a navigation file, handling both absolute and relative paths.
    
    Args:
        base_path: Base directory containing the navigation file
        nav_path: Path from the navigation file
        workspace_root: Root directory of the workspace
        content_root: Content directory root (auto-detected if not provided)
        
    Returns:
        Resolved absolute path
        
    Raises:
        ValueError: If path is invalid or contains dangerous sequences
    """
    
    if nav_path.startswith('/'):
        # Absolute path from content root, not workspace root
        if not content_root:
            # Auto-detect content directory
            current = base_path
            while current and current != workspace_root:
                # Look for common docs directory names or use the first subdirectory
                basename = os.path.basename(current)
                if basename in ('docs', 'polkadot-docs', 'content', 'src'):
                    content_root = current
                    break
                current = os.path.dirname(current)
            
            if not content_root:
                # Fallback to workspace root
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


def get_docs_dir_from_mkdocs(workspace_root: str) -> str:
    """
    Extract docs_dir from mkdocs.yml configuration using simple text parsing.
    
    Args:
        workspace_root: Path to workspace root containing mkdocs.yml
        
    Returns:
        Name of the docs directory (defaults to 'docs' if not found)
    """
    mkdocs_path = os.path.join(workspace_root, 'mkdocs.yml')
    try:
        with open(mkdocs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use simple text parsing to find docs_dir since YAML has complex tags
        for line in content.split('\n'):
            line = line.strip()
            # Skip commented lines
            if line.startswith('#'):
                continue
            
            # Check if docs_dir appears before any comment
            if 'docs_dir:' in line:
                comment_pos = line.find('#')
                docs_dir_pos = line.find('docs_dir:')
                
                # Only process if docs_dir appears before any comment
                if comment_pos == -1 or docs_dir_pos < comment_pos:
                    if line.startswith('docs_dir:'):
                        # Extract the value after 'docs_dir:'
                        docs_dir = line.split(':', 1)[1].strip()
                        # Remove quotes if present
                        docs_dir = docs_dir.strip('\'"')
                        logger.info(f"Found docs_dir in mkdocs.yml: {docs_dir}")
                        return docs_dir
        
        # If no docs_dir found, default to 'docs'
        logger.info("No docs_dir found in mkdocs.yml, defaulting to 'docs'")
        return 'docs'
        
    except Exception as e:
        logger.warning(f"Error reading mkdocs.yml: {e}, defaulting to 'docs'")
        return 'docs'


def process_nav_items(nav_items: List[Dict], base_path: str, workspace_root: str) -> List[str]:
    """
    Process navigation items and generate markdown content.
    
    Args:
        nav_items: List of navigation items from .nav.yml
        base_path: Base directory where nav file is located
        workspace_root: Root directory of workspace
        
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
                    logger.warning(f"Security warning - skipping unsafe path: {e}")
                    continue
                
                if os.path.isdir(resolved_path):
                    # It's a directory - buffer content first, then add section header if there's content
                    section_content = []
                    
                    # Look for .nav.yml in this directory
                    sub_nav_path = os.path.join(resolved_path, '.nav.yml')
                    if os.path.exists(sub_nav_path):
                        sub_nav_items = load_nav_file(sub_nav_path)
                        section_content = process_nav_items(sub_nav_items, resolved_path, 
                                                      workspace_root)
                    else:
                        # No nav file, scan for markdown files directly
                        md_files = [f for f in sorted(os.listdir(resolved_path)) 
                                  if f.endswith('.md') and f != 'index.md']
                        
                        if md_files:
                            table_rows = []
                            
                            for md_file in sorted(md_files):
                                md_path = os.path.join(resolved_path, md_file)
                                row = make_table_row(md_path, workspace_root)
                                if row:
                                    table_rows.append(row)
                                else:
                                    logger.warning(f"Skipping {shorten_path(md_path)} - missing title or description")
                            
                            if table_rows:
                                section_content.append("| Title | Tools | Description |")
                                section_content.append("|-------|-------|-------------|")
                                section_content.extend(table_rows)
                    
                    # Only add section header and content if there's actual content
                    if section_content:
                        content_lines.append(f"## {title}")
                        content_lines.append("")
                        content_lines.extend(section_content)
                        content_lines.append("")
                
                elif os.path.isfile(resolved_path) and resolved_path.endswith('.md'):
                    # It's a markdown file - add to current section
                    frontmatter = extract_frontmatter(resolved_path)
                    
                    if frontmatter.get('title'):
                        # This should be part of a table, but we need context of which section
                        # For now, we'll handle this in the main processing loop
                        pass
                    else:
                        logger.warning(f"No title found in frontmatter for {shorten_path(resolved_path)}")
                
                else:
                    # If directory not found, try looking for a .md file with the same name
                    # Handle both cases: path ending with / and without /
                    base_no_slash = resolved_path.rstrip('/')
                    md_file_path = base_no_slash + '.md'
                    
                    if os.path.isfile(md_file_path):
                        frontmatter = extract_frontmatter(md_file_path)
                        
                        title_fm = frontmatter.get('title', '').strip()
                        tools = frontmatter.get('tools', '').strip()
                        description = frontmatter.get('description', '').strip()
                        
                        row = make_table_row(md_file_path, workspace_root)
                        if row:
                            # Create section for single file
                            content_lines.append(f"## {title}")
                            content_lines.append("")
                            content_lines.append("| Title | Tools | Description |")
                            content_lines.append("|-------|-------|-------------|")
                            content_lines.append(row)
                            content_lines.append("")
                        else:
                            logger.warning(f"Skipping {shorten_path(md_file_path)} - missing title or description")
                    else:
                        logger.warning(f"Referenced path not found: {shorten_path(resolved_path)} (also tried {shorten_path(md_file_path)})")
    
    return content_lines


def extract_manual_content(output_path: str) -> List[str]:
    """
    Extract manual content from existing output file (everything before auto-generated marker).
    
    Args:
        output_path: Path to existing output file
        
    Returns:
        List of lines containing manual content
    """
    if not os.path.exists(output_path):
        return ["# Index", "", ""]
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
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
        logger.warning(f"Error reading existing output file: {e}")
        return ["# Index", "", ""]


def generate_index_content(target_dir: str, content_dir: str, workspace_root: str, output_filename: str = 'index.md') -> str:
    """
    Generate the complete index markdown content, preserving manual content.
    
    Args:
        target_dir: Directory where output file will be created
        content_dir: Directory to scan for content
        workspace_root: Root directory of workspace
        output_filename: Name of the output file (default: 'index.md')
        
    Returns:
        Generated markdown content
    """
    # Build auto-generated content separately (not pre-seeded with manual)
    auto_content_lines = []
    
    # Look for .nav.yml in target directory first
    nav_path = os.path.join(target_dir, '.nav.yml')
    
    if os.path.exists(nav_path):
        logger.info(f"Processing navigation file: {shorten_path(nav_path)}")
        nav_items = load_nav_file(nav_path)
        
        # Create sections based on nav items
        for item in nav_items:
            if isinstance(item, dict):
                for title, path in item.items():
                    # Skip index.md entries (including subdirectories)
                    if os.path.basename(path) == 'index.md':
                        continue
                    
                    try:
                        resolved_path = resolve_path(target_dir, path, workspace_root)
                    except ValueError as e:
                        logger.warning(f"Security warning - skipping unsafe path: {e}")
                        continue
                    
                    if os.path.isdir(resolved_path):
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
                                                logger.warning(f"Security warning - skipping unsafe path: {e}")
                                                continue
                                            
                                            if os.path.isfile(sub_resolved_path) and sub_resolved_path.endswith('.md'):
                                                row = make_table_row(sub_resolved_path, workspace_root)
                                                if row:
                                                    table_rows.append(row)
                                                else:
                                                    logger.warning(f"Skipping {shorten_path(sub_resolved_path)} - missing title or description")
                                
                                if table_rows:
                                    auto_content_lines.append(f"## {title}")
                                    auto_content_lines.append("")
                                    auto_content_lines.append("| Title | Tools | Description |")
                                    auto_content_lines.append("|-------|-------|-------------|")
                                    auto_content_lines.extend(table_rows)
                                    auto_content_lines.append("")
                    
                    elif os.path.isfile(resolved_path) and resolved_path.endswith('.md'):
                        # Handle direct markdown file references
                        frontmatter = extract_frontmatter(resolved_path)
                        if not frontmatter.get('title'):
                            logger.warning(f"No title found in frontmatter for {shorten_path(resolved_path)}")
                    
                    else:
                        # Try adding .md extension
                        md_path = resolved_path.rstrip('/') + '.md'
                        
                        if os.path.isfile(md_path):
                            frontmatter = extract_frontmatter(md_path)
                            
                            title_fm = frontmatter.get('title', '').strip()
                            tools = frontmatter.get('tools', '').strip()
                            description = frontmatter.get('description', '').strip()
                            
                            row = make_table_row(md_path, workspace_root)
                            if row:
                                # Create section for single file
                                auto_content_lines.append(f"## {title}")
                                auto_content_lines.append("")
                                auto_content_lines.append("| Title | Tools | Description |")
                                auto_content_lines.append("|-------|-------|-------------|")
                                auto_content_lines.append(row)
                                auto_content_lines.append("")
                            else:
                                logger.warning(f"Skipping {shorten_path(md_path)} - missing title or description")
    
    else:
        logger.info(f"No .nav.yml found in {shorten_path(target_dir)}, scanning subdirectories...")
        
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
                        
                        # Process items in this nav file
                        sub_content = process_nav_items(sub_nav_items, item_path, workspace_root)
                        
                        # Only add section if there's actual content
                        if sub_content:
                            auto_content_lines.append(f"## {section_title}")
                            auto_content_lines.append("")
                            auto_content_lines.extend(sub_content)
    
    # Stitch final content deterministically: manual → marker → auto → end marker
    output_path = os.path.join(target_dir, output_filename)
    manual_content = extract_manual_content(output_path)
    
    # Build final content explicitly
    final_content: List[str] = []
    final_content.extend(manual_content)
    
    # Only add auto-generated content if we have any
    if auto_content_lines:
        final_content.append(AUTO_START)
        final_content.append("")
        final_content.extend(auto_content_lines)
        if auto_content_lines and auto_content_lines[-1] != "":
            final_content.append("")
        final_content.append(AUTO_END)
    
    return '\n'.join(final_content)


def sanitize_path_input(path_input: str, allow_separators: bool = True) -> str:
    """
    Sanitize user input to prevent path traversal attacks.
    
    Args:
        path_input: User-provided path input
        allow_separators: Whether to allow directory separators (False for filenames)
        
    Returns:
        Sanitized path input
        
    Raises:
        ValueError: If path contains dangerous sequences
    """
    if not path_input or not isinstance(path_input, str):
        raise ValueError("Invalid path input")
    
    # Remove null bytes and normalize
    sanitized = path_input.replace('\x00', '').strip()
    
    # Normalize path to catch sneaky traversals
    normalized = os.path.normpath(sanitized)
    
    # Check for path traversal sequences (more robust)
    if (normalized.startswith(('../', '..\\')) or 
        normalized in ('.', '..') or
        '/../' in normalized or 
        '\\..\\' in normalized):
        raise ValueError(f"Path traversal detected: {normalized}")
    
    # Check for absolute paths (cross-platform)
    if os.path.isabs(sanitized) or sanitized.startswith('\\\\'):  # UNC paths
        raise ValueError("Absolute paths not allowed")
    
    # For filenames, ensure no directory separators
    if not allow_separators:
        if '/' in sanitized or '\\' in sanitized:
            raise ValueError("Filename cannot contain directory separators")
    
    return sanitized


def main():
    """Main function to generate cookbook indexes."""
    global _workspace_root, _docs_dir
    
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        logger.error("Usage: python generate-cookbook-indexes.py <target_path> [output_filename]")
        logger.error("  target_path: Relative path from docs directory (e.g., smart-contracts/cookbook)")
        logger.error("  output_filename: Name of output file (default: index.md)")
        logger.error("")
        logger.error("Examples:")
        logger.error("  python generate-cookbook-indexes.py smart-contracts/cookbook")
        logger.error("  python generate-cookbook-indexes.py smart-contracts/cookbook summary.md")
        sys.exit(1)
    
    # Sanitize user inputs to prevent path traversal
    try:
        target_path = sanitize_path_input(sys.argv[1], allow_separators=True)
        output_filename = sanitize_path_input(sys.argv[2] if len(sys.argv) == 3 else 'index.md', allow_separators=False)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    
    # Find workspace root from current directory
    workspace_root = find_workspace_root(os.getcwd())
    
    if not workspace_root:
        logger.error("Could not find workspace root (no mkdocs.yml found)")
        sys.exit(1)
    
    # Get docs directory from mkdocs.yml and initialize global variables for path shortening
    docs_dir_name = get_docs_dir_from_mkdocs(workspace_root)
    _workspace_root = workspace_root
    _docs_dir = docs_dir_name
    content_dir = os.path.join(workspace_root, docs_dir_name)
    target_dir = os.path.join(content_dir, target_path)
    
    # Security validation: Ensure resolved paths stay within workspace boundaries
    try:
        # Resolve to absolute paths and check boundaries using Path.resolve().relative_to()
        workspace_path = Path(workspace_root).resolve()
        content_path = Path(content_dir).resolve()
        target_path = Path(target_dir).resolve()
        
        # Ensure content directory is within workspace
        try:
            content_path.relative_to(workspace_path)
        except ValueError:
            raise ValueError("Content directory resolves outside of workspace")
            
        # Ensure target directory is within content directory
        try:
            target_path.relative_to(content_path)
        except ValueError:
            raise ValueError("Target path resolves outside of docs directory")
            
        # Validate output file path as well
        output_path = target_path / output_filename
        try:
            output_path.relative_to(content_path)
        except ValueError:
            raise ValueError("Output path resolves outside of docs directory")
            
    except (OSError, ValueError) as e:
        logger.error(f"Path validation failed: {e}")
        sys.exit(1)
    
    # Update paths to use validated resolved paths
    workspace_root = str(workspace_path)
    content_dir = str(content_path)
    target_dir = str(target_path)
    
    logger.info(f"Generating cookbook index")
    logger.info(f"Target directory: {shorten_path(target_dir)}")
    logger.info(f"Content directory: {shorten_path(content_dir)}")
    logger.info(f"Output filename: {output_filename}")
    logger.info(f"Workspace root: {os.path.basename(workspace_root)}")
    
    # Validate directories
    if not os.path.exists(target_dir):
        logger.error(f"Target directory does not exist: {shorten_path(target_dir)}")
        logger.error(f"Make sure '{target_path}' exists within the docs directory '{docs_dir_name}'")
        sys.exit(1)
    
    if not os.path.exists(content_dir):
        logger.error(f"Content directory does not exist: {shorten_path(content_dir)}")
        logger.error(f"Make sure mkdocs.yml has correct docs_dir: {docs_dir_name}")
        sys.exit(1)
    
    # Generate content
    try:
        content = generate_index_content(target_dir, content_dir, workspace_root, output_filename)
        
        # Write to output file
        output_path = os.path.join(target_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully generated {shorten_path(output_path)}")
        
    except Exception as e:
        logger.error(f"Error generating index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
