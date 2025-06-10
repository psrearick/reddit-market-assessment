"""Configuration management for Reddit Market Research Framework."""

import os
import importlib.util

class ConfigManager:
    """Manages configuration loading and file path generation."""

    def __init__(self, config_path: str = 'concept_config.py'):
        """Initialize with a configuration file path."""
        self.config = self._load_config(config_path)
        self.output_dir = os.getenv("OUTPUT_DIR", 'results')
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_config(self, config_path: str) -> object:
        """Load configuration from a Python file."""
        spec = importlib.util.spec_from_file_location("concept_config", config_path)
        if spec is None:
            raise ImportError(f"Could not load config from {config_path}")
        config = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not get loader for {config_path}")
        spec.loader.exec_module(config)
        return config

    def get_file_path(self, file_type: str) -> str:
        """Get standardized file paths based on concept prefix."""
        output_prefix = getattr(self.config, 'OUTPUT_FILE_PREFIX', 'default')
        paths = {
            'threads': f'{output_prefix}_reddit_threads.json',
            'analysis': f'{output_prefix}_final_analysis_results.json',
            'thematic': f'{output_prefix}_thematic_summary.json',
            'report': f'{output_prefix}_market_validation_report.md',
            'filtered_out': f'{output_prefix}_filtered_out_threads.json'
        }
        return os.path.join(self.output_dir, paths[file_type])

    @property
    def concept_name(self) -> str:
        """Get the concept name from config."""
        return getattr(self.config, 'CONCEPT_NAME', 'Unknown Concept')

    @property
    def concept_description(self) -> str:
        """Get the concept description from config."""
        return getattr(self.config, 'CONCEPT_DESCRIPTION', 'No description available.')

    @property
    def target_subreddits(self) -> list[str]:
        """Get target subreddits from config."""
        return getattr(self.config, 'TARGET_SUBREDDITS', [])

    @property
    def keywords(self) -> list[str]:
        """Get keywords from config."""
        return getattr(self.config, 'KEYWORDS', [])

    @property
    def analysis_categories(self) -> list[str]:
        """Get analysis categories from config."""
        return getattr(self.config, 'ANALYSIS_CATEGORIES', [])
