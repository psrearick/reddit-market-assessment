import argparse
from utils import ConfigManager, Settings, LLMClient, FileManager
from thread_analyzer import ThreadAnalyzer

def main():
    """Main function for Reddit thread analysis."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze Reddit threads with LLM for market research')
    parser.add_argument('--config', default='concept_config.py',
                        help='Path to concept configuration file (default: concept_config.py)')
    args = parser.parse_args()

    try:
        # Initialize components
        config_manager = ConfigManager(args.config)
        settings = Settings()
        settings.validate_required_settings()
        llm_client = LLMClient(settings)
        file_manager = FileManager()

        # Load threads data
        threads_file = config_manager.get_file_path('threads')
        threads = file_manager.load_json(threads_file)

        if not threads:
            print(f"No threads found at {threads_file}. Exiting.")
            return

        if not isinstance(threads, list):
            print(f"Invalid threads data format at {threads_file}. Expected a list of dictionaries.")
            return

        # Create analyzer and run analysis
        analyzer = ThreadAnalyzer(config_manager, llm_client, settings)
        analysis_results, filtered_out_threads = analyzer.analyze_threads(threads)

        # Save results
        analysis_file = config_manager.get_file_path('analysis')
        file_manager.save_json(analysis_results, analysis_file)
        print(f"Saved analysis results to {analysis_file}")

        # Save filtered out threads
        filtered_file = config_manager.get_file_path('filtered_out')
        file_manager.save_json(filtered_out_threads, filtered_file)
        print(f"Saved filtered out threads to {filtered_file}")

    except Exception as e:
        print(f"Error in reddit_llm_analyzer: {e}")
        raise

if __name__ == "__main__":
    main()
