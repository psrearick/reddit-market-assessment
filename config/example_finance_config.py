# Configuration file for market research concepts
# Example configuration for a different product concept: AI-powered personal finance advisor

# === CONCEPT DEFINITION ===
CONCEPT_NAME = "ai_finance_advisor"
CONCEPT_DESCRIPTION = (
    "AI-powered personal finance advisor app for millennials and Gen Z users"
)

# === REDDIT DATA COLLECTION ===
TARGET_SUBREDDITS = [
    "personalfinance",
    "financialindependence",
    "budgets",
    "millennials",
    "povertyfinance",
    "investing",
    "StudentLoans",
]

KEYWORDS = [
    "budgeting app",
    "financial planning",
    "money management",
    "debt tracking",
    "investment advice",
    "savings goals",
    "financial literacy",
    "expense tracking",
    "credit score",
    "financial anxiety",
    "money stress",
    "financial advisor",
    "budget help",
    "financial app",
    "money app",
    "personal finance",
]

# === ANALYSIS CONFIGURATION ===
# Filter prompt to determine if threads are relevant to the concept
FILTER_SYSTEM_PROMPT = """You are a highly efficient text classifier. Your task is to determine if a Reddit thread is relevant to personal finance management, budgeting challenges, or the need for financial planning tools and advice. Answer with only 'yes' or 'no'."""

FILTER_USER_PROMPT_TEMPLATE = """Is the following Reddit thread relevant to personal finance management, budgeting difficulties, investment concerns, or people seeking financial planning tools and advice?

---
{thread_content}
---"""

# Analysis prompt for extracting insights from relevant threads
ANALYSIS_SYSTEM_PROMPT = """You are a market research analyst. Your goal is to extract structured insights from a Reddit thread about personal finance challenges and needs. Provide your analysis in a structured JSON format."""

ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the following Reddit thread (post and comments). Based on the entire context, provide a JSON object with the following keys:
- "main_pain_points": A list of strings, each describing a core financial management frustration or challenge.
- "helper_challenges": A list of strings, each describing challenges faced by people trying to help others with finances (financial advisors, family members, etc.).
- "emotional_tone": A string describing the overall emotional sentiment (e.g., "Anxiety and stress", "Hopeful but overwhelmed").
- "mentioned_solutions": A list of strings for any current financial tools, apps, or strategies mentioned, including their perceived flaws.
- "unmet_needs": A list of strings describing what users seem to be missing or wishing for in financial management solutions.
- "key_tech_topics": A list of specific financial tools, apps, or services mentioned (e.g., "Mint", "YNAB", "Robinhood", "Credit monitoring").
- "is_high_value": A boolean (true/false) indicating if this thread contains a rich, detailed discussion highly relevant to building a personal finance app.

Here is the thread:
---
{thread_context}
---
"""

# === SYNTHESIS CONFIGURATION ===
# Categories for thematic analysis
ANALYSIS_CATEGORIES = {
    "main_pain_points": {
        "name": "Financial Pain Points",
        "description": "financial management frustrations and challenges",
    },
    "helper_challenges": {
        "name": "Advisor Challenges",
        "description": "challenges for people providing financial guidance",
    },
    "unmet_needs": {
        "name": "Unmet Financial Needs",
        "description": "features or financial services users wish they had",
    },
    "key_tech_topics": {
        "name": "Financial Technology Topics",
        "description": "specific financial tools and apps mentioned",
    },
}

# Report generation prompt
REPORT_SYSTEM_PROMPT = """You are a senior market research analyst and strategist. Your task is to write a comprehensive, yet concise, market validation report for a new AI-powered personal finance advisor app targeting millennials and Gen Z users. Use the provided thematic data to structure your report."""

REPORT_USER_PROMPT_TEMPLATE = """
Based on the following thematic analysis of Reddit discussions, write a market validation report in Markdown format. The report should have the following sections:

1.  **Executive Summary:** A high-level overview of the key findings. Is there a viable market need? What is the core financial problem?
2.  **Key Financial Pain Points:** Summarize the primary financial struggles of the target users. Use the 'main_pain_points' data.
3.  **Challenges for Financial Helpers:** Detail the frustrations and challenges faced by those trying to provide financial guidance. Use the 'helper_challenges' data.
4.  **Market Opportunity & Unmet Needs:** Analyze the gap in the market. What financial solutions are people missing? Use the 'unmet_needs' and 'mentioned_solutions' data to highlight why current solutions are failing.
5.  **Critical Financial Technology Areas:** List the most important financial technology areas that the app must address to be successful. Use the 'key_tech_topics' data.
6.  **Strategic Recommendations:** Based on all the data, provide 2-3 actionable recommendations for the product team building this financial app. What should they focus on first? What features are most critical?

Be insightful and base your conclusions directly on the data provided below.

**DATA:**
---
{full_context}
---
"""

# === FILE NAMING ===
OUTPUT_FILE_PREFIX = CONCEPT_NAME
