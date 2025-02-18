# import os
# from dotenv import load_dotenv
# import praw
# from datetime import datetime, timedelta
# import pytz
# from typing import Dict, List, Optional
# import json
# from collections import defaultdict
# import re

# from writing_analyzer import PostContent, WritingToolClassifier

# class RedditToolAnalyzer:
#     def __init__(self, client_id: str, client_secret: str, user_agent: str):
#         """Initialize Reddit client and setup analyzer."""
#         self.reddit = praw.Reddit(
#             client_id=client_id,
#             client_secret=client_secret,
#             user_agent=user_agent
#         )

#         self.classifier = WritingToolClassifier()
#         # # Common tool-related keywords to help identify relevant posts
#         # self.tool_keywords = {
#         #     'tool', 'software', 'app', 'application', 'library', 'framework',
#         #     'alternative', 'versus', 'vs', 'comparison', 'recommend',
#         #     'recommendation', 'solution', 'platform'
#         # }

#     # def is_tool_related(self, text: str) -> bool:
#     #     """
#     #     Check if text is likely about tools/software.

#     #     Args:
#     #         text: The text to analyze

#     #     Returns:
#     #         bool: True if the text appears to be about tools
#     #     """
#     #     text_lower = text.lower()
#     #     # Check for tool-related keywords
#     #     if any(keyword in text_lower for keyword in self.tool_keywords):
#     #         return True
#     #     # Check for specific patterns like "How do I...", "What's the best..."
#     #     patterns = [
#     #         r"what('s| is) the best",
#     #         r"how (do|can|should) i",
#     #         r"looking for( a)?",
#     #         r"alternative to",
#     #         r"anyone use",
#     #         r"experience with"
#     #     ]
#     #     return any(re.search(pattern, text_lower) for pattern in patterns)

#     def get_recent_submissions(self, subreddit_name: str, days: int = 30) -> List[Dict]:
#         """
#         Get and filter submissions from the last N days.

#         Args:
#             subreddit_name: Name of the subreddit
#             days: Number of days to look back

#         Returns:
#             List[Dict]: Filtered and formatted submissions
#         """
#         subreddit = self.reddit.subreddit(subreddit_name)
#         cutoff_time = datetime.now(pytz.UTC) - timedelta(days=days)


#         all_posts = []
#         for submission in subreddit.new(limit=None):
#             if datetime.fromtimestamp(submission.created_utc, pytz.UTC) < cutoff_time:
#                 break

#             all_posts.append(PostContent(
#                 title=submission.title,
#                 text=submission.selftext,
#                 url=submission.url,
#                 date=datetime.fromtimestamp(submission.created_utc, pytz.UTC),
#                 name=submission.name
#             ))

#         formatted_posts = []
#         for post in all_posts:
#             evaluation = self.classifier.run(post)

#             # print(evaluation)

#             # Check if the submission is tool-related
#             # if not self.is_tool_related(f"{submission.title} {submission.selftext}"):
#             #     continue

#         #     if not evaluation['is_tool_related']:
#         #         continue

#         #     formatted_submission = self.format_submission(submission)
#         #     if formatted_submission:
#         #         formatted_submissions.append(formatted_submission)

#         # return formatted_submissions

#     def format_submission(self, submission) -> Optional[Dict]:
#         """
#         Format a submission and its comments into a structured dictionary.

#         Args:
#             submission: PRAW submission object

#         Returns:
#             Optional[Dict]: Formatted submission data
#         """
#         try:
#             submission.comments.replace_more(limit=None)

#             formatted_data = {
#                 "id": submission.id,
#                 "url": f"https://reddit.com{submission.permalink}",
#                 "timestamp": datetime.fromtimestamp(submission.created_utc, pytz.UTC).isoformat(),
#                 "title": submission.title,
#                 "content": submission.selftext,
#                 "author": str(submission.author) if submission.author else "[deleted]",
#                 "score": submission.score,
#                 "comments": []
#             }

