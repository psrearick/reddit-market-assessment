import asyncio
from datetime import datetime
from openai import OpenAI
import praw
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from collections import defaultdict
from anthropic import AsyncAnthropic
import re
from dotenv import load_dotenv
import os

@dataclass
class PostContent:
    title: str
    text: str
    url: str
    date: datetime
    name: str

class WritingToolClassifier:
    def __init__(self):
        # Load spaCy model for NLP tasks
        self.nlp = spacy.load("en_core_web_sm")

        # Known writing software and related terms
        self.writing_tools = {
            # Popular writing software
            'scrivener', 'ulysses', 'final draft', 'fade in',
            'celtx', 'manuskript', 'bibisco', 'writeroom', 'focus writer',
            'hemingway editor', 'prowritingaid', 'grammarly', 'campfire',
            'novelwriter', 'storyist', 'writeway', 'ywriter', 'wavemaker',
            'novlr', 'dabble', 'livingwriter', 'atticus', 'word',

            # Generic tool terms
            'software', 'app', 'application', 'tool', 'program',
            'editor', 'word processor', 'writing platform',

            # Features
            'autocorrect', 'spell', 'grammar', 'check',
            'outline', 'outlining', 'timeline', 'character sheet',
            'manuscript format', 'export', 'backup', 'sync', 'manage', 'manager', 'managing',

            # Common writing software features
            'dark mode', 'distraction free', 'word count',
            'chapter', 'scene', 'revision', 'draft',
            'formatting', 'template', 'stylesheet'
        }

        # Tool-related action verbs
        self.tool_actions = {
            'recommend', 'suggest', 'try', 'use', 'switch',
            'export', 'import', 'save', 'backup', 'sync',
            'install', 'download', 'purchase', 'buy'
        }

        # Initialize patterns for complex matching
        self.initialize_patterns()

    def initialize_patterns(self):
        """Initialize regex patterns for sophisticated matching."""
        self.patterns = [
            # Direct tool questions
            r"what (?:tool|software|app|program)s?(?:\s+do\s+you)?(?:\s+use|recommend)",
            r"looking\s+for\s+(?:a\s+)?(?:new\s+)?(?:writing\s+)?(?:tool|software|app|program)",

            # Comparative patterns
            r"(?:better|worse|alternative)\s+than\s+(\w+)",
            r"switch(?:ing)?\s+from\s+(\w+)\s+to",
            r"compared?\s+to\s+(\w+)",

            # Problem-solution patterns
            r"how\s+(?:do|can|should)\s+i\s+(?:organize|format|structure|outline)",
            r"(?:trouble|problem|issue|help)\s+with\s+(\w+)",
            r"anyone\s+(?:use|tried?|recommend)",

            # Feature requests/questions
            r"is\s+there\s+(?:a\s+)?(?:tool|software|app|program)\s+that\s+can",
            r"need\s+(?:a\s+)?(?:tool|software|app|program)\s+(?:that|for|to)",

            # Technical discussions
            r"(?:export|import|backup|sync|format)(?:ing)?\s+(?:to|from|with)",
            r"compatible\s+with",
            r"version\s+\d+[\.\d]*"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def analyze_entities(self, text: str) -> Set[str]:
        """
        Use spaCy to extract relevant entities and noun phrases.

        Args:
            text: Text to analyze

        Returns:
            Set[str]: Extracted relevant terms
        """
        doc = self.nlp(text)
        entities = set()

        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in {'PRODUCT', 'ORG', 'GPE'}:
                entities.add(ent.text.lower())

        # Extract noun phrases that might be tools
        for chunk in doc.noun_chunks:
            if any(tool in chunk.text.lower() for tool in self.writing_tools):
                entities.add(chunk.text.lower())

        return entities

    def check_context_windows(self, text: str) -> List[Tuple[str, str]]:
        """
        Analyze context windows around tool-related terms.

        Args:
            text: Text to analyze

        Returns:
            List[Tuple[str, str]]: List of (term, context) pairs
        """
        doc = self.nlp(text)
        contexts = []

        for sent in doc.sents:
            sent_text = sent.text.lower()

            # Check for tool terms
            for tool in self.writing_tools:
                if tool in sent_text:
                    # Get window of 5 words before and after
                    tool_index = sent_text.find(tool)
                    start = max(0, tool_index - 30)
                    end = min(len(sent_text), tool_index + len(tool) + 30)
                    context = sent_text[start:end]
                    contexts.append((tool, context))

        return contexts

    # async def classify_with_claude_ai(self, post: PostContent, client: AsyncAnthropic) -> Dict[str, bool|float|str]:
    #     """
    #     Use Claude to classify if a post is about writing tools.

    #     Args:
    #         post: Post content to analyze
    #         client: Anthropic API client

    #     Returns:
    #         Tuple[bool, float, str]: (is_tool_related, confidence, reasoning)
    #     """
    #     prompt = f"""Analyze this Reddit post and determine if it's about writing software/tools.
    #     Consider both explicit mentions and implicit references to writing tools.

    #     Title: {post.title}
    #     Content: {post.text}

    #     Please respond with:
    #     1. Is this post about writing software/tools? (Yes/No)
    #     2. Confidence (0-1)
    #     3. Brief explanation of reasoning

    #     Format: [Yes/No]|[0.0-1.0]|[explanation]
    #     """

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



    def classify_post(self, post: PostContent) -> Dict:
        """
        Combine multiple classification methods to determine if a post is about writing tools.

        Args:
            post: Post content to analyze

        Returns:
            Dict: Classification results with confidence scores and reasoning
        """
        combined_text = f"{post.title} {post.text}"

        # Method 1: Pattern Matching
        pattern_matches = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(combined_text.lower())
            if matches:
                pattern_matches.extend(matches)

        # Method 2: Entity Analysis
        entities = self.analyze_entities(combined_text)

        # Method 3: Context Windows
        contexts = self.check_context_windows(combined_text)

        # Combine evidence
        evidence = {
            'pattern_matches': pattern_matches,
            'entities': list(entities),
            'contexts': contexts,
            'tool_terms': [term for term in self.writing_tools if term in combined_text.lower()],
            'action_verbs': [verb for verb in self.tool_actions if verb in combined_text.lower()]
        }

        # Calculate confidence score
        confidence = self.calculate_confidence(evidence)

        return {
            'is_tool_related': confidence >= 0.6,
            'confidence': confidence,
            'evidence': evidence
        }

    def calculate_confidence(self, evidence: Dict) -> float:
        """
        Calculate confidence score based on collected evidence.

        Args:
            evidence: Dictionary of evidence from different methods

        Returns:
            float: Confidence score between 0 and 1
        """
        score = 0.0

        # Weight pattern matches
        if evidence['pattern_matches']:
            score += 0.3 * min(len(evidence['pattern_matches']) / 3, 1.0)

        # Weight entity matches
        if evidence['entities']:
            score += 0.2 * min(len(evidence['entities']) / 2, 1.0)

        # Weight context windows
        if evidence['contexts']:
            score += 0.2 * min(len(evidence['contexts']) / 2, 1.0)

        # Weight direct tool terms
        if evidence['tool_terms']:
            score += 0.2 * min(len(evidence['tool_terms']) / 2, 1.0)

        # Weight action verbs
        if evidence['action_verbs']:
            score += 0.1 * min(len(evidence['action_verbs']) / 2, 1.0)

        return min(score, 1.0)

    def run(self, post: PostContent):
        load_dotenv()
        classifier = WritingToolClassifier()

        # # Classify post
        # result = classifier.classify_post(post)

        # print(f"Is tool related: {result['is_tool_related']}")
        # print(f"Confidence: {result['confidence']:.2f}")
        # print("Evidence:")
        # for key, value in result['evidence'].items():
        #     print(f"- {key}: {value}")

        # client = AsyncAnthropic(
        #     api_key=os.environ.get("ANTHROPIC_API_KEY")
        # )

        # result = asyncio.run(classifier.classify_with_ai(post, client))
        # print(f"Is tool related: {result['is_tool_related']}")
        # print(f"Confidence: {result['confidence']:.2f}")
        # print(f"Evidence:\n- {result['evidence']}")

        # return result
