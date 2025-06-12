# Reddit Market Research Framework

A flexible framework for conducting market research by analyzing Reddit discussions for different product concepts.

## Quick Start

1. **Install dependencies**: `pip install praw python-dotenv requests`
2. **Set up API keys**: Create a `.env` file with Reddit and OpenRouter credentials
3. **Test the framework**: `python demo.py` to see examples
4. **Run analysis**: `python run_analysis.py --config config/example_finance_config.py`

## Overview

This framework allows you to analyze Reddit discussions to validate market opportunities for various product concepts. The system is designed to be concept-agnostic - you simply create a configuration file for your specific product idea, and the same scripts will collect, analyze, and synthesize data tailored to your concept.

## Architecture

The framework consists of modular components organized into classes and utilities:

### Core Components

1. **`RedditFetcher`** - Collects Reddit posts and comments based on your concept configuration
2. **`ThreadAnalyzer`** - Uses LLM to filter and analyze threads for market insights
3. **`ReportSynthesizer`** - Generates thematic summaries and final market validation report

### Main Scripts

- **`run_analysis.py`** - Main pipeline runner that orchestrates the entire analysis process
- **`demo.py`** - Demonstration script showing framework capabilities and usage examples
- **`test_config.py`** - Configuration validator to ensure config files are properly structured

### Utilities Module (`utils/`)

- **`ConfigManager`** - Handles loading and validation of concept configuration files
- **`LLMClient`** - Manages API calls to OpenRouter for LLM analysis
- **`FileManager`** - Handles all file I/O operations (JSON, text, markdown)
- **`TextProcessor`** - Text processing utilities including token estimation
- **`Settings`** - Environment variable management and application settings

All concept-specific elements (subreddits, keywords, analysis prompts) are externalized into configuration files in the `config/` directory.

## Setup

### Prerequisites

1. **Python 3.8+** (tested with Python 3.11-3.12)
2. **Required packages**:
   ```bash
   pip install praw python-dotenv requests
   ```
3. **API Access**:
   - Reddit API credentials (free)
   - OpenRouter API key (paid, ~$5-20 per analysis)

### API Keys

Create a `.env` file in the project root with:

```env
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

# OpenRouter API key for LLM analysis
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional: Model configurations (defaults shown)
FILTER_MODEL=mistralai/mistral-nemo
ANALYSIS_MODEL=gpt-4o-mini
SYNTHESIS_MODEL=gpt-4o-mini

# Optional: Reddit fetching limits (defaults shown)
POST_LIMIT_PER_QUERY=150
COMMENT_LIMIT_PER_POST=50
MAX_REPLIES_PER_COMMENT=10
REPLY_FETCH_DEPTH=1
TOP_POSTS_COUNT=100

# Optional: Analysis limits (defaults shown)
MAX_TOKENS_FOR_ANALYSIS=16000
RATE_LIMIT_DELAY=0.5
API_TIMEOUT=180
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

Create a configuration file for your product concept in the `config/` directory (see `config/example_finance_config.py` for an example):

```python
# config/my_concept_config.py
CONCEPT_NAME = "my_product_idea"
CONCEPT_DESCRIPTION = "Description of your product concept"

TARGET_SUBREDDITS = ['relevant', 'subreddits', 'for_your_concept']
KEYWORDS = ['keyword1', 'keyword2', 'etc']

# ... (see existing config files for full structure)
```

### Step 2: Run the Analysis Pipeline

The framework provides a single main runner script that handles the complete pipeline:

**Run the complete pipeline:**
```bash
python run_analysis.py --config config/my_concept_config.py
```

**Run specific steps:**
```bash
# Run only analysis and synthesis (skip data collection)
python run_analysis.py --config config/my_concept_config.py --skip-fetch

# Run only specific steps
python run_analysis.py --config config/my_concept_config.py --steps analyze,synthesize
```

**Pipeline Steps:**
1. **Fetch** - Collects Reddit data from configured subreddits using keyword searches and top posts
2. **Analyze** - Uses LLM to filter relevant threads and extract structured insights
3. **Synthesize** - Performs thematic analysis and generates final market validation report

**Additional Examples:**
```bash
# Get help on all available options
python run_analysis.py --help

# Run with different configuration
python run_analysis.py --config config/example_smarthome_config.py

# Skip data fetching if you already have results
python run_analysis.py --config config/my_config.py --skip-fetch

