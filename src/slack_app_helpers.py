"""Helper functions for Slack app"""
import re
from pathlib import Path


def extract_executive_summary(markdown_path: str) -> str:
    """
    Extract executive summary from markdown report

    Args:
        markdown_path: Path to markdown file

    Returns:
        Executive summary text (first 500 chars)
    """
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find executive summary section
        match = re.search(
            r'#\s*🚀\s*Executive Summary\s*\n(.*?)(?=\n#|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            summary = match.group(1).strip()
            # Clean up markdown formatting
            summary = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', summary)  # Remove links
            summary = re.sub(r'[*_`]', '', summary)  # Remove formatting
            summary = re.sub(r'\n+', ' ', summary)  # Replace newlines with spaces
            summary = ' '.join(summary.split())  # Normalize whitespace

            # Limit to 500 characters
            if len(summary) > 500:
                summary = summary[:497] + "..."

            return summary
        else:
            return "Executive summary not found in report."

    except Exception as e:
        return f"Error extracting summary: {str(e)}"


def count_words(markdown_path: str) -> int:
    """
    Count words in markdown file

    Args:
        markdown_path: Path to markdown file

    Returns:
        Word count
    """
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove markdown syntax
        content = re.sub(r'#+ ', '', content)  # Headers
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Links
        content = re.sub(r'[*_`]', '', content)  # Formatting
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Code blocks

        # Count words
        words = content.split()
        return len(words)

    except Exception as e:
        return 0


def markdown_to_slack_blocks(markdown_text: str, max_blocks: int = 40) -> list:
    """
    Convert markdown to Slack blocks

    Args:
        markdown_text: Markdown content
        max_blocks: Maximum number of blocks to return

    Returns:
        List of Slack block dictionaries
    """
    blocks = []
    lines = markdown_text.split('\n')

    current_section = []
    section_char_count = 0

    for line in lines:
        # Headers
        if line.startswith('# '):
            # Flush current section
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(current_section)
                    }
                })
                current_section = []
                section_char_count = 0

            # Add header
            header_text = line.replace('# ', '').strip()
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text[:150]  # Slack limit
                }
            })
            blocks.append({"type": "divider"})

        elif line.startswith('## '):
            # Flush current section
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(current_section)
                    }
                })
                current_section = []
                section_char_count = 0

            # Add subheader as bold text
            header_text = line.replace('## ', '').strip()
            current_section.append(f"*{header_text}*")
            section_char_count += len(header_text) + 4

        else:
            # Regular content
            if line.strip():
                # Check if adding this line would exceed Slack's limit (3000 chars)
                if section_char_count + len(line) + 1 > 2900:
                    # Flush current section
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": '\n'.join(current_section)
                        }
                    })
                    current_section = [line]
                    section_char_count = len(line)
                else:
                    current_section.append(line)
                    section_char_count += len(line) + 1

        # Stop if we've reached max blocks (Slack limit is 50)
        if len(blocks) >= max_blocks:
            break

    # Flush remaining section
    if current_section and len(blocks) < max_blocks:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": '\n'.join(current_section)
            }
        })

    return blocks


def truncate_text(text: str, max_length: int = 3000) -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