#             def format_comment(comment, depth=0):
#                 """Format a single comment and its replies."""
#                 if not isinstance(comment, praw.models.Comment):
#                     return None

#                 comment_data = {
#                     "id": comment.id,
#                     "author": str(comment.author) if comment.author else "[deleted]",
#                     "content": comment.body,
#                     "timestamp": datetime.fromtimestamp(comment.created_utc, pytz.UTC).isoformat(),
#                     "score": comment.score,
#                     "depth": depth,
#                     "replies": []
#                 }

#                 # Add replies
#                 for reply in comment.replies:
#                     formatted_reply = format_comment(reply, depth + 1)
#                     if formatted_reply:
#                         comment_data["replies"].append(formatted_reply)

#                 return comment_data

#             # Format all top-level comments
#             for comment in submission.comments:
#                 formatted_comment = format_comment(comment)
#                 if formatted_comment:
#                     formatted_data["comments"].append(formatted_comment)

#             return formatted_data

#         except Exception as e:
#             print(f"Error formatting submission {submission.id}: {e}")
#             return None

#     def create_ai_prompt(self, submissions: List[Dict]) -> str:
#         """
#         Create a prompt for AI analysis of multiple submissions.

#         Args:
#             submissions: List of formatted submission dictionaries

#         Returns:
#             str: Formatted prompt for AI analysis
#         """
#         prompt = """Please analyze these Reddit submissions about tools and create a comprehensive summary that:

# 1. Identifies all unique tools mentioned across all submissions
# 2. Groups related discussions about the same tools
# 3. Summarizes the general sentiment and key points about each tool
# 4. Notes any comparisons or alternatives suggested
# 5. Identifies any patterns or trends in tool preferences

# For each tool, please include:
# - The context in which it was discussed (which submissions/comments)
# - Aggregated feedback from all mentions
# - Common comparisons with other tools
# - Notable features or use cases highlighted

# Here are the submissions:

# """
#         for submission in submissions:
#             prompt += f"\n=== SUBMISSION {submission['id']} ===\n"
#             prompt += f"Posted by u/{submission['author']} on {submission['timestamp']}\n"
#             prompt += f"Title: {submission['title']}\n"
#             prompt += f"Content: {submission['content']}\n"
#             prompt += "\nComments:\n"

#             def format_comment_for_prompt(comment, indent=""):
#                 """Format a comment for the prompt with proper indentation."""
#                 comment_replaced = comment['content'].replace('\n', f'\n{indent}│  ')
#                 comment_text = (
#                     f"{indent}├─ u/{comment['author']} "
#                     f"(Score: {comment['score']}):\n"
#                     f"{indent}│  {comment_replaced}\n"
#                 )

#                 for reply in comment['replies']:
#                     comment_text += format_comment_for_prompt(reply, indent + "│  ")

#                 return comment_text

#             for comment in submission['comments']:
#                 prompt += format_comment_for_prompt(comment)

#             prompt += "\n"

#         return prompt

# # Example usage
# if __name__ == "__main__":
#     load_dotenv()
#     analyzer = RedditToolAnalyzer(
#         client_id=str(os.environ.get("REDDIT_CLIENT_ID")),
#         client_secret=str(os.environ.get("REDDIT_CLIENT_SECRET")),
#         user_agent=str(os.environ.get("REDDIT_USER_AGENT"))
#     )

#     # Get submissions from a subreddit
#     submissions = analyzer.get_recent_submissions("writing", days=5)

#     # Create AI prompt
#     # prompt = analyzer.create_ai_prompt(submissions)

#     # # Example of saving the data
#     # with open("submissions_data.json", "w") as f:
#     #     json.dump(submissions, f, indent=2)

#     # with open("ai_prompt.txt", "w") as f:
#     #     f.write(prompt)

#     # print(f"Processed {len(submissions)} tool-related submissions")
