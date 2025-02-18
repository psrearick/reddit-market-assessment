import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from post import Post

class Classifier:
    def __init__(self, subreddits: List[str] = []) -> None:
        load_dotenv()
        self.subreddits = subreddits
        self.topic = ""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

    def is_post_valid(self, post: Post) -> bool:
        if not self.topic:
            return False


        prompt = f"""Analyze this Reddit post and determine if it's about {self.topic}.
        Consider both explicit mentions and implicit references to this topic.

        Title: {post.title}
        Content: {post.text}

        Please respond with:
        1. Is this post about {self.topic}? (Yes/No)
        2. Confidence (0-1)
        3. Brief explanation of reasoning

        Format: [Yes/No]|[0.0-1.0]|[explanation]
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

        print(completion.choices[0].message.content)

        return False


    #     message = await client.messages.create(
    #         model="claude-3-5-sonnet-latest",
    #         max_tokens=1024,
    #         temperature=0,
    #         messages=[{"role": "user", "content": prompt}]
    #     )

    #     # Parse Claude's response
    #     response = message.content
    #     try:
    #         decision, confidence, reasoning = response[0].text.split('|')
    #         is_tool_related = decision.strip().lower() == 'yes'
    #         confidence = float(confidence.strip())
    #         return {
    #             'is_tool_related': is_tool_related,
    #             'confidence': confidence,
    #             'evidence': reasoning.strip()
    #         }
    #     except:
    #         return {
    #            'is_tool_related': False,
    #            'confidence': 0.0,
    #            'evidence': "Error parsing AI response"
    #            }
