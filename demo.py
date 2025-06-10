#!/usr/bin/env python3
"""
Demo script showing how to use the Reddit Market Research Framework
with different product concepts.
"""

import os
import sys

def demo_concept_switching():
    """Demonstrate how easy it is to switch between different product concepts."""

    print("Reddit Market Research Framework Demo")
    print("=" * 60)
    print()

    print("This framework allows you to analyze market potential for any product concept")
    print("by simply creating a configuration file. Here are the example concepts included:")
    print()

    # Show available configurations
    concepts = {
        'concept_config.py': 'Tech Education Platform for Seniors',
        'example_finance_config.py': 'AI-Powered Personal Finance Advisor',
        'example_smarthome_config.py': 'Family-Focused Smart Home Automation'
    }

    for i, (config_file, description) in enumerate(concepts.items(), 1):
        if os.path.exists(config_file):
            print(f"{i}. {description}")
            print(f"   Config: {config_file}")

            # Load and show key details
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_file)
                if spec is not None and spec.loader is not None:
                    config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config)
                else:
                    raise ImportError(f"Could not load spec for {config_file}")

                print(f"   Subreddits: {', '.join(config.TARGET_SUBREDDITS[:3])}{'...' if len(config.TARGET_SUBREDDITS) > 3 else ''}")
                print(f"   Keywords: {len(config.KEYWORDS)} terms")
                print()
            except Exception as e:
                print(f"   (Error loading config: {e})")
                print()

    print("To analyze any of these concepts, simply run:")
    print()
    for config_file in concepts.keys():
        if os.path.exists(config_file):
            print(f"   python3 run_analysis.py --config {config_file}")
    print()

    print("To create your own concept:")
    print("1. Copy one of the example config files")
    print("2. Modify the concept details, subreddits, and keywords")
    print("3. Adjust the analysis prompts for your specific product")
    print("4. Run the analysis with your new config file")
    print()

    print("All results will be saved with your concept name as prefix:")
    print("   results/{concept_name}_reddit_threads.json")
    print("   results/{concept_name}_final_analysis_results.json")
    print("   results/{concept_name}_thematic_summary.json")
    print("   results/{concept_name}_market_validation_report.md")
    print()

    print("Example analysis commands:")
    print("   # Run complete pipeline")
    print("   python3 run_analysis.py --config example_finance_config.py")
    print()
    print("   # Run only analysis and synthesis (skip data collection)")
    print("   python3 run_analysis.py --config concept_config.py --skip-fetch")
    print()
    print("   # Run specific steps")
    print("   python3 run_analysis.py --config example_smarthome_config.py --steps analyze,synthesize")
    print()

def show_file_structure():
    """Show the project file structure."""
    print("Project Structure:")
    print("=" * 30)

    files = [
        ("Core Scripts", [
            "run_analysis.py - Main pipeline runner",
            "fetch_reddit_threads.py - Data collection",
            "reddit_llm_analyzer.py - LLM analysis",
            "synthesize_llm_findings.py - Report generation"
        ]),
        ("Configuration Examples", [
            "concept_config.py - Tech education platform",
            "example_finance_config.py - Personal finance app",
            "example_smarthome_config.py - Smart home for families"
        ]),
        ("Utilities", [
            "test_config.py - Configuration validator",
            "README.md - Complete documentation"
        ]),
        ("Output Directory", [
            "results/ - All analysis outputs go here"
        ])
    ]

    for category, file_list in files:
        print(f"\n{category}:")
        for file_desc in file_list:
            filename = file_desc.split(' - ')[0]
            desc = file_desc.split(' - ')[1] if ' - ' in file_desc else ''
            exists = "Exists:" if os.path.exists(filename) else "Missing:"
            file_desc = f"{filename} - {desc}" if desc else filename
            print(f"  {exists} {file_desc}")

def main():
    """Main demo function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--structure':
        show_file_structure()
    else:
        demo_concept_switching()

    print("For complete documentation, see README.md")
    print("To test all configurations, run: python3 test_config.py")

if __name__ == "__main__":
    main()
