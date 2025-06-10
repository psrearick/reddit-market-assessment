# Configuration file for market research concepts
# This file contains all concept-specific elements that can be modified for different product ideas

# === CONCEPT DEFINITION ===
CONCEPT_NAME = "tech_education_platform"
CONCEPT_DESCRIPTION = "Online learning platform for tech-savvy individuals to teach technology to non-tech-savvy loved ones"

# === REDDIT DATA COLLECTION ===
TARGET_SUBREDDITS = [
    'AgingParents',
    'Caregivers',
    'CaregiverSupport',
    'TechSupport'
]

KEYWORDS = [
    'tech help', 'computer problems', 'internet safety', 'scam',
    'digital literacy', 'teaching parents', 'grandparents tech',
    'elderly tech', 'zoom help', 'phishing', 'online security',
    'social media safety', 'digital skills', 'senior tech',
    'elderly computer'
]

# === ANALYSIS CONFIGURATION ===
# Filter prompt to determine if threads are relevant to the concept
FILTER_SYSTEM_PROMPT = """You are a highly efficient text classifier. Your task is to determine if a Reddit thread is relevant to the topic of teaching technology to non-tech-savvy individuals (like seniors) or the challenges faced by them or their helpers. Answer with only 'yes' or 'no'."""

FILTER_USER_PROMPT_TEMPLATE = """Is the following Reddit thread relevant to the topic of tech challenges for seniors, digital literacy for beginners, or people helping them with technology?

---
{thread_content}
---"""

# Analysis prompt for extracting insights from relevant threads
ANALYSIS_SYSTEM_PROMPT = """You are a market research analyst. Your goal is to extract structured insights from a Reddit thread about technology challenges for non-tech-savvy individuals. Provide your analysis in a structured JSON format."""

ANALYSIS_USER_PROMPT_TEMPLATE = """
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

# === SYNTHESIS CONFIGURATION ===
# Categories for thematic analysis
ANALYSIS_CATEGORIES = {
    'main_pain_points': {
        'name': "Learner Pain Points",
        'description': "pain points for non-tech-savvy individuals"
    },
    'helper_challenges': {
        'name': "Helper Challenges",
        'description': "challenges for people teaching tech"
    },
    'unmet_needs': {
        'name': "Unmet Needs",
        'description': "features or solutions users wish they had"
    },
    'key_tech_topics': {
        'name': "Key Technology Topics",
        'description': "specific technologies causing issues"
    }
}

# Report generation prompt
REPORT_SYSTEM_PROMPT = """You are a senior market research analyst and strategist. Your task is to write a comprehensive, yet concise, market validation report for a new online learning platform. The platform aims to help tech-savvy individuals teach technology to non-tech-savvy loved ones. Use the provided thematic data to structure your report."""

REPORT_USER_PROMPT_TEMPLATE = """
Based on the following thematic analysis of Reddit discussions, write a market validation report in Markdown format. The report should have the following sections:

1.  **Executive Summary:** A high-level overview of the key findings. Is there a viable market need? What is the core problem?
2.  **Key Pain Points for Learners (Non-Tech-Savvy Individuals):** Summarize the primary struggles of the end-users. Use the 'main_pain_points' data.
3.  **Key Challenges for 'Teachers' (Tech-Savvy Helpers):** Detail the frustrations and challenges faced by those trying to provide tech support. Use the 'helper_challenges' data.
4.  **Market Opportunity & Unmet Needs:** Analyze the gap in the market. What are people missing? What do they wish for? Use the 'unmet_needs' and 'mentioned_solutions' data to highlight why current solutions are failing.
5.  **Critical Technology Topics:** List the most pressing technology areas that the platform must cover to be successful. Use the 'key_tech_topics' data.
6.  **Strategic Recommendations:** Based on all the data, provide 2-3 actionable recommendations for the product team building this platform. What should they focus on first? What features are most critical?

Be insightful and base your conclusions directly on the data provided below.

**DATA:**
---
{full_context}
---
"""

# === FILE NAMING ===
OUTPUT_FILE_PREFIX = CONCEPT_NAME
