"""Reddit thread analysis using LLM."""

import time
from utils import TextProcessor, Config, Settings, LLMClient


class ThreadAnalyzer:
    """Handles LLM-based analysis of Reddit threads."""

    def __init__(self, config: Config, llm_client: LLMClient, settings: Settings):
        """
        Initialize the thread analyzer.

        Args:
            config: Config instance
            llm_client: LLMClient instance
            settings: Settings instance
        """
        self.config = config
        self.llm = llm_client
        self.settings = settings
        self.text_processor = TextProcessor()

    def build_thread_context(self, thread_object: dict) -> str:
        """
        Build a single string from a thread object with nested comments,
        using indentation to show hierarchy.

        Args:
            thread_object: Thread data dictionary

        Returns:
            Formatted context string
        """
        context = f"POST TITLE: {thread_object.get('title', '')}\n"
        context += f"POST BODY: {thread_object.get('selftext', '[no body]')}\n\n--- COMMENTS ---\n\n"

        # Helper function to recursively process comments
        def append_comments_recursive(comments_list: list[dict], indent_level: int = 0):
            nonlocal context
            indent = "    " * indent_level  # 4 spaces per indent level
            for comment in comments_list:
                context += f"{indent}Comment (Score: {comment.get('score', 0)}):\n"
                context += f"{indent}{comment.get('body', '')}\n{indent}---\n"
                # If there are replies, recurse
                if comment.get("replies"):
                    append_comments_recursive(comment["replies"], indent_level + 1)

        # Start the recursion on the top-level comments
        append_comments_recursive(thread_object.get("comments", []), 0)
        return context

    def filter_threads(self, threads: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Filter threads using a fast, cheap model.

        Args:
            threads: List of thread data dictionaries

        Returns:
            Tuple of (relevant_threads, irrelevant_threads)
        """
        print("\n--- STAGE 1: Filtering irrelevant threads ---")
        relevant_threads = []
        irrelevant_threads = []

        for i, thread in enumerate(threads):
            print(
                f"Filtering thread {i + 1}/{len(threads)}: {thread.get('title', 'No Title')[:80]}..."
            )

            # We only need the thread title and body for the initial filter to save tokens
            thread_content_for_filter = (
                f"Title: {thread.get('title', '')}\nBody: {thread.get('selftext', '')}"
            )

            filter_user_prompt = self.config.filter_user_prompt_template.format(
                thread_content=thread_content_for_filter
            )

            prompt_messages = [
                {"role": "system", "content": self.config.filter_system_prompt},
                {"role": "user", "content": filter_user_prompt},
            ]

            response = self.llm.call_api(prompt_messages, self.settings.filter_model)

            if response and "yes" in response.lower():
                relevant_threads.append(thread)
                print("  -> RELEVANT")
            else:
                irrelevant_threads.append(thread)
                print("  -> IRRELEVANT")

            time.sleep(self.settings.rate_limit_delay)

        print(
            f"\nFiltering complete. Found {len(relevant_threads)} potentially relevant threads."
        )
        return relevant_threads, irrelevant_threads

    def analyze_relevant_threads(self, relevant_threads: list[dict]) -> list[dict]:
        """
        Perform deep analysis on relevant threads.

        Args:
            relevant_threads: List of filtered thread data dictionaries

        Returns:
            List of analysis results
        """
        print("\n--- STAGE 2: Deep analysis of relevant threads ---")
        final_analysis_results = []

        for i, thread in enumerate(relevant_threads):
            print(
                f"Analyzing thread {i + 1}/{len(relevant_threads)}: {thread.get('title', 'No Title')[:80]}..."
            )

            thread_context = self.build_thread_context(thread)

            # Simple token check to avoid API errors
            estimated_tokens = self.text_processor.estimate_token_count(thread_context)
            if estimated_tokens > self.settings.max_tokens_for_analysis:
                print(
                    f"  -> SKIPPING: Thread context is too long ({estimated_tokens} tokens approx)."
                )
                continue

            analysis_user_prompt = self.config.analysis_user_prompt_template.format(
                thread_context=thread_context
            )

            prompt_messages = [
                {"role": "system", "content": self.config.analysis_system_prompt},
                {"role": "user", "content": analysis_user_prompt},
            ]

            # Use JSON mode for models that support it
            analysis_json = self.llm.call_with_json_response(
                prompt_messages, self.settings.analysis_model
            )

            if analysis_json is None:
                print("  -> FAILED: No response from LLM.")
                final_analysis_results.append(
                    {
                        "post_id": thread.get("id"),
                        "post_title": thread.get("title"),
                        "permalink": thread.get("permalink"),
                        "analysis_error": "No response from LLM",
                        "raw_response": None,
                    }
                )
                continue

            if "error" not in analysis_json:
                final_analysis_results.append(
                    {
                        "post_id": thread.get("id"),
                        "post_title": thread.get("title"),
                        "permalink": thread.get("permalink"),
                        "analysis": analysis_json,
                    }
                )
                print("  -> Analysis successful.")
            else:
                print(f"  -> FAILED: {analysis_json.get('error', 'Unknown error')}")
                final_analysis_results.append(
                    {
                        "post_id": thread.get("id"),
                        "post_title": thread.get("title"),
                        "permalink": thread.get("permalink"),
                        "analysis_error": analysis_json.get("error"),
                        "raw_response": analysis_json.get("raw_response"),
                    }
                )

            time.sleep(1)

        return final_analysis_results

    def analyze_threads(self, threads: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Main analysis pipeline.

        Args:
            threads: List of thread data dictionaries

        Returns:
            Tuple of (analysis_results, filtered_out_threads)
        """
        print(f"Starting LLM Analysis for concept: {self.config.concept_name}")
        print(f"Description: {self.config.concept_description}")
        print(f"Loaded {len(threads)} threads.")

        # Stage 1: Filter with cheap model
        relevant_threads, irrelevant_threads = self.filter_threads(threads)

        # Stage 2: Deep analysis with powerful model
        analysis_results = self.analyze_relevant_threads(relevant_threads)

        print("\nAnalysis complete!")
        return analysis_results, irrelevant_threads
