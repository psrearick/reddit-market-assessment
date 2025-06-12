"""Text processing utilities for Reddit Market Research Framework."""

import re


class TextProcessor:
    """Handles text processing operations."""

    @staticmethod
    def markdown_to_plain_text(text: str) -> str:
        """
        Convert markdown text to plain text.

        Args:
            text: Markdown text to convert

        Returns:
            Plain text version
        """
        if not text or text.strip() == "":
            return text

        # Remove Reddit quotes (lines starting with >)
        text = re.sub(r"^&gt;.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)

        # Remove markdown links [text](url)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # Remove markdown emphasis
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # Italic
        text = re.sub(r"~~(.*?)~~", r"\1", text)  # Strikethrough
        text = re.sub(r"`(.*?)`", r"\1", text)  # Inline code

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"    .*$", "", text, flags=re.MULTILINE)  # Indented code

        # Remove headers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)

        # Remove bullet points and numbering
        text = re.sub(r"^\s*[\*\-\+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple empty lines to double
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces/tabs to single space
        text = text.strip()

        return text

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """
        Rough estimation of token count (approximately 4 characters per token).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4 if text else 0
