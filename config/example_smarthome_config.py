# Configuration file for market research concepts
# Example configuration: Smart home automation platform for busy families

# === CONCEPT DEFINITION ===
CONCEPT_NAME = "family_smart_home"
CONCEPT_DESCRIPTION = "Smart home automation platform designed specifically for busy families with children"

# === REDDIT DATA COLLECTION ===
TARGET_SUBREDDITS = [
    "homeautomation",
    "smarthome",
    "Parenting",
    "workingmoms",
    "daddit",
    "HomeImprovement",
    "amazonecho",
    "googlehome",
]

KEYWORDS = [
    "smart home kids",
    "home automation family",
    "smart lights children",
    "family routines",
    "morning routine automation",
    "bedtime routine",
    "chore automation",
    "family schedule",
    "busy parents",
    "working parents",
    "smart home security kids",
    "child safety automation",
    "parental controls",
    "family organization",
    "smart home overwhelmed",
    "home automation complex",
]

# === ANALYSIS CONFIGURATION ===
# Filter prompt to determine if threads are relevant to the concept
FILTER_SYSTEM_PROMPT = """You are a highly efficient text classifier. Your task is to determine if a Reddit thread is relevant to smart home automation for families, parenting challenges that could be solved by automation, or family organization and routine management. Answer with only 'yes' or 'no'."""

FILTER_USER_PROMPT_TEMPLATE = """Is the following Reddit thread relevant to smart home automation for families, parenting challenges, family routines, or home organization that could benefit from automation?

---
{thread_content}
---"""

# Analysis prompt for extracting insights from relevant threads
ANALYSIS_SYSTEM_PROMPT = """You are a market research analyst. Your goal is to extract structured insights from a Reddit thread about family life, parenting challenges, and home automation needs. Provide your analysis in a structured JSON format."""

ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze the following Reddit thread (post and comments). Based on the entire context, provide a JSON object with the following keys:
- "main_pain_points": A list of strings, each describing a core family organization, routine, or home management frustration.
- "helper_challenges": A list of strings, each describing challenges faced by people trying to help families with organization or tech setup.
- "emotional_tone": A string describing the overall emotional sentiment (e.g., "Overwhelmed and stressed", "Seeking solutions").
- "mentioned_solutions": A list of strings for any current home automation tools, apps, or strategies mentioned, including their perceived flaws.
- "unmet_needs": A list of strings describing what families seem to be missing or wishing for in home automation solutions.
- "key_tech_topics": A list of specific technologies, devices, or services mentioned (e.g., "Alexa", "Google Home", "Smart thermostats", "Security cameras").
- "is_high_value": A boolean (true/false) indicating if this thread contains a rich, detailed discussion highly relevant to building a family-focused smart home platform.

Here is the thread:
---
{thread_context}
---
"""

# === SYNTHESIS CONFIGURATION ===
# Categories for thematic analysis
ANALYSIS_CATEGORIES = {
    "main_pain_points": {
        "name": "Family Organization Pain Points",
        "description": "family organization, routine, and home management frustrations",
    },
    "helper_challenges": {
        "name": "Helper Challenges",
        "description": "challenges for people helping families with organization or tech",
    },
    "unmet_needs": {
        "name": "Unmet Family Automation Needs",
        "description": "features or automation solutions families wish they had",
    },
    "key_tech_topics": {
        "name": "Smart Home Technology Topics",
        "description": "specific smart home devices and technologies mentioned",
    },
}

# Report generation prompt
REPORT_SYSTEM_PROMPT = """You are a senior market research analyst and strategist. Your task is to write a comprehensive, yet concise, market validation report for a new smart home automation platform designed specifically for busy families with children. Use the provided thematic data to structure your report."""

REPORT_USER_PROMPT_TEMPLATE = """
Based on the following thematic analysis of Reddit discussions, write a market validation report in Markdown format. The report should have the following sections:

1.  **Executive Summary:** A high-level overview of the key findings. Is there a viable market need? What is the core family organization problem?
2.  **Key Family Pain Points:** Summarize the primary struggles of busy families that could be addressed by smart home automation. Use the 'main_pain_points' data.
3.  **Challenges for Family Tech Helpers:** Detail the frustrations and challenges faced by those trying to help families organize or set up smart home technology. Use the 'helper_challenges' data.
4.  **Market Opportunity & Unmet Needs:** Analyze the gap in the market. What automation solutions are families missing? Use the 'unmet_needs' and 'mentioned_solutions' data to highlight why current solutions are failing for families.
5.  **Critical Smart Home Technology Areas:** List the most important smart home technologies that the platform must integrate to be successful for families. Use the 'key_tech_topics' data.
6.  **Strategic Recommendations:** Based on all the data, provide 2-3 actionable recommendations for the product team building this family-focused smart home platform. What should they focus on first? What features are most critical for busy parents?

Be insightful and base your conclusions directly on the data provided below.

**DATA:**
---
{full_context}
---
"""

# === FILE NAMING ===
OUTPUT_FILE_PREFIX = CONCEPT_NAME
