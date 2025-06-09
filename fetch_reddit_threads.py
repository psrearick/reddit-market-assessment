from dotenv import load_dotenv
import os
import praw
import json
import re
import time
from praw.models import Comment


TARGET_SUBREDDITS = ['AgingParents', 'Caregivers', 'CaregiverSupport', 'TechSupport']
KEYWORDS = ['tech help', 'computer problems', 'internet safety', 'scam',
            'digital literacy', 'teaching parents', 'grandparents tech',
            'elderly tech', 'zoom help', 'phishing', 'online security',
            'social media safety', 'digital skills', 'senior tech',
            'elderly computer']
POST_LIMIT_PER_QUERY = 150  # Number of posts to fetch for each keyword in each subreddit
COMMENT_LIMIT_PER_POST = 50 # Max number of comments to fetch for each post
MAX_REPLIES_PER_COMMENT = 10 # Max replies to fetch for each top-level comment
REPLY_FETCH_DEPTH = 1 # How many levels of replies to fetch (1 = top-level + their direct replies)
OUTPUT_FILE = 'reddit_threads.json'

def markdown_to_plain_text(text):
    """Convert markdown text to plain text."""
    if not text or text.strip() == "":
        return text

    # Remove Reddit quotes (lines starting with >)
    text = re.sub(r'^&gt;.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)

    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove markdown emphasis
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
    text = re.sub(r'`(.*?)`', r'\1', text)        # Inline code

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'    .*$', '', text, flags=re.MULTILINE)  # Indented code

    # Remove headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

    # Remove bullet points and numbering
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple empty lines to double
    text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces/tabs to single space
    text = text.strip()

    return text

class Fetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit client."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        self.all_threads = {}

    def fetch_replies(self, comment: Comment, current_depth):
        """Recursively fetches replies up to a certain depth."""
        if current_depth >= REPLY_FETCH_DEPTH:
            return []

        replies_data = []
        # Ensure comment.replies is loaded

        comment.replies.replace_more(limit=0) # Expand only the first level of "more"
        sorted_replies = sorted(comment.replies.list(), key=lambda r: r.score if isinstance(r, Comment) else 0, reverse=True)

        for reply in sorted_replies[:MAX_REPLIES_PER_COMMENT]:
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

    def process_submission(self, submission, sub_name):
        """
        Processes a single submission, fetching its comments and replies.
        """
        # Skip if we've already processed this post from a different keyword search
        if submission.id in self.all_threads:
            return

        comments_data = []

        try:
            submission.comments.replace_more(limit=10) # Expand "more comments" links, limit to 10 expansions to avoid long waits

            # Sort comments by score (upvotes) to get the most relevant ones
            sorted_comments = sorted(submission.comments.list(), key=lambda c: c.score if isinstance(c, Comment) else 0, reverse=True)

            for comment in sorted_comments[:COMMENT_LIMIT_PER_POST]:
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

    def fetch_reddit_threads_for_keywords(self, target_subreddits=TARGET_SUBREDDITS, keywords=KEYWORDS):
        """
        Fetches posts based on keywords and then fetches their top comments
        """
        for sub_name in target_subreddits:
            subreddit = self.reddit.subreddit(sub_name)
            for keyword in keywords:
                print(f"\nSearching for '{keyword}' in r/{sub_name}...")
                try:
                    for submission in subreddit.search(keyword, limit=POST_LIMIT_PER_QUERY):
                        self.process_submission(submission, sub_name)
                        time.sleep(0.5)
                except Exception as e:
                    print(f"    An error occurred while searching in r/{sub_name}: {e}")
                    time.sleep(5) # Wait a bit if there's a broader issue

    def fetch_top_threads(self, target_subreddits=TARGET_SUBREDDITS, time_filters=['all', 'year'], limit=100):
        """
        Fetches top posts from subreddits based on the time filter.
        """
        for subreddit_name in target_subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for time_filter in time_filters:
                print(f"Fetching top posts from r/{subreddit_name} ({time_filter})...")
                try:
                    for submission in subreddit.top(time_filter=time_filter, limit=limit):
                        self.process_submission(submission, subreddit_name)
                        time.sleep(0.5)
                except Exception as e:
                    print(f"    An error occurred while fetching top posts from r/{subreddit_name}: {e}")
                    time.sleep(5)

def main():
    load_dotenv()

    fetcher = Fetcher(
        client_id=str(os.getenv("REDDIT_CLIENT_ID")),
        client_secret=str(os.getenv("REDDIT_CLIENT_SECRET")),
        user_agent=str(os.getenv("REDDIT_USER_AGENT"))
    )

    fetcher.fetch_reddit_threads_for_keywords()
    fetcher.fetch_top_threads()

    print(f"Total unique posts: {len(fetcher.all_threads)}")

    threads_list = list(fetcher.all_threads.values())

    # Save the final combined data to a single JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(threads_list, f, ensure_ascii=False, indent=4)

    print(f"Successfully saved all threads and their comments to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
