from datetime import datetime, timedelta
import json
import os
from typing import List, Optional
from dotenv import load_dotenv
import praw
from praw.models import Comment as PrawComment
import pytz
from concurrent.futures import ThreadPoolExecutor
from classifier import Classifier
from backup.post import Post, Comment
from writing_tool_classifier import WritingToolClassifier

class Analyzer:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, classifier: Classifier) -> None:
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            requestor_kwargs={"timeout": 30}
        )
        self.classifier = classifier

    def get_recent_posts(self, days: int = 30, max_workers: int = 5) -> List[Post]:
        all_posts = []
        cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days)

        def fetch_subreddit_posts(subreddit_name: str) -> List[Post]:
            subreddit_posts = []
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.new(limit=1000):
                if datetime.fromtimestamp(submission.created_utc, pytz.UTC) < cutoff_time:
                    break
                subreddit_posts.append(Post(
                    id=submission.id,
                    author=str(submission.author.name) if submission.author else "[deleted]",
                    title=submission.title,
                    content=submission.selftext,
                    url=submission.url,
                    date=datetime.fromtimestamp(submission.created_utc, pytz.UTC),
                    name=submission.name,
                    subreddit=subreddit_name,
                    score=submission.score,
                    submission=submission
                ))
            return subreddit_posts

        # Parallel fetch posts from different subreddits
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(fetch_subreddit_posts, self.classifier.subreddits)
            for subreddit_posts in results:
                all_posts.extend(subreddit_posts)

        return all_posts

    def classify_batch(self, posts: List[Post], batch_size: int = 10) -> List[bool]:
        results = []
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            # Create a combined prompt for the batch
            prompts = [
                f"Title: {post.title}\nContent: {post.content}"
                for post in batch
            ]
            combined_prompt = f"""Analyze these Reddit posts and determine if each is about {self.classifier.topic}.
            Consider both explicit mentions and implicit references to this topic.

            Posts:
            {'-' * 40}
            """ + "\n".join(f"Post {i+1}:\n{prompt}\n{'-' * 40}" for i, prompt in enumerate(prompts))

            combined_prompt += f"\n\nRespond with a comma-separated list of Yes/No for each post (e.g., 'Yes,No,Yes'):"

            completion = self.classifier.client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[{
                    "role": "user",
                    "content": combined_prompt
                }]
            )

            response = str(completion.choices[0].message.content).strip().lower()
            batch_results = ["yes" in r.lower() for r in response.split(",")]
            results.extend(batch_results)

        return results

    def format_comment(self, comment: PrawComment, depth=0, max_depth: int = 5) -> Optional[Comment]:
        if depth > max_depth:  # Limit comment depth
            return None

        comment_data = Comment(
            id=comment.id,
            author=str(comment.author.name) if comment.author else "[deleted]",
            content=comment.body,
            date=datetime.fromtimestamp(comment.created_utc, pytz.UTC),
            score=comment.score,
            depth=depth,
        )

        for reply in comment.replies:
            if not isinstance(reply, PrawComment):
                continue

            formatted_reply = self.format_comment(reply, depth + 1, max_depth)
            if formatted_reply:
                comment_data.replies.append(formatted_reply)

        return comment_data

    def add_comments_to_post(self, post: Post, max_comments: int = 100) -> Optional[Post]:
        try:
            # Limit the number of "more comments" expansions
            post.submission.comments.replace_more(limit=3)

            # Process only top-level comments up to max_comments
            for i, comment in enumerate(post.submission.comments):
                if i >= max_comments:
                    break

                formatted_comment = self.format_comment(comment)
                if formatted_comment:
                    post.comments.append(formatted_comment)
            return post
        except Exception as e:
            print(f"Error formatting submission {post.id}: {e}")
            return None

    def create_ai_prompt(self, submissions: List[Post]) -> str:
        """
        Create a prompt for AI analysis of multiple submissions.

        Args:
            submissions: List of formatted submission dictionaries

        Returns:
            str: Formatted prompt for AI analysis
        """
        prompt = """Please analyze these Reddit submissions about tools and create a comprehensive summary that:

1. Identifies all unique tools mentioned across all submissions
2. Groups related discussions about the same tools
3. Summarizes the general sentiment and key points about each tool
4. Notes any comparisons or alternatives suggested
5. Identifies any patterns or trends in tool preferences

For each tool, please include:
- The context in which it was discussed (which submissions/comments)
- Aggregated feedback from all mentions
- Common comparisons with other tools
- Notable features or use cases highlighted

Here are the submissions:

"""
        for submission in submissions:
            prompt += f"\n=== SUBMISSION {submission.id} ===\n"
            prompt += f"Posted in r/{submission.subreddit} on {submission.date}\n"
            prompt += f"Title: {submission.title}\n"
            prompt += f"Content: {submission.content}\n"
            prompt += f"Score: {submission.score}\n"
            prompt += "\nComments:\n"

            def format_comment_for_prompt(comment, indent=""):
                """Format a comment for the prompt with proper indentation."""
                comment_replaced = comment.content.replace('\n', f'\n{indent}│  ')
                comment_text = (
                    f"{indent}├─ u/{comment.author} "
                    f"(Score: {comment.score}):\n"
                    f"{indent}│  {comment_replaced}\n"
                )

                for reply in comment.replies:
                    comment_text += format_comment_for_prompt(reply, indent + "│  ")

                return comment_text

            for comment in submission.comments:
                prompt += format_comment_for_prompt(comment)

            prompt += "\n"

        return prompt


    def create_condensed_ai_prompt(self, submissions: List[Post]) -> str:
        """
        Create a prompt for AI analysis of multiple submissions.

        Args:
            submissions: List of formatted submission dictionaries

        Returns:
            str: Formatted prompt for AI analysis
        """
        prompt = """Please analyze these Reddit submissions about tools and create a comprehensive summary that:

1. Identifies all unique tools mentioned across all submissions
2. Groups related discussions about the same tools
3. Summarizes the general sentiment and key points about each tool
4. Notes any comparisons or alternatives suggested
5. Identifies any patterns or trends in tool preferences

For each tool, please include:
- The context in which it was discussed (which submissions/comments)
- Aggregated feedback from all mentions
- Common comparisons with other tools
- Notable features or use cases highlighted

Here are the submissions:

"""
        for submission in submissions:
            prompt += f"\n=== SUBMISSION ===\n"
            prompt += f"Title: {submission.title}\n"
            prompt += f"Content: {submission.content}\n"
            prompt += "\nComments:\n"

            def format_comment_for_prompt(comment, indent=""):
                """Format a comment for the prompt with proper indentation."""
                comment_replaced = comment.content.replace('\n', f'\n{indent}│  ')
                comment_text = (
                    f"{indent}├─ {comment_replaced} "
                )

                for reply in comment.replies:
                    comment_text += format_comment_for_prompt(reply, indent + "│  ")

                return comment_text

            for comment in submission.comments:
                prompt += format_comment_for_prompt(comment)

            prompt += "\n"

        return prompt

