from datetime import datetime, timedelta
import os
from typing import List, Optional
from dotenv import load_dotenv
import praw
from praw.models import Comment as PrawComment
import pytz
from classifier import Classifier
from post import Post, Comment
from writing_tool_classifier import WritingToolClassifier

class Analyzer:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, classifier: Classifier) -> None:
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        self.classifier = classifier

    def get_recent_posts(self, days: int = 30) -> List[Post]:
        all_posts = []

        cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days)
        for subreddit_name in self.classifier.subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.new(limit=1000):
                if datetime.fromtimestamp(submission.created_utc, pytz.UTC) < cutoff_time:
                    break
                all_posts.append(Post(
                    id=submission.id,
                    title=submission.title,
                    text=submission.selftext,
                    url=submission.url,
                    date=datetime.fromtimestamp(submission.created_utc, pytz.UTC),
                    name=submission.name,
                    subreddit=subreddit_name,
                    score=submission.score,
                    submission=submission
                ))

        return all_posts

    def classify(self, post: Post):
        return self.classifier.is_post_valid(post)

    def format_comment(self, comment: PrawComment, depth=0) -> Comment:
        """Format a single comment and its replies."""

        comment_data = Comment(
            id = comment.id,
            author = str(comment.author) if comment.author else "[deleted]",
            content = comment.body,
            timestamp = datetime.fromtimestamp(comment.created_utc, pytz.UTC).isoformat(),
            score = comment.score,
            depth = depth,
        )

        for reply in comment.replies:
            if not isinstance(reply, Comment):
                continue

            formatted_reply = self.format_comment(reply, depth + 1)
            if formatted_reply:
                comment_data.replies.append(formatted_reply)

        return comment_data

    def format_post(self, post: Post) -> Optional[Post]:
        try:
            post.submission.comments.replace_more(limit=None)
            for comment in post.submission.comments:
                formatted_comment = self.format_comment(comment)
                if formatted_comment:
                    post.comments.append(formatted_comment)
            return post
        except Exception as e:
            print(f"Error formatting submission {post.id}: {e}")
            return None

def main():
    load_dotenv()

    classifier = WritingToolClassifier()
    analyzer = Analyzer(
        client_id=str(os.environ.get("REDDIT_CLIENT_ID")),
        client_secret=str(os.environ.get("REDDIT_CLIENT_SECRET")),
        user_agent=str(os.environ.get("REDDIT_USER_AGENT")),
        classifier=classifier
    )

    posts = analyzer.get_recent_posts()
    valid_posts = [post for post in posts if analyzer.classify(post)]
    formatted_posts = [analyzer.format_post(post) for post in valid_posts]
    formatted_posts = [post for post in formatted_posts if post is not None]

if __name__ == "__main__":
    main()
