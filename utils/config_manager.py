"""Configuration management for Reddit Market Research Framework."""

import os
import importlib.util
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class ConceptConfig:
    """Dataclass representing a concept configuration."""

    # Basic concept information
    concept_name: str
    concept_description: str

    # Reddit data collection
    target_subreddits: List[str]
    keywords: List[str]

    # Analysis prompts
    filter_system_prompt: str
    filter_user_prompt_template: str
    analysis_system_prompt: str
    analysis_user_prompt_template: str

    # Synthesis configuration
    analysis_categories: Dict[str, Dict[str, str]]
    report_system_prompt: str
    report_user_prompt_template: str

    # File naming
    output_file_prefix: str

    @classmethod
    def from_module(cls, module) -> 'ConceptConfig':
        """Create a ConceptConfig from a loaded module."""
        return cls(
            concept_name=getattr(module, 'CONCEPT_NAME', 'unknown_concept'),
            concept_description=getattr(module, 'CONCEPT_DESCRIPTION', 'No description provided'),
            target_subreddits=getattr(module, 'TARGET_SUBREDDITS', []),
            keywords=getattr(module, 'KEYWORDS', []),
            filter_system_prompt=getattr(module, 'FILTER_SYSTEM_PROMPT', ''),
            filter_user_prompt_template=getattr(module, 'FILTER_USER_PROMPT_TEMPLATE', ''),
            analysis_system_prompt=getattr(module, 'ANALYSIS_SYSTEM_PROMPT', ''),
            analysis_user_prompt_template=getattr(module, 'ANALYSIS_USER_PROMPT_TEMPLATE', ''),
            analysis_categories=getattr(module, 'ANALYSIS_CATEGORIES', {}),
            report_system_prompt=getattr(module, 'REPORT_SYSTEM_PROMPT', ''),
            report_user_prompt_template=getattr(module, 'REPORT_USER_PROMPT_TEMPLATE', ''),
            output_file_prefix=getattr(module, 'OUTPUT_FILE_PREFIX', 'default')
        )

    def validate(self) -> None:
        """Validate that required fields are present and properly formatted."""
        errors = []

        if not self.concept_name:
            errors.append("CONCEPT_NAME is required")

        if not self.concept_description:
            errors.append("CONCEPT_DESCRIPTION is required")

        if not self.target_subreddits:
            errors.append("TARGET_SUBREDDITS must contain at least one subreddit")

        if not self.keywords:
            errors.append("KEYWORDS must contain at least one keyword")

        if not self.filter_system_prompt:
            errors.append("FILTER_SYSTEM_PROMPT is required")

        if not self.analysis_system_prompt:
            errors.append("ANALYSIS_SYSTEM_PROMPT is required")

        if not self.analysis_categories:
            errors.append("ANALYSIS_CATEGORIES is required")

        # Check prompt templates have required placeholders
        if '{thread_content}' not in self.filter_user_prompt_template:
            errors.append("FILTER_USER_PROMPT_TEMPLATE must contain {thread_content} placeholder")

        if '{thread_context}' not in self.analysis_user_prompt_template:
            errors.append("ANALYSIS_USER_PROMPT_TEMPLATE must contain {thread_context} placeholder")

        if '{full_context}' not in self.report_user_prompt_template:
            errors.append("REPORT_USER_PROMPT_TEMPLATE must contain {full_context} placeholder")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))


class ConfigManager:
    """Manages configuration loading and file path generation."""

    def __init__(self, config_path: str = 'concept_config.py'):
        """Initialize with a configuration file path."""
        self.config = self._load_config(config_path)
        self.output_dir = os.getenv("OUTPUT_DIR", 'results')
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_config(self, config_path: str) -> ConceptConfig:
        """Load configuration from a Python file and return as ConceptConfig dataclass."""
        spec = importlib.util.spec_from_file_location("concept_config", config_path)
        if spec is None:
            raise ImportError(f"Could not load config from {config_path}")
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not get loader for {config_path}")
        spec.loader.exec_module(module)

        # Convert module to dataclass
        config = ConceptConfig.from_module(module)

        # Validate the configuration
        config.validate()

        return config

    def get_file_path(self, file_type: str) -> str:
        """Get standardized file paths based on concept prefix."""
        paths = {
            'threads': f'{self.config.output_file_prefix}_reddit_threads.json',
            'analysis': f'{self.config.output_file_prefix}_final_analysis_results.json',
            'thematic': f'{self.config.output_file_prefix}_thematic_summary.json',
            'report': f'{self.config.output_file_prefix}_market_validation_report.md',
            'filtered_out': f'{self.config.output_file_prefix}_filtered_out_threads.json'
        }
        return os.path.join(self.output_dir, paths[file_type])

    @property
    def concept_name(self) -> str:
        """Get the concept name from config."""
        return self.config.concept_name

    @property
    def concept_description(self) -> str:
        """Get the concept description from config."""
        return self.config.concept_description

    @property
    def target_subreddits(self) -> List[str]:
        """Get target subreddits from config."""
        return self.config.target_subreddits

    @property
    def keywords(self) -> List[str]:
        """Get keywords from config."""
        return self.config.keywords

    @property
    def analysis_categories(self) -> Dict[str, Dict[str, str]]:
        """Get analysis categories from config."""
        return self.config.analysis_categories
