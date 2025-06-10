#!/usr/bin/env python3
"""
Runner script for the Reddit Market Research Framework.
Executes the complete analysis pipeline for a given concept configuration.
"""

import argparse
import subprocess
import sys
import os
import time
import importlib.util

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

def run_script(script_name, config_path, step_name):
    """Run a script with the given config and handle errors."""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}")

    cmd = [sys.executable, script_name, '--config', config_path]

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"{step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{step_name} failed with return code {e.returncode}")
        print(f"Command: {' '.join(cmd)}")
        return False
    except FileNotFoundError:
        print(f"Script not found: {script_name}")
        print("Make sure all scripts are in the current directory")
        return False

def check_prerequisites():
    """Check if required files and dependencies exist."""
    required_scripts = [
        'fetch_reddit_threads.py',
        'reddit_llm_analyzer.py',
        'synthesize_llm_findings.py'
    ]

    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)

    if missing_scripts:
        print("Missing required scripts:")
        for script in missing_scripts:
            print(f"   - {script}")
        return False

    # Check for .env file
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Make sure you have set up your API keys.")
        print("   See README.md for setup instructions.")

    return True

def main():
    parser = argparse.ArgumentParser(
        description='Run complete Reddit market research analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py --config concept_config.py
  python run_analysis.py --config example_finance_config.py --skip-fetch
  python run_analysis.py --config my_config.py --steps analyze,synthesize
        """
    )

    parser.add_argument('--config', default='concept_config.py',
                        help='Path to concept configuration file (default: concept_config.py)')

    parser.add_argument('--steps',
                        help='Comma-separated list of steps to run: fetch,analyze,synthesize (default: all)')

    parser.add_argument('--skip-fetch', action='store_true',
                        help='Skip data fetching step (useful if you already have data)')

    parser.add_argument('--skip-analyze', action='store_true',
                        help='Skip LLM analysis step')

    parser.add_argument('--skip-synthesize', action='store_true',
                        help='Skip synthesis/report generation step')

    args = parser.parse_args()

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Validate config file
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)

    try:
        config = load_concept_config(args.config)
        print(f"Loaded configuration for: {config.CONCEPT_NAME}")
        print(f"Description: {config.CONCEPT_DESCRIPTION}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Determine which steps to run
    if args.steps:
        step_names = [s.strip().lower() for s in args.steps.split(',')]
        run_fetch = 'fetch' in step_names
        run_analyze = 'analyze' in step_names
        run_synthesize = 'synthesize' in step_names
    else:
        run_fetch = not args.skip_fetch
        run_analyze = not args.skip_analyze
        run_synthesize = not args.skip_synthesize

    # Ensure results directory exists
    os.makedirs('results', exist_ok=True)

    start_time = time.time()
    success = True

    print(f"\nStarting analysis pipeline for concept: {config.CONCEPT_NAME}")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Fetch Reddit data
    if run_fetch:
        success = run_script('fetch_reddit_threads.py', args.config,
                            "Fetching Reddit threads")
        if not success:
            print("\nPipeline failed at data fetching step")
            sys.exit(1)
    else:
        print("\nSkipping data fetching step")

    # Step 2: LLM Analysis
    if run_analyze:
        success = run_script('reddit_llm_analyzer.py', args.config,
                            "Analyzing threads with LLM")
        if not success:
            print("\nPipeline failed at LLM analysis step")
            sys.exit(1)
    else:
        print("\nSkipping LLM analysis step")

    # Step 3: Synthesis and Report Generation
    if run_synthesize:
        success = run_script('synthesize_llm_findings.py', args.config,
                            "Synthesizing findings and generating report")
        if not success:
            print("\nPipeline failed at synthesis step")
            sys.exit(1)
    else:
        print("\nSkipping synthesis step")

    # Success!
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)

    print(f"\n{'='*60}")
    print("ANALYSIS PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"Total time: {int(minutes)}m {int(seconds)}s")
    print(f"Results saved in: results/")
    print(f"Final report: results/{config.OUTPUT_FILE_PREFIX}_market_validation_report.md")
    print(f"Thematic summary: results/{config.OUTPUT_FILE_PREFIX}_thematic_summary.json")

    # Check if final report exists and show file size
    report_path = f"results/{config.OUTPUT_FILE_PREFIX}_market_validation_report.md"
    if os.path.exists(report_path):
        file_size = os.path.getsize(report_path)
        print(f"Report size: {file_size:,} bytes")

    print("\nNext steps:")
    print("   1. Review the markdown report for key insights")
    print("   2. Examine the thematic summary for detailed breakdowns")
    print("   3. Consider adjusting your concept based on the findings")

if __name__ == "__main__":
    main()
