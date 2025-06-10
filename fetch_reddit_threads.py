import argparse
from utils import ConfigManager, Settings, FileManager
from reddit_fetcher import RedditFetcher

def main():
    """Main function for Reddit data fetching."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch Reddit threads for market research')
    parser.add_argument('--config', default='concept_config.py',
                        help='Path to concept configuration file (default: concept_config.py)')
    args = parser.parse_args()

    try:
        # Initialize components
        config_manager = ConfigManager(args.config)
        settings = Settings()
        settings.validate_required_settings()
        file_manager = FileManager()

        # Create Reddit fetcher and fetch data
        fetcher = RedditFetcher(config_manager, settings)
        threads = fetcher.fetch_all_data()

        # Save results
        output_file = config_manager.get_file_path('threads')
        file_manager.save_json(threads, output_file)

        print(f"Successfully saved {len(threads)} threads to {output_file}")

    except Exception as e:
        print(f"Error in fetch_reddit_threads: {e}")
        raise

if __name__ == "__main__":
    main()
