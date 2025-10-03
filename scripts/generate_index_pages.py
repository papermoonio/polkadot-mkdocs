import os
import re

IGNORE_DIRECTORIES = {".", "node_modules", "js", "images"}

def parse_frontmatter(file_path):
    """
    Extracts title and description from the frontmatter of a Markdown file.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    frontmatter_match = re.match(r'^---\s*(.*?)\s*---', content, re.DOTALL | re.MULTILINE)
    if frontmatter_match:
        frontmatter_content = frontmatter_match.group(1)
        # Extract title and description from the frontmatter
        title = re.search(r'^title:\s*(.+)', frontmatter_content, re.MULTILINE)
        description = re.search(r'^description:\s*(.+)', frontmatter_content, re.MULTILINE)
        return (
            title.group(1).strip() if title else None, 
            description.group(1).strip() if description else None
        )
    return None, None

def check_content_after_second_frontmatter(file_path):
    """
    Checks if there is any content after the second `---` in the file.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    parts = re.split(r'^---\s*$', content, flags=re.MULTILINE)
    return len(parts) > 2 and parts[2].strip() != ''

def convert_path(file_path):
    """
    Converts a full file path (i.e., 'polkadot-docs/develop/blockchains/deployment/generate-chain-specs.md')
    to an absolute path (i.e., '/develop/blockchains/deployment/generate-chain-specs/')
    """
    # Remove the 'polkadot-docs' prefix
    if file_path.startswith('polkadot-docs'):
        file_path = file_path[len('polkadot-docs'):]
    
    # Remove the '.md' extension
    if file_path.endswith('.md'):
        file_path = file_path[:-3]
    
    # Ensure it starts with '/'
    return file_path + '/'

def process_directory(directory):
    """
    Processes a directory to create or modify `index.md` based on the rules.
    """
    index_path = os.path.join(directory, 'index.md')

    if not os.path.isfile(index_path):
        return

    if check_content_after_second_frontmatter(index_path):
        return

    in_this_section = []

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isdir(item_path) and os.path.basename(item_path) not in IGNORE_DIRECTORIES:
            sub_index_path = os.path.join(item_path, 'index.md')
            if os.path.isfile(sub_index_path):
                title, description = parse_frontmatter(sub_index_path)
                if title or description:
                    in_this_section.append((title, description, sub_index_path))

        elif item.endswith('.md') and item != 'index.md':
            title, description = parse_frontmatter(item_path)
            if title or description:
                in_this_section.append((title, description, item_path))

    if in_this_section:
        with open(index_path, 'r+') as f:
            content = f.read()
            parts = re.split(r'^---\s*$', content, flags=re.MULTILINE)
            if len(parts) >= 2:
                # Add content below the second `---`
                new_content = parts[0] + "---" + parts[1] + "---" + os.linesep + os.linesep
                title = re.search(r'^title:\s*(.+)', parts[1], re.MULTILINE)
                title = title.group(1).strip() if title else None

                description = re.search(r'^description:\s*(.+)', parts[1], re.MULTILINE)
                description = description.group(1).strip() if title else None

                print(description)

                # Preserve any content that might exist after the second `---`
                existing_content = parts[2] if len(parts) > 2 else ""

                # Append the new content to the existing content
                new_content += f'# {title or ""}' + os.linesep + os.linesep
                new_content += f'{description or ""}' + os.linesep + os.linesep
                new_content += "## In This Section" + os.linesep + os.linesep
                new_content += ":::INSERT_IN_THIS_SECTION:::"

                new_content += existing_content

                # Write the modified content back to the file
                f.seek(0)
                f.write(new_content)
                f.truncate()


def main(base_directory):
    """
    Main function to iterate over directories and process each.
    """
    for root, dirs, files in os.walk(base_directory):
        # Exclude directories in-place to prevent walking into them
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRECTORIES and not d.startswith('.')]
        process_directory(root)

if __name__ == '__main__':
    base_directory = "polkadot-docs"  # Replace with the path to your polkadot-docs directory
    main(base_directory)
