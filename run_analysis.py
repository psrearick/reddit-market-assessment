#!/usr/bin/env python3
"""
Runner script for the Reddit Market Research Framework.
Executes the complete analysis pipeline for a given concept configuration.
"""

import argparse
import sys
import os
import time
from reddit_fetcher import RedditFetcher
from report_synthesizer import ReportSynthesizer
from thread_analyzer import ThreadAnalyzer
from utils import ConfigManager, Settings, FileManager, LLMClient, Config


class AnalysisRunner:
    """Runner class to encapsulate the analysis pipeline logic."""

    def __init__(self, config_path: str, settings: Settings):
        self.config = self.load_concept_config(config_path)
        self.settings = settings
        self.llm_client = LLMClient(settings)
        self.step_names = {
            "fetch": "Fetching Reddit Threads",
            "analyze": "Analyzing Threads with LLM",
            "synthesize": "Synthesizing Findings and Generating Report",
        }

    def load_concept_config(self, config_path: str) -> Config:
        """Load configuration from a Python file."""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            config_manager = ConfigManager(config_path)
            self.config = config_manager.config
            print(f"Loaded configuration for: {self.config.concept_name}")
            print(f"Description: {self.config.concept_description}")

            # Ensure results directory exists
            os.makedirs(self.config.get_file_path("results"), exist_ok=True)

            return self.config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            raise

    def print_header(self, header: str) -> None:
        """Print a formatted header."""
        print(f"\n{'=' * 60}")
        print(f"{header.upper()}")
        print(f"{'=' * 60}")

    def print_step_header(self, step_name: str) -> None:
        """Print a formatted header for each step in the pipeline."""
        self.print_header(f"STEP: {step_name}")
        print(f"Running step: {step_name}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def run_steps(self, steps: dict) -> bool:
        """Run the specified steps in the analysis pipeline."""
        start_time = time.time()
        success = True

        print(f"\nStarting analysis pipeline for concept: {self.config.concept_name}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        if not steps or not any(steps.values()):
            print("No steps to run. Exiting.")
            return False

        print(
            f"Configured steps to run: {', '.join([k for k, v in steps.items() if v])}"
        )

        try:
            if steps.get("fetch", False):
                self.fetch_step()
            else:
                print("Skipping data fetching step as per configuration.")

            if steps.get("analyze", False):
                self.analyze_step()
            else:
                print("Skipping analysis step as per configuration.")

            if steps.get("synthesize", False):
                self.synthesize_step()
            else:
                print("Skipping synthesis step as per configuration.")
        except Exception as e:
            print(f"Error running analysis steps: {e}")
            raise

        elapsed_time = time.time() - start_time
        self.print_summary(elapsed_time)

        return success

    def fetch_step(self) -> None:
        """Run the data fetching step to collect Reddit threads."""
        self.print_step_header(self.step_names["fetch"])
        try:
            # Create Reddit fetcher and fetch data
            fetcher = RedditFetcher(self.config, self.settings)
            threads = fetcher.fetch_all_data()

            # Save results
            output_file = self.config.get_file_path("threads")
            FileManager.save_json(threads, output_file)
        except Exception as e:
            print(f"Error in {self.step_names['fetch']}: {e}")
            raise

        print(f"{self.step_names['fetch']} completed successfully")

    def analyze_step(self) -> None:
        """Run the analysis step."""
        self.print_step_header(self.step_names["analyze"])
        try:
            # Load threads data
            threads_file = self.config.get_file_path("threads")
            threads = FileManager.load_json(threads_file)

            if not threads:
                print(f"No threads found at {threads_file}. Exiting.")
                return

            if not isinstance(threads, list):
                print(
                    f"Invalid threads data format at {threads_file}. Expected a list of dictionaries."
                )
                return

            # Create analyzer and run analysis
            analyzer = ThreadAnalyzer(self.config, self.llm_client, self.settings)
            analysis_results, filtered_out_threads = analyzer.analyze_threads(threads)

            # Save results
            analysis_file = self.config.get_file_path("analysis")
            FileManager.save_json(analysis_results, analysis_file)
            print(f"Saved analysis results to {analysis_file}")

            # Save filtered out threads
            filtered_file = self.config.get_file_path("filtered_out")
            FileManager.save_json(filtered_out_threads, filtered_file)
            print(f"Saved filtered out threads to {filtered_file}")
        except Exception as e:
            print(f"Error in {self.step_names['analyze']}: {e}")
            raise

        print(f"{self.step_names['analyze']} completed successfully")

    def synthesize_step(self) -> None:
        """Run the synthesis step to generate the final report."""
        self.print_step_header(self.step_names["synthesize"])
        llm_client = LLMClient(self.settings)
        synthesizer = ReportSynthesizer(self.config, llm_client)
        success = synthesizer.synthesize()
        if not success:
            print(f"Error in {self.step_names['synthesize']}")
            raise
        print(f"{self.step_names['synthesize']} completed successfully")

    def print_summary(self, elapsed_time: float) -> None:
        """Print a summary of the analysis pipeline execution."""
        minutes, seconds = divmod(elapsed_time, 60)

        self.print_header("Analysis Pipeline Summary")
        print(f"Total time: {int(minutes)}m {int(seconds)}s")
        print(f"Results saved in: {self.config.get_file_path('results')}")
        print(f"Final report: {self.config.get_file_path('report')}")
        print(f"Thematic summary: {self.config.get_file_path('thematic')}")

        # Check if final report exists and show file size
        report_path = self.config.get_file_path("report")
        if not os.path.exists(report_path):
            print("Final report not found. Please check the synthesis step.")
            sys.exit(1)

        file_size = FileManager.get_file_size(report_path)
        print(f"Report size: {file_size:,} bytes")

        print("\nNext steps:")
        print("   1. Review the markdown report for key insights")
        print("   2. Examine the thematic summary for detailed breakdowns")
        print("   3. Consider adjusting your concept based on the findings")


def main():
    settings = Settings()
    settings.validate_required_settings()

    parser = argparse.ArgumentParser(
        description="Run complete Reddit market research analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_analysis.py --config my_config.py
    python run_analysis.py --config my_config.py --skip-fetch
    python run_analysis.py --config my_config.py --steps analyze,synthesize
        """,
    )

    parser.add_argument(
        "--config",
        default="config/concept_config.py",
        help="Path to concept configuration file (default: config/concept_config.py)",
    )

    parser.add_argument(
        "--steps",
        help="Comma-separated list of steps to run: fetch,analyze,synthesize (default: all)",
    )

    parser.add_argument(
        "--skip-fetch", action="store_true", help="Skip data fetching step"
    )

    parser.add_argument(
        "--skip-analyze", action="store_true", help="Skip LLM analysis step"
    )

    parser.add_argument(
        "--skip-synthesize",
        action="store_true",
        help="Skip synthesis/report generation step",
    )

    args = parser.parse_args()

    # Validate config file
    runner = AnalysisRunner(args.config, settings)

    # Determine which steps to run
    run_fetch = not args.skip_fetch
    run_analyze = not args.skip_analyze
    run_synthesize = not args.skip_synthesize

    if args.steps:
        step_names = [s.strip().lower() for s in args.steps.split(",")]
        run_fetch = "fetch" in step_names
        run_analyze = "analyze" in step_names
        run_synthesize = "synthesize" in step_names

    steps = {"fetch": run_fetch, "analyze": run_analyze, "synthesize": run_synthesize}

    # Run the analysis steps
    runner.run_steps(steps)


if __name__ == "__main__":
    main()
