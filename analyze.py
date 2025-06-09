from dotenv import load_dotenv
import os
import praw
import json
import re
from praw.models import Comment

class Analyzer:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit client."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def markdown_to_plain_text(self, text):
        """Convert markdown text to plain text."""
        if not text or text.strip() == "":
            return text

        # First, handle Reddit-specific markdown
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

    # Fetch posts by search query within a subreddit
    def fetch_posts_by_search(self, subreddit_name, query, limit=500):
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        print(f"Searching '{query}' in r/{subreddit_name}...")
        for submission in subreddit.search(query, limit=limit):
            posts.append({
                'id': submission.id,
                'title': self.markdown_to_plain_text(submission.title),
                'selftext': self.markdown_to_plain_text(submission.selftext),
                'url': submission.url,
                'subreddit': subreddit_name,
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'permalink': f"https://reddit.com{submission.permalink}"
            })
        print(f"Found {len(posts)} posts for '{query}' in r/{subreddit_name}")

        return posts

    # Fetch top posts from a subreddit
    def fetch_top_posts(self, subreddit_name, time_filter='year', limit=100):
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        print(f"Fetching top posts from r/{subreddit_name} ({time_filter})...")
        for submission in subreddit.top(time_filter=time_filter, limit=limit):
            posts.append({
                'id': submission.id,
                'title': self.markdown_to_plain_text(submission.title),
                'selftext': self.markdown_to_plain_text(submission.selftext),
                'url': submission.url,
                'subreddit': subreddit_name,
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'permalink': f"https://reddit.com{submission.permalink}"
            })
        print(f"Found {len(posts)} top posts in r/{subreddit_name}")
        return posts

    def fetch_relevant_posts_from_subreddits(self, target_subreddits, keywords, limit=200):
        all_relevant_posts = []
        for sub in target_subreddits:
            for keyword in keywords:
                all_relevant_posts.extend(self.fetch_posts_by_search(sub, keyword, limit=limit)) # Limit per keyword per sub

        # Remove duplicates
        unique_posts = {post['id']: post for post in all_relevant_posts}.values()

        return list(unique_posts)

    def fetch_top_posts_from_subreddits(self, target_subreddits, time_filters=['all', 'year'], limit=100):
        all_top_posts = []
        for sub in target_subreddits:
            for time_filter in time_filters:
                all_top_posts.extend(self.fetch_top_posts(sub, time_filter=time_filter, limit=limit))

        # Remove duplicates
        unique_posts = {post['id']: post for post in all_top_posts}.values()

        return list(unique_posts)

    # Function to fetch comments for a given submission
    def fetch_comments_for_submission(self, submission_id, limit=5):
        submission = self.reddit.submission(id=submission_id)
        submission.comments.replace_more(limit=limit) # Expand 'More Comments'
        comments_data = []
        for comment in submission.comments.list():
            if isinstance(comment, Comment): # Ensure it's a valid comment object
                comments_data.append({
                    'id': comment.id,
                    'body': self.markdown_to_plain_text(comment.body),
                    'author': "anonymous",
                    # 'author': str(comment.author), # Convert Redditor object to string
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'permalink': f"https://reddit.com{comment.permalink}"
                })
        return comments_data

def main():
    load_dotenv()

    analyzer = Analyzer(
        client_id=str(os.getenv("REDDIT_CLIENT_ID")),
        client_secret=str(os.getenv("REDDIT_CLIENT_SECRET")),
        user_agent=str(os.getenv("REDDIT_USER_AGENT"))
    )

    all_relevant_posts = []

    # Fetch posts related to tech help for elderly parents
    relevant_posts_target_subreddits = ['AgingParents', 'Caregivers', 'CaregiverSupport', 'TechSupport']
    keywords = ['tech help', 'computer problems', 'internet safety', 'scam', 'digital literacy', 'teaching parents', 'grandparents tech', 'elderly tech']
    relevant_posts = analyzer.fetch_relevant_posts_from_subreddits(relevant_posts_target_subreddits, keywords, limit=200)
    all_relevant_posts.extend(relevant_posts)

    # Fetch top posts from specific subreddits related to elderly care
    top_post_target_subreddits = ['AgingParents', 'Caregivers', 'CaregiverSupport']
    top_posts = analyzer.fetch_top_posts_from_subreddits(top_post_target_subreddits, limit=100)
    all_relevant_posts.extend(top_posts)

    unique_posts = {post['id']: post for post in all_relevant_posts}.values()

    print(f"Total unique posts: {len(unique_posts)}")

    all_comments = []

    # Prioritize posts with high engagement (num_comments).
    sorted_posts = sorted(unique_posts, key=lambda x: x['num_comments'], reverse=True)
    top_n_posts_for_comments = list(sorted_posts)[:500] # Adjust N based on your needs and API limits

    for i, post in enumerate(top_n_posts_for_comments):
        print(f"Fetching comments for post {i+1}/{len(top_n_posts_for_comments)}: {post['title']}")
        try:
            all_comments.extend(analyzer.fetch_comments_for_submission(post['id'], limit=5))
        except Exception as e:
            print(f"Error fetching comments for {post['id']}: {e}")
        # time.sleep(1)

    print(f"Total comments fetched: {len(all_comments)}")

    # Save posts
    with open('reddit_posts.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_posts), f, ensure_ascii=False, indent=4)
    print("Posts saved to reddit_posts.json")

    # Save comments
    with open('reddit_comments.json', 'w', encoding='utf-8') as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=4)
    print("Comments saved to reddit_comments.json")

if __name__ == "__main__":
    main()
