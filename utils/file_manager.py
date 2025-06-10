"""File operations utilities for Reddit Market Research Framework."""

import json
import os


class FileManager:
    """Handles file operations for the framework."""

    @staticmethod
    def load_json(filepath):
        """
        Load JSON data from a file with error handling.

        Args:
            filepath: Path to the JSON file

        Returns:
            Loaded data or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {filepath}: {e}")
            return None

    @staticmethod
    def save_json(data, filepath):
        """
        Save data as JSON to a file.

        Args:
            data: Data to save
            filepath: Destination file path
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def save_text(content, filepath):
        """
        Save text content to a file.

        Args:
            content: Text content to save
            filepath: Destination file path
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def file_exists(filepath):
        """Check if a file exists."""
        return os.path.exists(filepath)

    @staticmethod
    def get_file_size(filepath):
        """Get file size in bytes."""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