# Run only the synthesis step
python run_analysis.py --config config/my_config.py --steps synthesize
```

### Step 3: Review Results

All outputs are saved in the `results/` directory with your concept name as prefix:

- **`{concept_name}_reddit_threads.json`** - Raw Reddit data (posts and comments)
- **`{concept_name}_final_analysis_results.json`** - LLM analysis results with structured insights
- **`{concept_name}_filtered_out_threads.json`** - Threads that were filtered out as irrelevant
- **`{concept_name}_thematic_summary.json`** - Thematic clustering of insights by category
- **`{concept_name}_market_validation_report.md`** - Final markdown report with actionable insights

**Understanding the Output:**

- The **raw threads** file contains all collected Reddit data for reference
- The **analysis results** contain structured insights extracted by the LLM
- The **thematic summary** groups similar insights into themes with counts
- The **market validation report** is your final deliverable with strategic recommendations

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

The repository includes example configurations in the `config/` directory:

- **`config/example_smarthome_config.py`** - Smart home automation platform for busy families
- **`config/example_finance_config.py`** - AI-powered personal finance advisor

You can test these configurations or use them as templates for your own concepts.

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

## Project Structure

```
reddit-assessment/
├── run_analysis.py          # Main pipeline runner
├── demo.py                  # Framework demonstration and examples
├── test_config.py           # Configuration validator
├── reddit_fetcher.py        # Reddit data collection class
├── thread_analyzer.py       # LLM analysis class
├── report_synthesizer.py    # Report generation class
├── config/                  # Configuration files
│   ├── example_finance_config.py
│   └── example_smarthome_config.py
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── config_manager.py    # Configuration loading and validation
│   ├── settings.py          # Environment variable management
│   ├── llm_client.py        # OpenRouter API client
│   ├── file_manager.py      # File I/O operations
│   └── text_processor.py    # Text processing utilities
├── results/                 # Output directory for analysis results
├── .env                     # Environment variables (create this)
└── README.md               # This file
```

## Cost Considerations

The LLM analysis can incur costs based on:
- Number of threads analyzed (typically 100-500 relevant threads)
- Length of threads (posts + comments)
- Model choices (cheaper models for filtering, premium for analysis)
- Configuration settings (POST_LIMIT_PER_QUERY, COMMENT_LIMIT_PER_POST, etc.)

Estimated costs for a typical analysis: $5-20 depending on data volume and model selection.

You can control costs by:
- Adjusting `POST_LIMIT_PER_QUERY` and `COMMENT_LIMIT_PER_POST` in your .env file
- Using cheaper models like `mistralai/mistral-nemo` for filtering
- Limiting the number of subreddits and keywords in your config

## Troubleshooting

**Common Issues:**

1. **Configuration errors**: Run `python test_config.py` to validate your configuration files
2. **No threads found**: Check your subreddit names and keywords in your config
3. **API rate limits**: The framework includes automatic delays, but you may need to adjust `RATE_LIMIT_DELAY` in your .env file
4. **High costs**: Reduce `POST_LIMIT_PER_QUERY` in your .env file or use cheaper models
5. **Poor analysis quality**: Refine your LLM prompts in your configuration file
6. **Missing dependencies**: Run `pip install praw python-dotenv requests` to install required packages

**Getting Help:**
- Check the console output for detailed error messages
- Verify your API keys are correct in the `.env` file
- Ensure your config file follows the required structure (use `test_config.py`)
- Review the `demo.py` script for usage examples

## Testing and Development

### Validate Configuration Files

Before running analysis, validate your configuration:

```bash
# Test all configurations in config/ directory
python test_config.py

# Test a specific configuration
python test_config.py config/my_concept_config.py
```

### Demo and Examples

Explore the framework capabilities:

```bash
# Show framework overview and examples
python demo.py

# Show project structure
python demo.py --structure
```

### Development Tips

1. **Start Small**: Begin with a limited number of subreddits and keywords to test your configuration
2. **Iterate on Prompts**: Use the example configs as templates and refine your LLM prompts based on results
3. **Monitor Costs**: Check your OpenRouter usage regularly, especially when testing new configurations
4. **Use Skip Options**: Use `--skip-fetch` to test analysis and synthesis steps without re-collecting data

## Contributing

To add new features or example configurations:

1. **Keep concept-specific logic in config files** - The core framework should remain concept-agnostic
2. **Maintain backwards compatibility** with existing configs and utilities
3. **Add proper validation** - Update `config_manager.py` if adding new required config fields
4. **Test thoroughly** - Use `test_config.py` to validate any new configuration examples
5. **Document examples** - Add new concepts to the `config/` directory with clear documentation
6. **Follow the modular architecture** - New functionality should be added to appropriate utility classes

### Adding New Analysis Categories

To add new analysis categories:
1. Update your config file's `ANALYSIS_CATEGORIES` section
2. Modify the `ANALYSIS_USER_PROMPT_TEMPLATE` to extract the new data
3. Update the `REPORT_USER_PROMPT_TEMPLATE` to include the new insights in reports
