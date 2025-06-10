# Reddit Market Research Framework

A flexible framework for conducting market research by analyzing Reddit discussions for different product concepts.

## Overview

This framework allows you to analyze Reddit discussions to validate market opportunities for various product concepts. The system is designed to be concept-agnostic - you simply create a configuration file for your specific product idea, and the same scripts will collect, analyze, and synthesize data tailored to your concept.

## Architecture

The framework consists of three main scripts:

1. **`fetch_reddit_threads.py`** - Collects Reddit posts and comments based on your concept configuration
2. **`reddit_llm_analyzer.py`** - Uses LLM to filter and analyze threads for market insights
3. **`synthesize_llm_findings.py`** - Generates thematic summaries and final market validation report

All concept-specific elements (subreddits, keywords, analysis prompts) are externalized into configuration files.

## Setup

### Prerequisites

1. Python 3.8+
2. Required packages (install via pip):
   ```bash
   pip install praw python-dotenv requests
   ```

### API Keys

Create a `.env` file in the project root with:

```env
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

# OpenRouter API key for LLM analysis
OPENROUTER_API_KEY=your_openrouter_api_key
```

**Getting Reddit API credentials:**
1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (select "script" type)
3. Use the client ID and secret in your .env file

**Getting OpenRouter API key:**
1. Sign up at https://openrouter.ai/
2. Add credits to your account
3. Generate an API key

## Usage

### Step 1: Create a Concept Configuration

Create a configuration file for your product concept (see `concept_config.py` for the tech education example):

```python
# my_concept_config.py
CONCEPT_NAME = "my_product_idea"
CONCEPT_DESCRIPTION = "Description of your product concept"

TARGET_SUBREDDITS = ['relevant', 'subreddits', 'for_your_concept']
KEYWORDS = ['keyword1', 'keyword2', 'etc']

# ... (see existing config files for full structure)
```

### Step 2: Run the Analysis Pipeline

You can run each step individually or use the provided runner script.

**Option A: Run individual scripts**
```bash
# Step 1: Collect Reddit data
python fetch_reddit_threads.py --config my_concept_config.py

# Step 2: Analyze with LLM
python reddit_llm_analyzer.py --config my_concept_config.py

# Step 3: Generate final report
python synthesize_llm_findings.py --config my_concept_config.py
```

**Option B: Run the complete pipeline**
```bash
python run_analysis.py --config my_concept_config.py
```

### Step 3: Review Results

All outputs are saved in the `results/` directory with your concept name as prefix:
- `{concept_name}_reddit_threads.json` - Raw Reddit data
- `{concept_name}_final_analysis_results.json` - LLM analysis results
- `{concept_name}_thematic_summary.json` - Thematic clustering of insights
- `{concept_name}_market_validation_report.md` - Final markdown report

## Configuration File Structure

Each concept configuration file should include:

### Required Sections

1. **Concept Definition**
   ```python
   CONCEPT_NAME = "unique_identifier"
   CONCEPT_DESCRIPTION = "Brief description"
   ```

2. **Reddit Data Collection**
   ```python
   TARGET_SUBREDDITS = ['list', 'of', 'relevant', 'subreddits']
   KEYWORDS = ['search', 'terms', 'for', 'your', 'concept']
   ```

3. **Analysis Configuration**
   ```python
   FILTER_SYSTEM_PROMPT = "LLM prompt for filtering relevant threads"
   FILTER_USER_PROMPT_TEMPLATE = "Template for filtering {thread_content}"
   ANALYSIS_SYSTEM_PROMPT = "LLM prompt for analyzing threads"
   ANALYSIS_USER_PROMPT_TEMPLATE = "Template for analysis {thread_context}"
   ```

4. **Synthesis Configuration**
   ```python
   ANALYSIS_CATEGORIES = {
       'category1': {'name': 'Display Name', 'description': 'category description'},
       # ... more categories
   }
   REPORT_SYSTEM_PROMPT = "LLM prompt for report generation"
   REPORT_USER_PROMPT_TEMPLATE = "Template for report {full_context}"
   ```

5. **File Naming**
   ```python
   OUTPUT_FILE_PREFIX = CONCEPT_NAME
   ```

## Example Concepts

The repository includes example configurations:

- **`concept_config.py`** - Tech education platform for seniors
- **`example_finance_config.py`** - AI-powered personal finance advisor

## Customization Tips

### Choosing Subreddits
- Look for communities where your target users discuss problems
- Include both problem-focused and solution-focused subreddits
- Consider niche communities and broader general-interest subs

### Selecting Keywords
- Include problem keywords ("help with X", "struggling with Y")
- Include solution keywords ("tool for X", "app for Y")
- Use domain-specific terminology your users would use
- Include variations and synonyms

### Tailoring LLM Prompts
- **Filter prompts**: Be specific about what makes a thread relevant to your concept
- **Analysis prompts**: Define the exact insights you want to extract
- **Report prompts**: Specify the structure and focus for your final report

### Analysis Categories
Customize the `ANALYSIS_CATEGORIES` to match the insights most relevant to your product:
- Pain points, challenges, frustrations
- Existing solutions and their limitations
- Unmet needs and wishes
- Specific tools/technologies mentioned
- Market segments or user types
- Pricing sensitivities

## Cost Considerations

The LLM analysis can incur costs based on:
- Number of threads analyzed (typically 100-500 relevant threads)
- Length of threads (posts + comments)
- Model choices (cheaper models for filtering, premium for analysis)

Estimated costs for a typical analysis: $5-20 depending on data volume and model selection.

## Troubleshooting

**Common Issues:**

1. **No threads found**: Check your subreddit names and keywords
2. **API rate limits**: The scripts include delays, but you may need to adjust them
3. **High costs**: Reduce `POST_LIMIT_PER_QUERY` or use cheaper models
4. **Poor analysis quality**: Refine your LLM prompts for better results

**Getting Help:**
- Check the console output for error messages
- Verify your API keys are correct
- Ensure your config file follows the required structure

## Contributing

To add new features or example configurations:
1. Keep concept-specific logic in config files
2. Maintain backwards compatibility with existing configs
3. Add examples and documentation for new features
