"""Application settings management for Reddit Market Research Framework."""

import os
from dotenv import load_dotenv


class Settings:
    """Manages application settings from environment variables."""

    def __init__(self):
        """Initialize settings from environment variables."""
        load_dotenv()

        # Reddit API settings
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

        # OpenRouter API settings
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"

        # Model configurations
        self.filter_model = os.getenv("ANALYSIS_FILTER_MODEL", "mistralai/mistral-nemo")
        self.analysis_model = os.getenv("ANALYSIS_MODEL", "gpt-4o-mini")
        self.synthesis_model = os.getenv("SYNTHESIS_MODEL", "gpt-4o-mini")

        # Reddit fetching limits
        self.post_limit_per_query = int(os.getenv("POST_LIMIT_PER_QUERY", "150"))
        self.comment_limit_per_post = int(os.getenv("COMMENT_LIMIT_PER_POST", "50"))
        self.max_replies_per_comment = int(os.getenv("MAX_REPLIES_PER_COMMENT", "10"))
        self.reply_fetch_depth = int(os.getenv("REPLY_FETCH_DEPTH", "1"))

        # Analysis limits
        self.max_comments_per_post = int(os.getenv("MAX_COMMENTS_PER_POST", "30"))
        self.max_tokens_for_analysis = int(os.getenv("MAX_TOKENS_FOR_ANALYSIS", "16000"))

        # API settings
        self.api_timeout = int(os.getenv("API_TIMEOUT", "180"))
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "0.5"))
        self.progress_save_interval = int(os.getenv("PROGRESS_SAVE_INTERVAL", "5"))

        # Reddit request settings
        self.reddit_request_delay = float(os.getenv("REDDIT_REQUEST_DELAY", "0.25"))
        self.reddit_more_comments_limit = int(os.getenv("REDDIT_MORE_COMMENTS_LIMIT", "10"))

    def validate_required_settings(self) -> bool:
        """Validate that all required settings are present."""
        required_settings = [
            ('OPENROUTER_API_KEY', self.openrouter_api_key),
            ('REDDIT_CLIENT_ID', self.reddit_client_id),
            ('REDDIT_CLIENT_SECRET', self.reddit_client_secret),
            ('REDDIT_USER_AGENT', self.reddit_user_agent),
        ]

        missing = []
        for name, value in required_settings:
            if not value:
                missing.append(name)

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True
