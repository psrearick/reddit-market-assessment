"""LLM API client for Reddit Market Research Framework."""

import requests
import time
import json

from utils.settings import Settings


class LLMClient:
    """Handles communication with LLM APIs."""

    def __init__(self, settings: 'Settings'):
        """Initialize with settings."""
        self.settings = settings
        if not self.settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not found in settings.")

    def call_api(self, messages: list[dict], model: str, response_format: str = "json_object", timeout: float | None = None) -> str | None:
        """
        Send a request to the OpenRouter API.

        Args:
            messages: List of message dictionaries for the conversation
            model: Model name to use
            response_format: Optional response format (e.g., "json_object")
            timeout: Optional timeout override

        Returns:
            Response content string or None if failed
        """
        if timeout is None:
            timeout = self.settings.api_timeout

        headers = {"Authorization": f"Bearer {self.settings.openrouter_api_key}"}
        data = {"model": model, "messages": messages}

        if response_format == "json_object":
            data["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(
                self.settings.openrouter_api_url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                print("Rate limit hit. Waiting...")
                time.sleep(60)
            return None

        except (KeyError, IndexError):
            print(f"Unexpected API response format")
            return None

    def call_with_json_response(self, messages: list[dict], model: str, timeout: float | None = None) -> dict | None:
        """
        Call API expecting a JSON response and parse it.

        Returns:
            Parsed JSON object or error dict
        """
        response_str = self.call_api(messages, model, response_format="json_object", timeout=timeout)

        if response_str:
            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from LLM response.")
                return {"error": "Failed to parse LLM response", "raw_response": response_str}

        return {"error": "No response from LLM"}
