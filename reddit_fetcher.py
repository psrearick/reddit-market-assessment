"""Reddit data fetching for market research."""

import praw
import time
from praw.models import Comment, Submission
from utils import Settings, Config, FileManager, TextProcessor

class RedditFetcher:
    """Handles Reddit data fetching operations."""

    def __init__(self, config: Config, settings: Settings):
        """
        Initialize the Reddit fetcher.

        Args:
            config: Config instance
            settings: Settings instance
        """
        self.config = config
        self.settings = settings
        self.text_processor = TextProcessor()
        self.file_manager = FileManager()
        self.reddit = self._init_reddit_client()
        self.all_threads = {}

    def _init_reddit_client(self) -> praw.Reddit:
        """Initialize Reddit client with credentials."""
        return praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent
        )

    def fetch_replies(self, comment: Comment, current_depth: int = 0) -> list[dict]:
        """
        Recursively fetch replies up to a certain depth.

        Args:
            comment: Comment to fetch replies for
            current_depth: Current recursion depth

        Returns:
            List of reply data dictionaries
        """
        if current_depth >= self.settings.reply_fetch_depth:
            return []

        replies_data = []
        comment.replies.replace_more(limit=0)  # Expand only the first level of "more"
        sorted_replies = sorted(
            comment.replies.list(),
            key=lambda r: r.score if isinstance(r, Comment) else 0,
            reverse=True
        )

        for reply in sorted_replies[:self.settings.max_replies_per_comment]:
            if isinstance(reply, Comment):
                replies_data.append({
                    'id': reply.id,
                    'body': reply.body,
                    'author': str(reply.author),
                    'score': reply.score,
                    'created_utc': reply.created_utc,
                    'replies': self.fetch_replies(reply, current_depth + 1)
                })
        return replies_data

    def process_submission(self, submission : Submission, sub_name: str) -> None:
        """
        Process a single submission, fetching its comments and replies.

        Args:
            submission: Reddit submission object
            sub_name: Subreddit name
        """
        # Skip if we've already processed this post from a different keyword search
        if submission.id in self.all_threads:
            return

        comments_data = []

        try:
            submission.comments.replace_more(limit=self.settings.reddit_more_comments_limit)

            # Sort comments by score (upvotes) to get the most relevant ones
            sorted_comments = sorted(
                submission.comments.list(),
                key=lambda c: c.score if isinstance(c, Comment) else 0,
                reverse=True
            )

            for comment in sorted_comments[:self.settings.comment_limit_per_post]:
                if isinstance(comment, Comment):
                    comment_dict = {
                        'id': comment.id,
                        'body': comment.body,
                        'author': str(comment.author),
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'replies': self.fetch_replies(comment, current_depth=0)
                    }
                    comments_data.append(comment_dict)
        except Exception as e:
            print(f"      Error fetching comments for post {submission.id}: {e}")

        self.all_threads[submission.id] = {
            'id': submission.id,
            'title': submission.title,
            'selftext': submission.selftext,
            'url': submission.url,
            'subreddit': sub_name,
            'score': submission.score,
            'num_comments': submission.num_comments,
            'created_utc': submission.created_utc,
            'permalink': f"https://reddit.com{submission.permalink}",
            'comments': comments_data
        }

    def fetch_keyword_threads(self) -> None:
        """Fetch posts based on keywords from target subreddits."""
        for sub_name in self.config.target_subreddits:
            subreddit = self.reddit.subreddit(sub_name)
            for keyword in self.config.keywords:
                print(f"\nSearching for '{keyword}' in r/{sub_name}...")
                try:
                    for submission in subreddit.search(keyword, limit=self.settings.post_limit_per_query):
                        self.process_submission(submission, sub_name)
                        time.sleep(self.settings.reddit_request_delay)
                except Exception as e:
                    print(f"    An error occurred while searching in r/{sub_name}: {e}")
                    time.sleep(5)  # Wait a bit if there's a broader issue

    def fetch_top_threads(self, time_filters=['all', 'year']) -> None:
        """
        Fetch top posts from subreddits based on time filter.

        Args:
            time_filters: List of time filters to use
            limit: Number of posts to fetch per time filter
        """
        for subreddit_name in self.config.target_subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for time_filter in time_filters:
                print(f"Fetching top posts from r/{subreddit_name} ({time_filter})...")
                try:
                    for submission in subreddit.top(time_filter=time_filter, limit=self.settings.top_posts_count):
                        self.process_submission(submission, subreddit_name)
                        time.sleep(self.settings.reddit_request_delay)
                except Exception as e:
                    print(f"    An error occurred while fetching top posts from r/{subreddit_name}: {e}")
                    time.sleep(5)

    def fetch_all_data(self) -> list[dict]:
        """
        Main method to fetch all Reddit data.

        Returns:
            List of thread data dictionaries
        """
        print(f"Starting Reddit data collection for concept: {self.config.concept_name}")
        print(f"Description: {self.config.concept_description}")
        print(f"Target subreddits: {self.config.target_subreddits}")
        print(f"Keywords: {len(self.config.keywords)} keywords")

        self.fetch_keyword_threads()
        self.fetch_top_threads()

        print(f"Total unique posts: {len(self.all_threads)}")
        return list(self.all_threads.values())
