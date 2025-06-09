from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from praw.models import Submission

@dataclass
class Comment:
    id: str
    author: str
    content: str
    date: datetime
    score: str
    depth: int
    replies: List["Comment"] = field(default_factory=list)

    def to_dict(self, depth=0) -> Dict[str, str|list]:
        formatted_comment = {
            "id": self.id,
            "author": self.author if self.author else "[deleted]",
            "content": self.content,
            "date": self.date.isoformat(),
            "score": self.score,
            "depth": depth,
            "replies": []
        }

        for reply in self.replies:
            formatted_comment["replies"].append(reply.to_dict(), depth+1)

        return formatted_comment

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
    comments: List["Comment"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, str|list]:
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

        for comment in self.comments:
            formatted_data["comments"].append(comment.to_dict())

        return formatted_data
