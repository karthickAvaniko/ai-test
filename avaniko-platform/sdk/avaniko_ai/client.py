"""
Avaniko AI Python SDK
Usage:
    from avaniko_ai import Avaniko
    client = Avaniko(api_key="ava-sk-xxxx")
    response = client.chat("Hello!")
"""
import httpx
import json
import time
from typing import Optional, List, Iterator, AsyncIterator
from .exceptions import AvanikoError, AuthError, RateLimitError, APIError

DEFAULT_BASE_URL = "https://api.avaniko.com"

class Avaniko:
    def __init__(
        self,
        api_key:  str,
        base_url: str = DEFAULT_BASE_URL,
        timeout:  int = 120,
        max_retries: int = 3
    ):
        if not api_key.startswith("ava-sk-"):
            raise AuthError("Invalid API key format. Must start with 'ava-sk-'")

        self.api_key     = api_key
        self.base_url    = base_url.rstrip("/")
        self.timeout     = timeout
        self.max_retries = max_retries
        self._headers    = {
            "x-api-key":    api_key,
            "Content-Type": "application/json",
            "User-Agent":   "avaniko-python/1.0.0"
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.request(method, url, headers=self._headers, **kwargs)
                    if resp.status_code == 401:
                        raise AuthError("Invalid or expired API key")
                    if resp.status_code == 429:
                        raise RateLimitError("Rate limit exceeded. Slow down your requests.")
                    if resp.status_code >= 500:
                        if attempt < self.max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        raise APIError(f"Server error: {resp.status_code}")
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise APIError(f"Connection failed after {self.max_retries} retries: {e}")

    # ── Chat ─────────────────────────────────────────────
    def chat(
        self,
        message:       str,
        model:         str = "qwen3-moe",
        system:        Optional[str] = None,
        project_id:    Optional[str] = None,
        temperature:   float = 0.7,
        max_tokens:    int = 4096,
        history:       Optional[List[dict]] = None
    ) -> str:
        messages = list(history or []) + [{"role": "user", "content": message}]
        payload  = {
            "model":       model,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  max_tokens,
            "stream":      False
        }
        if system:     payload["system"]     = system
        if project_id: payload["project_id"] = project_id

        result = self._request("POST", "/v1/chat/completions", json=payload)
        return result["choices"][0]["message"]["content"]

    def chat_raw(self, **kwargs) -> dict:
        """Returns full OpenAI-format response."""
        return self._request("POST", "/v1/chat/completions", json=kwargs)

    # ── Streaming ────────────────────────────────────────
    def stream(
        self,
        message:     str,
        model:       str = "qwen3-moe",
        system:      Optional[str] = None,
        project_id:  Optional[str] = None,
        temperature: float = 0.7,
        max_tokens:  int = 4096
    ) -> Iterator[str]:
        payload = {
            "model":       model,
            "messages":    [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens":  max_tokens,
            "stream":      True
        }
        if system:     payload["system"]     = system
        if project_id: payload["project_id"] = project_id

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers,
                json=payload
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data  = json.loads(data_str)
                        token = data["choices"][0]["delta"].get("content", "")
                        if token:
                            yield token
                    except Exception:
                        continue

    # ── Embeddings ───────────────────────────────────────
    def embed(self, text: str, model: str = "qwen3-moe") -> List[float]:
        result = self._request("POST", "/v1/embeddings", json={"input": text, "model": model})
        return result["data"][0]["embedding"]

    def embed_batch(self, texts: List[str], model: str = "qwen3-moe") -> List[List[float]]:
        result = self._request("POST", "/v1/embeddings", json={"input": texts, "model": model})
        return [d["embedding"] for d in result["data"]]

    # ── Models ───────────────────────────────────────────
    def models(self) -> List[dict]:
        return self._request("GET", "/v1/models")["data"]

    # ── Usage ────────────────────────────────────────────
    def usage(self, days: int = 30) -> dict:
        return self._request("GET", f"/v1/usage?days={days}")

    # ── Projects ─────────────────────────────────────────
    def create_project(
        self,
        name:          str,
        system_prompt: str,
        model_id:      str = "qwen3-moe",
        temperature:   float = 0.7,
        max_tokens:    int = 4096,
        description:   str = ""
    ) -> dict:
        return self._request("POST", "/v1/projects", json={
            "name":          name,
            "system_prompt": system_prompt,
            "model_id":      model_id,
            "temperature":   temperature,
            "max_tokens":    max_tokens,
            "description":   description
        })

    def list_projects(self) -> List[dict]:
        return self._request("GET", "/v1/projects")["projects"]

    def delete_project(self, project_id: str) -> dict:
        return self._request("DELETE", f"/v1/projects/{project_id}")

    # ── API Keys ─────────────────────────────────────────
    def create_api_key(self, name: str = "My Key", daily_limit: int = 1000) -> dict:
        return self._request("POST", "/v1/api-keys/create", json={
            "name": name, "daily_limit": daily_limit
        })

    # ── Context manager support ───────────────────────────
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return f"Avaniko(base_url='{self.base_url}', key='...{self.api_key[-8:]}')"
