"""
Ollama API client for local LLM interaction.
"""

import json
import urllib.request
import urllib.error


class OllamaClient:
    """Simple client for the Ollama REST API."""

    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def check_connection(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check if our model (or a variant) is available
                for m in models:
                    if self.model.split(":")[0] in m:
                        return True
                # Model not pulled yet
                if models:
                    print(f"\n  Available models: {', '.join(models)}")
                    print(f"  Required model '{self.model}' not found.")
                return False
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            return False

    def generate(self, prompt: str, system: str = "", temperature: float = 0.3,
                 max_retries: int = 3) -> str | None:
        """
        Generate a completion from the model.

        Args:
            prompt: The user prompt
            system: System prompt for context
            temperature: Sampling temperature (lower = more deterministic)
            max_retries: Number of retries on failure

        Returns:
            The model's response text, or None on failure
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode())
                    return data.get("response", "")
            except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt + 1}/{max_retries} - {e}")
                else:
                    print(f"  ERROR: Failed after {max_retries} attempts: {e}")
                    return None
            except json.JSONDecodeError as e:
                print(f"  ERROR: Invalid JSON response: {e}")
                return None

    def generate_json(self, prompt: str, system: str = "", temperature: float = 0.2,
                      max_retries: int = 3) -> dict | None:
        """
        Generate a JSON response from the model.

        Uses Ollama's native format=json mode to guarantee valid JSON output,
        then falls back to manual extraction if needed. On JSON parse failure,
        retries with a correction prompt before giving up.

        Returns:
            Parsed dict, or None on failure
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",   # Grammar-constrained JSON output
            "options": {
                "temperature": temperature,
                "num_predict": 2048,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        current_prompt = prompt
        for attempt in range(max_retries):
            try:
                payload["prompt"] = current_prompt
                req = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode())
                    text = data.get("response", "")

                result = self._extract_json(text)
                if result is not None:
                    return result

                # JSON extraction failed — retry with a correction prompt
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt + 1} — fixing malformed JSON...")
                    current_prompt = (
                        f"The previous response was not valid JSON.\n"
                        f"Original request: {prompt}\n\n"
                        f"Output ONLY the JSON object with no extra text."
                    )

            except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt + 1}/{max_retries} - {e}")
                else:
                    print(f"  ERROR: Failed after {max_retries} attempts: {e}")
                    return None
            except json.JSONDecodeError as e:
                print(f"  ERROR: Invalid API response: {e}")
                return None

        print("  WARNING: Could not get valid JSON after retries")
        return None

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """Extract JSON from a response that may contain markdown fences or extra text."""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        import re
        patterns = [
            r"```json\s*\n(.*?)```",
            r"```\s*\n(.*?)```",
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",  # Nested braces
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue

        # Last resort: find the first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        print(f"  WARNING: Could not extract JSON from LLM response")
        return None
