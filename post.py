from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from praw.models import Submission

@dataclass
class Comment:
    id: str
    author: str
    content: str
    date: datetime
    score: str
    depth: int
    replies: list = field(default_factory=list)

@dataclass
class Post:
    id: str
    author: str
    title: str
    content: str
    url: str
    date: datetime
    name: str
    subreddit: str
    score: int
    submission: Submission
    comments: List[Comment] = field(default_factory=list)

    def format_post(self) -> Dict[str, str|list]:
        formatted_data = {
            "id": self.id,
            "url": self.url,
            "author": self.author,
            "date": self.date.isoformat(),
            "title": self.title,
            "content": self.content,
            "name": self.name,
            "subreddit": self.subreddit,
            "score": self.score,
            "comments": []
        }

        def format_comment(comment: Comment, depth=0) -> Dict[str, str|list]:
            formatted_comment = {
                "id": comment.id,
                "author": comment.author if comment.author else "[deleted]",
                "content": comment.content,
                "date": comment.date.isoformat(),
                "score": comment.score,
                "depth": depth,
                "replies": []
            }

            for reply in comment.replies:
                formatted_comment["replies"].append(format_comment(reply, depth+1))

            return formatted_comment

        for comment in self.comments:
            formatted_data["comments"].append(format_comment(comment))

        return formatted_data
