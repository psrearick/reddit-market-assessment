import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from backup.post import Post

class Classifier:
    def __init__(self, subreddits: List[str] = []) -> None:
        load_dotenv()
        self.subreddits = subreddits
        self.topic = ""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

    def is_valid(self, post: Post) -> bool:
        if not self.topic:
            return False

        prompt = f"""Analyze this Reddit post and determine if it's about {self.topic}.
        Consider both explicit mentions and implicit references to this topic.

        Title: {post.title}
        Content: {post.content}

        Please respond with:
        Is this post about {self.topic}? (Yes/No)

        Follow the provided format. Your response must be a single word with no formatting.

        Format: [Yes/No]
        """

        completion = self.client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                "role": "user",
                "content": prompt
                }
            ]
        )

        response = str(completion.choices[0].message.content).strip().lower()

        return "yes" in response