def main():
    load_dotenv()

    max_workers = 10
    classifier = WritingToolClassifier()
    analyzer = Analyzer(
        client_id=str(os.environ.get("REDDIT_CLIENT_ID")),
        client_secret=str(os.environ.get("REDDIT_CLIENT_SECRET")),
        user_agent=str(os.environ.get("REDDIT_USER_AGENT")),
        classifier=classifier
    )

    # Get recent posts with parallel processing
    posts = analyzer.get_recent_posts(days=3, max_workers=max_workers)

    # Batch classify posts
    valid_indices = analyzer.classify_batch(posts)
    valid_posts = [post for post, is_valid in zip(posts, valid_indices) if is_valid]

    # Format valid posts with parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        posts_with_comments = list(executor.map(analyzer.add_comments_to_post, valid_posts))
    posts_with_comments = [post for post in posts_with_comments if post is not None]

    prompt = analyzer.create_ai_prompt(posts_with_comments)
    condensed_prompt = analyzer.create_condensed_ai_prompt(posts_with_comments)
    formatted_posts = [post.to_dict() for post in posts_with_comments]

    # Example of saving the data
    with open("submissions_data.json", "w") as f:
        json.dump(formatted_posts, f, indent=2)

    with open("ai_prompt.txt", "w") as f:
        f.write(prompt)

    with open("ai_prompt_condensed.txt", "w") as f:
        f.write(condensed_prompt)

    print(f"Processed {len(formatted_posts)} tool-related submissions")

if __name__ == "__main__":
    main()
