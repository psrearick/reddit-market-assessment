import json
import os
import requests
import time
import argparse
import importlib.util
from dotenv import load_dotenv

# Load concept configuration
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

# Parse command line arguments
parser = argparse.ArgumentParser(description='Analyze Reddit threads with LLM for market research')
parser.add_argument('--config', default='concept_config.py',
                    help='Path to concept configuration file (default: concept_config.py)')
args = parser.parse_args()

# Load configuration
config = load_concept_config(args.config)

# --- Configuration ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found.")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Stage 1: Fast, cheap model for filtering
FILTER_MODEL = os.getenv("ANALYSIS_FILTER_MODEL")
# Stage 2: Powerful, more expensive model for deep analysis
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL")

# File paths - using concept-specific naming
THREADS_FILE = f'{config.OUTPUT_FILE_PREFIX}_reddit_threads.json'
OUTPUT_DIR = os.getenv("OUTPUT_DIR", 'results')

# Limits
MAX_COMMENTS_PER_POST = 30 # Limit the number of comments per post to keep context manageable
MAX_TOKENS_FOR_ANALYSIS = 16000 # Max tokens for the combined post+comments content to send to the analysis model

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions ---

def load_json_data(filepath):
    """Loads data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return []

def call_llm_api(prompt_messages, model, response_format=None):
    """Sends a request to the OpenRouter API."""
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {
        "model": model,
        "messages": prompt_messages,
    }
    # For models that support JSON mode (like newer OpenAI models)
    if response_format == "json_object":
        data["response_format"] = {"type": "json_object"}

    response = None
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        if response and response.status_code == 429:
            print("Rate limit hit. Waiting...")
            time.sleep(60)
        return None
    except (KeyError, IndexError):
        print(f"Unexpected API response format: {response.text if response else 'No response'}")
        return None

def build_thread_context(thread_object):
    """
    Builds a single string from a thread object with nested comments,
    using indentation to show hierarchy.
    """
    context = f"POST TITLE: {thread_object.get('title', '')}\n"
    context += f"POST BODY: {thread_object.get('selftext', '[no body]')}\n\n--- COMMENTS ---\n\n"

    # Helper function to recursively process comments
    def append_comments_recursive(comments_list, indent_level):
        nonlocal context
        indent = "    " * indent_level # 4 spaces per indent level
        for comment in comments_list:
            context += f"{indent}Comment (Score: {comment.get('score', 0)}):\n"
            context += f"{indent}{comment.get('body', '')}\n{indent}---\n"
            # If there are replies, recurse
            if comment.get('replies'):
                append_comments_recursive(comment['replies'], indent_level + 1)

    # Start the recursion on the top-level comments
    append_comments_recursive(thread_object.get('comments', []), 0)
    return context

# --- Main Logic ---

def main():
    print("Starting LLM Analysis...")
    print(f"Analyzing concept: {config.CONCEPT_NAME}")
    print(f"Description: {config.CONCEPT_DESCRIPTION}")

    threads = load_json_data(os.path.join(OUTPUT_DIR, THREADS_FILE))

    if not threads:
        print("No threads found. Exiting.")
        return

    print(f"Loaded {len(threads)} threads.")

    # --- STAGE 1: FILTERING with a Cheap Model ---
    print("\n--- STAGE 1: Filtering irrelevant threads ---")
    relevant_threads = []
    irrelevant_threads = []

    filter_system_prompt = config.FILTER_SYSTEM_PROMPT

    for i, thread in enumerate(threads):
        print(f"Filtering thread {i+1}/{len(threads)}: {thread.get('title', 'No Title')[:80]}...")

        # We only need the thread title and body for the initial filter to save tokens
        thread_content_for_filter = f"Title: {thread.get('title', '')}\nBody: {thread.get('selftext', '')}"

        filter_user_prompt = config.FILTER_USER_PROMPT_TEMPLATE.format(thread_content=thread_content_for_filter)

        prompt_messages = [
            {"role": "system", "content": filter_system_prompt},
            {"role": "user", "content": filter_user_prompt}
        ]

        response = call_llm_api(prompt_messages, FILTER_MODEL)

        if response and 'yes' in response.lower():
            relevant_threads.append(thread)
            print("  -> RELEVANT")
        else:
            irrelevant_threads.append(thread)
            print("  -> IRRELEVANT")

        time.sleep(0.5) # Be nice to the API

    print(f"\nFiltering complete. Found {len(relevant_threads)} potentially relevant threads.")
    with open(os.path.join(OUTPUT_DIR, f'{config.OUTPUT_FILE_PREFIX}_filtered_out_threads.json'), 'w') as f:
        json.dump(irrelevant_threads, f, indent=2)

    # --- STAGE 2: DEEP ANALYSIS with a Powerful Model ---
    print("\n--- STAGE 2: Deep analysis of relevant threads ---")
    final_analysis_results = []

    analysis_system_prompt = config.ANALYSIS_SYSTEM_PROMPT

    for i, thread in enumerate(relevant_threads):
        print(f"Analyzing thread {i+1}/{len(relevant_threads)}: {thread.get('title', 'No Title')[:80]}...")

        thread_context = build_thread_context(thread)

        # Simple token check to avoid API errors
        if len(thread_context) / 4 > MAX_TOKENS_FOR_ANALYSIS:
            print(f"  -> SKIPPING: Thread context is too long ({len(thread_context)/4:.0f} tokens approx).")
            continue

        analysis_user_prompt = config.ANALYSIS_USER_PROMPT_TEMPLATE.format(thread_context=thread_context)

        prompt_messages = [
            {"role": "system", "content": analysis_system_prompt},
            {"role": "user", "content": analysis_user_prompt}
        ]

        # Use JSON mode for models that support it
        response_str = call_llm_api(prompt_messages, ANALYSIS_MODEL, response_format="json_object")

        if response_str:
            try:
                # The response should be a JSON string, so we parse it
                analysis_json = json.loads(response_str)
                final_analysis_results.append({
                    "post_id": thread.get('id'),
                    "post_title": thread.get('title'),
                    "permalink": thread.get('permalink'),
                    "analysis": analysis_json
                })
                print("  -> Analysis successful.")
            except json.JSONDecodeError:
                print("  -> FAILED to parse JSON response from LLM. Saving raw response.")
                final_analysis_results.append({
                    "post_id": thread.get('id'),
                    "post_title": thread.get('title'),
                    "permalink": thread.get('permalink'),
                    "analysis_error": "JSON_DECODE_ERROR",
                    "raw_response": response_str
                })
        else:
            print("  -> FAILED to get a response from the analysis model.")

        time.sleep(1)

        # Save progress
        if (i + 1) % 5 == 0 or (i + 1) == len(relevant_threads):
            with open(os.path.join(OUTPUT_DIR, f'{config.OUTPUT_FILE_PREFIX}_final_analysis_results.json'), 'w') as f:
                json.dump(final_analysis_results, f, indent=2)
            print(f"  -> Saved progress to {config.OUTPUT_FILE_PREFIX}_final_analysis_results.json")

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
