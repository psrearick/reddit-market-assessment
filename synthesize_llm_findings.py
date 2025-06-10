import json
import os
import requests
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
parser = argparse.ArgumentParser(description='Synthesize LLM analysis results into final report')
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

# Use a powerful model for these complex synthesis tasks
SYNTHESIS_MODEL = "google/gemini-2.5-pro-preview"

OUTPUT_DIR = 'results'
# Input file from the previous script - now concept-specific
ANALYSIS_FILE = os.path.join(OUTPUT_DIR, f'{config.OUTPUT_FILE_PREFIX}_final_analysis_results.json')
# Output files - now concept-specific
THEMATIC_SUMMARY_FILE = os.path.join(OUTPUT_DIR, f'{config.OUTPUT_FILE_PREFIX}_thematic_summary.json')
FINAL_REPORT_FILE = os.path.join(OUTPUT_DIR, f'{config.OUTPUT_FILE_PREFIX}_market_validation_report.md')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions ---
def load_json_data(filepath):
    """Loads data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return None

def call_llm_api(prompt_messages, model=SYNTHESIS_MODEL, response_format=None):
    """Sends a request to the OpenRouter API."""
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {"model": model, "messages": prompt_messages}
    if response_format == "json_object":
        data["response_format"] = {"type": "json_object"}

    response = None
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=180) # Longer timeout for big tasks
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return None
    except (KeyError, IndexError):
        print(f"Unexpected API response format: {response.text if response else 'No response'}")
        return None

# --- Phase 0: Data Aggregation ---

def aggregate_data_from_analysis(analysis_data):
    """Aggregates all lists from the analysis file into master lists."""
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

# --- Phase 1: AI-Powered Thematic Clustering ---

def get_thematic_summary(items_list, category_name, item_description):
    """Uses an LLM to cluster a list of strings into themes and count them."""
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

    response_str = call_llm_api(messages, response_format="json_object")

    if response_str:
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            print(f"  -> ERROR: Failed to decode JSON from LLM response for '{category_name}'.")
            return {"error": "Failed to parse LLM response", "raw_response": response_str}
    return {"error": "No response from LLM"}

# --- Phase 2: AI-Powered Report Generation ---

def generate_final_report(thematic_summaries):
    """Uses an LLM to write a final market validation report from the thematic summaries."""
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

    system_prompt = config.REPORT_SYSTEM_PROMPT
    user_prompt = config.REPORT_USER_PROMPT_TEMPLATE.format(full_context=full_context)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    report_content = call_llm_api(messages)
    return report_content if report_content else "# Report Generation Failed"

# --- Main Execution ---

def main():
    print("Starting Synthesis of LLM Analysis...")
    print(f"Synthesizing results for concept: {config.CONCEPT_NAME}")
    print(f"Description: {config.CONCEPT_DESCRIPTION}")

    analysis_data = load_json_data(ANALYSIS_FILE)
    if not analysis_data:
        return

    # Phase 0: Aggregate all the data into master lists
    aggregated_data = aggregate_data_from_analysis(analysis_data)

    # Phase 1: Perform thematic analysis on each category from config
    thematic_summaries = {}
    for category_key, category_info in config.ANALYSIS_CATEGORIES.items():
        thematic_summaries[category_key] = get_thematic_summary(
            aggregated_data[category_key],
            category_info['name'],
            category_info['description']
        )

    # Add the non-LLM aggregated data
    thematic_summaries['high_value_threads'] = aggregated_data['high_value_threads']

    # Save the structured thematic summary
    with open(THEMATIC_SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(thematic_summaries, f, indent=4)
    print(f"\nSaved thematic summary to {THEMATIC_SUMMARY_FILE}")

    # Phase 2: Generate the final human-readable report using config prompts
    final_report = generate_final_report(thematic_summaries)

    # Save the final report as a Markdown file
    with open(FINAL_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_report)
    print(f"Saved final market validation report to {FINAL_REPORT_FILE}")

    print("\nSynthesis complete!")

if __name__ == "__main__":
    main()
