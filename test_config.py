#!/usr/bin/env python3
"""
Test script to validate configuration loading and basic functionality.
"""

import importlib.util
import os
import sys

def load_concept_config(config_path):
    """Load configuration from a Python file."""
    spec = importlib.util.spec_from_file_location("concept_config", config_path)
    if spec is None:
        raise ImportError(f"Could not load config from {config_path}")
    config = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Could not get loader for {config_path}")
    spec.loader.exec_module(config)
    return config

def test_config(config_path):
    """Test that a configuration file is valid."""
    print(f"\n{'='*60}")
    print(f"Testing configuration: {config_path}")
    print(f"{'='*60}")

    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return False

    try:
        config = load_concept_config(config_path)

        # Check required attributes
        required_attrs = [
            'CONCEPT_NAME', 'CONCEPT_DESCRIPTION', 'TARGET_SUBREDDITS', 'KEYWORDS',
            'FILTER_SYSTEM_PROMPT', 'FILTER_USER_PROMPT_TEMPLATE',
            'ANALYSIS_SYSTEM_PROMPT', 'ANALYSIS_USER_PROMPT_TEMPLATE',
            'ANALYSIS_CATEGORIES', 'REPORT_SYSTEM_PROMPT', 'REPORT_USER_PROMPT_TEMPLATE',
            'OUTPUT_FILE_PREFIX'
        ]

        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(config, attr):
                missing_attrs.append(attr)

        if missing_attrs:
            print(f"Missing required attributes: {missing_attrs}")
            return False

        # Validate basic structure
        print(f"Concept Name: {config.CONCEPT_NAME}")
        print(f"Description: {config.CONCEPT_DESCRIPTION}")
        print(f"Target Subreddits: {len(config.TARGET_SUBREDDITS)} subreddits")
        print(f"Keywords: {len(config.KEYWORDS)} keywords")
        print(f"Analysis Categories: {len(config.ANALYSIS_CATEGORIES)} categories")
        print(f"Output Prefix: {config.OUTPUT_FILE_PREFIX}")

        # Test prompt templates
        try:
            test_format = config.FILTER_USER_PROMPT_TEMPLATE.format(thread_content="test")
            test_format = config.ANALYSIS_USER_PROMPT_TEMPLATE.format(thread_context="test")
            test_format = config.REPORT_USER_PROMPT_TEMPLATE.format(full_context="test")
            print("Prompt templates are valid")
        except KeyError as e:
            print(f"Invalid prompt template: missing {e}")
            print(f"{'='*60}")
            return False

        print("Configuration is valid!")
        print(f"{'='*60}")
        return True

    except Exception as e:
        print(f"Error loading configuration: {e}")
        print(f"{'='*60}")
        return False

def main():
    """Test all available configurations."""
    # Find all config files automatically
    import glob
    configs_to_test = glob.glob('config/*_config.py')
    configs_to_test = list(set(configs_to_test))  # Remove duplicates

    # Filter out test scripts and other non-config files
    configs_to_test = [f for f in configs_to_test if not f.startswith('test_')]
    configs_to_test.sort()

    print("Testing configuration files...\n")

    all_passed = True
    for config_path in configs_to_test:
        if os.path.exists(config_path):
            success = test_config(config_path)
            all_passed = all_passed and success
            print()
        else:
            print(f"Skipping {config_path} (file not found)")
            print()

    if all_passed:
        print("All configuration tests passed!")

        # Test the runner script help
        print(f"\n{'='*60}")
        print("Testing runner script accessibility...")
        import subprocess
        try:
            result = subprocess.run([sys.executable, 'run_analysis.py', '--help'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print("Runner script is accessible")
            else:
                print("Runner script has issues")
        except Exception as e:
            print(f"Error testing runner script: {e}")

    else:
        print("Some configuration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
