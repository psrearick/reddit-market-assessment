"""Report synthesis from LLM analysis results."""

from utils import FileManager, Config, LLMClient


class ReportSynthesizer:
    """Handles synthesis of analysis results into final reports."""

    def __init__(self, config : Config, llm_client: LLMClient):
        """
        Initialize the report synthesizer.

        Args:
            config_manager: ConfigManager instance
            llm_client: LLMClient instance
        """
        self.config = config
        self.llm = llm_client
        self.file_manager = FileManager()

    def aggregate_data(self, analysis_data : list[dict]) -> dict:
        """
        Aggregate all lists from the analysis file into master lists.

        Args:
            analysis_data: List of analysis result dictionaries

        Returns:
            Dictionary with aggregated data
        """
        aggregated = {
            "main_pain_points": [],
            "helper_challenges": [],
            "mentioned_solutions": [],
            "unmet_needs": [],
            "key_tech_topics": [],
        }
        high_value_threads = []

        for item in analysis_data:
            analysis = item.get('analysis', {})
            # Skip items that had errors during the previous stage
            if not isinstance(analysis, dict):
                continue

            for key in aggregated.keys():
                # Extend the master list with the list from the current item
                aggregated[key].extend(analysis.get(key, []))

            if analysis.get('is_high_value'):
                high_value_threads.append(item.get('permalink'))

        print("Data Aggregation Complete:")
        for key, value in aggregated.items():
            print(f"  - Found {len(value)} total items for '{key}'")

        aggregated['high_value_threads'] = high_value_threads
        return aggregated

    def perform_thematic_analysis(self, items_list: list[str], category_name: str, item_description: str) -> dict | None:
        """
        Use an LLM to cluster a list of strings into themes and count them.

        Args:
            items_list: List of items to analyze
            category_name: Name of the category being analyzed
            item_description: Description of what the items represent

        Returns:
            Thematic analysis results
        """
        print(f"\nPerforming thematic analysis for '{category_name}'...")
        if not items_list:
            print("  -> No items to analyze.")
            return {}

        # Create a string of all items, separated by newlines
        items_str = "\n".join(f"- {item}" for item in items_list)

        system_prompt = "You are a data analyst specializing in qualitative data. Your task is to perform thematic analysis on a list of user-provided items, group them into high-level categories, and count the occurrences for each category."

        user_prompt = f"""
        Analyze the following list of raw '{item_description}'. Group similar items into meaningful, high-level themes.

        For each theme, provide:
        1. A concise `theme_name`.
        2. The `count` of how many raw items fall into that theme.
        3. A list of `example_items` (up to 3) from the raw data that best represent the theme.

        Return your analysis as a JSON object, which is a list of these themes, sorted by count in descending order.
        Example format:
        [
            {{
                "theme_name": "Example Theme 1",
                "count": 42,
                "example_items": ["Raw item A", "Raw item B"]
            }},
            {{
                "theme_name": "Example Theme 2",
                "count": 19,
                "example_items": ["Raw item C", "Raw item D", "Raw item E"]
            }}
        ]

        Here is the list of raw items to analyze:
        ---
        {items_str}
        ---
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self.llm.call_with_json_response(messages, self.llm.settings.synthesis_model)

    def generate_report(self, thematic_summaries : dict) -> str:
        """
        Use an LLM to write a final market validation report from thematic summaries.

        Args:
            thematic_summaries: Dictionary of thematic analysis results

        Returns:
            Generated report content string
        """
        print("\nGenerating final market validation report...")

        # Build a comprehensive prompt with all our structured data
        full_context = ""
        for key, summary in thematic_summaries.items():
            full_context += f"## Thematic Summary for: {key}\n\n"
            if isinstance(summary, list) and summary:
                for theme in summary:
                    if isinstance(theme, dict):
                        full_context += f"- **Theme:** {theme.get('theme_name', 'N/A')} (Count: {theme.get('count', 0)})\n"
                        full_context += f"  - Examples: {'; '.join(theme.get('example_items', []))}\n"
                    else:
                        full_context += f"- **Item:** {theme}\n"
            elif key == 'high_value_threads':
                full_context += f"Found {len(summary)} high-value discussion threads.\n"
            elif isinstance(summary, dict) and 'error' in summary:
                full_context += f"Error processing {key}: {summary.get('error', 'Unknown error')}\n"
            else:
                full_context += f"Data type: {type(summary).__name__}, Length: {len(summary) if hasattr(summary, '__len__') else 'N/A'}\n"
            full_context += "\n---\n"

        system_prompt = self.config.report_system_prompt
        user_prompt = self.config.report_user_prompt_template.format(full_context=full_context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        report_content = self.llm.call_api(messages, self.llm.settings.synthesis_model)
        return report_content if report_content else "# Report Generation Failed"

    def save_results(self, thematic_summaries: dict, report: str) -> None:
        """
        Save thematic summaries and final report.

        Args:
            thematic_summaries: Dictionary of thematic analysis results
            report: Generated report content string
        """
        # Save the structured thematic summary
        thematic_file = self.config.get_file_path('thematic')
        self.file_manager.save_json(thematic_summaries, thematic_file)
        print(f"\nSaved thematic summary to {thematic_file}")

        # Save the final report as a Markdown file
        report_file = self.config.get_file_path('report')
        self.file_manager.save_text(report, report_file)
        print(f"Saved final market validation report to {report_file}")

    def synthesize(self) -> bool:
        """
        Main synthesis pipeline.

        Returns:
            True if successful, False otherwise
        """
        print("Starting Synthesis of LLM Analysis...")
        print(f"Synthesizing results for concept: {self.config.concept_name}")
        print(f"Description: {self.config.concept_description}")

        # Load analysis data
        analysis_file = self.config.get_file_path('analysis')
        analysis_data = self.file_manager.load_json(analysis_file)
        if not analysis_data:
            print(f"No analysis data found at {analysis_file}")
            return False
        if not isinstance(analysis_data, list):
            print(f"Invalid analysis data format at {analysis_file}. Expected a list of dictionaries.")
            return False

        # Phase 0: Aggregate all the data into master lists
        aggregated_data = self.aggregate_data(analysis_data)

        # Phase 1: Perform thematic analysis on each category from config
        thematic_summaries = {}
        for category_key, category_info in self.config.analysis_categories.items():
            thematic_summaries[category_key] = self.perform_thematic_analysis(
                aggregated_data[category_key],
                category_info['name'],
                category_info['description']
            )

        # Add the non-LLM aggregated data
        thematic_summaries['high_value_threads'] = aggregated_data['high_value_threads']

        # Phase 2: Generate the final human-readable report using config prompts
        final_report = self.generate_report(thematic_summaries)

        # Save results
        self.save_results(thematic_summaries, final_report)

        print("\nSynthesis complete!")
        return True
