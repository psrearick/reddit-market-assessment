import json
import os
import requests
import time
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found.")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Stage 1: Fast, cheap model for filtering
FILTER_MODEL = "mistralai/mistral-nemo"
# Stage 2: Powerful, more expensive model for deep analysis
ANALYSIS_MODEL = "google/gemini-2.5-flash-preview-05-20"

# File paths
THREADS_FILE = 'reddit_threads.json'
OUTPUT_DIR = 'results'

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

    threads = load_json_data(os.path.join(OUTPUT_DIR, THREADS_FILE))

    if not threads:
        print("No threads found. Exiting.")
        return

    print(f"Loaded {len(threads)} threads.")

    # --- STAGE 1: FILTERING with a Cheap Model ---
    print("\n--- STAGE 1: Filtering irrelevant threads ---")
    relevant_threads = []
    irrelevant_threads = []

    filter_system_prompt = "You are a highly efficient text classifier. Your task is to determine if a Reddit thread is relevant to the topic of teaching technology to non-tech-savvy individuals (like seniors) or the challenges faced by them or their helpers. Answer with only 'yes' or 'no'."

    for i, thread in enumerate(threads):
        print(f"Filtering thread {i+1}/{len(threads)}: {thread.get('title', 'No Title')[:80]}...")

        # We only need the thread title and body for the initial filter to save tokens
        thread_content_for_filter = f"Title: {thread.get('title', '')}\nBody: {thread.get('selftext', '')}"

        filter_user_prompt = f"Is the following Reddit thread relevant to the topic of tech challenges for seniors, digital literacy for beginners, or people helping them with technology?\n\n---\n{thread_content_for_filter}\n---"

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
    with open(os.path.join(OUTPUT_DIR, 'filtered_out_threads.json'), 'w') as f:
        json.dump(irrelevant_threads, f, indent=2)

    # --- STAGE 2: DEEP ANALYSIS with a Powerful Model ---
    print("\n--- STAGE 2: Deep analysis of relevant threads ---")
    final_analysis_results = []

    analysis_system_prompt = "You are a market research analyst. Your goal is to extract structured insights from a Reddit thread about technology challenges for non-tech-savvy individuals. Provide your analysis in a structured JSON format."

    # This prompt asks for a single JSON object, which is much more efficient.
    analysis_user_prompt_template = """
    Analyze the following Reddit thread (post and comments). Based on the entire context, provide a JSON object with the following keys:
    - "main_pain_points": A list of strings, each describing a core technology-related frustration for the non-tech-savvy person.
    - "helper_challenges": A list of strings, each describing a challenge faced by the person trying to help/teach.
    - "emotional_tone": A string describing the overall emotional sentiment (e.g., "Frustration and anxiety", "Empathetic but stressed").
    - "mentioned_solutions": A list of strings for any current solutions or workarounds mentioned, including their perceived flaws.
    - "unmet_needs": A list of strings describing what users seem to be missing or wishing for in a solution.
    - "key_tech_topics": A list of specific technologies or apps causing issues (e.g., "Zoom", "Phishing emails", "Photo sharing").
    - "is_high_value": A boolean (true/false) indicating if this thread contains a rich, detailed discussion highly relevant to building a tech education platform.

    Here is the thread:
    ---
    {thread_context}
    ---
    """

    for i, thread in enumerate(relevant_threads):
        print(f"Analyzing thread {i+1}/{len(relevant_threads)}: {thread.get('title', 'No Title')[:80]}...")

        thread_context = build_thread_context(thread)

        # Simple token check to avoid API errors
        if len(thread_context) / 4 > MAX_TOKENS_FOR_ANALYSIS:
            print(f"  -> SKIPPING: Thread context is too long ({len(thread_context)/4:.0f} tokens approx).")
            continue

        prompt_messages = [
            {"role": "system", "content": analysis_system_prompt},
            {"role": "user", "content": analysis_user_prompt_template.format(thread_context=thread_context)}
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
            with open(os.path.join(OUTPUT_DIR, 'final_analysis_results.json'), 'w') as f:
                json.dump(final_analysis_results, f, indent=2)
            print("  -> Saved progress to final_analysis_results.json")

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
