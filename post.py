from dataclasses import dataclass, field
from datetime import datetime
from praw.models import Submission

@dataclass
class Post:
    id: str
    title: str
    text: str
    url: str
    date: datetime
    name: str
    subreddit: str
    score: int
    submission: Submission
    comments: list = field(default_factory=list)

@dataclass
class Comment:
    id: str
    author: str
    content: str
    timestamp: str
    score: str
    depth: int
    replies: list = field(default_factory=list)
