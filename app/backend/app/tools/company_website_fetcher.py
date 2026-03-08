"""Website content fetcher tool for company information lookup."""

from __future__ import annotations

import json
import logging
import re
from html import unescape
from typing import Annotated
from urllib.parse import urlparse

import httpx
from agent_framework._tools import tool
from pydantic import Field

logger = logging.getLogger(__name__)


class CompanyWebsiteFetcher:
    """Helper class that fetches and extracts readable text from company websites."""

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        max_chars_per_site: int = 4000,
        default_websites: str | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_chars_per_site = max_chars_per_site
        self._default_websites = default_websites or ""

    @staticmethod
    def _normalize_url(url: str) -> str:
        cleaned = url.strip()
        if not cleaned:
            return cleaned
        if not cleaned.startswith(("http://", "https://")):
            cleaned = f"https://{cleaned}"
        return cleaned

    @staticmethod
    def _split_urls(raw_urls: str) -> list[str]:
        tokens = re.split(r"[\s,;]+", raw_urls.strip())
        return [token for token in tokens if token.strip()]

    @staticmethod
    def _extract_title(html: str) -> str | None:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return unescape(re.sub(r"\s+", " ", match.group(1)).strip())

    @staticmethod
    def _html_to_text(html: str) -> str:
        without_scripts = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        without_styles = re.sub(r"<style\b[^>]*>.*?</style>", " ", without_scripts, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", without_styles)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @tool(name="fetchCompanyWebsiteContent")
    def fetch_company_website_content(
        self,
        urls: Annotated[
            str,
            Field(
                description=(
                    "One or more company website URLs separated by comma, whitespace, or newline. "
                    "Examples: 'https://contoso.com, https://fabrikam.com/about'. "
                    "Pass empty string to use configured COMPANY_WEBSITES."
                )
            ),
        ],
    ) -> Annotated[
        str,
        Field(
            description=(
                "JSON string with fetched website summaries. Includes url, title, snippet, and status "
                "for each requested site."
            )
        ),
    ]:
        input_urls = urls.strip() if urls else ""
        if not input_urls:
            input_urls = self._default_websites

        raw_tokens = self._split_urls(input_urls)
        normalized_urls = [self._normalize_url(token) for token in raw_tokens]

        if not normalized_urls:
            return json.dumps({"error": "No valid URLs provided and no COMPANY_WEBSITES configured", "results": []})

        results: list[dict[str, str | int]] = []

        with httpx.Client(timeout=self._timeout_seconds, follow_redirects=True) as client:
            for url in normalized_urls:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    results.append({"url": url, "status": "error", "message": "Invalid URL"})
                    continue

                try:
                    response = client.get(url)
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                        results.append(
                            {
                                "url": url,
                                "status": "error",
                                "message": f"Unsupported content type: {content_type or 'unknown'}",
                            }
                        )
                        continue

                    html = response.text
                    title = self._extract_title(html) or ""
                    text = self._html_to_text(html)
                    snippet = text[: self._max_chars_per_site]

                    results.append(
                        {
                            "url": url,
                            "status": "ok",
                            "title": title,
                            "snippet": snippet,
                            "chars": len(snippet),
                        }
                    )
                except Exception as exc:  # pragma: no cover - defensive path
                    logger.warning("Failed to fetch website %s: %s", url, exc)
                    results.append({"url": url, "status": "error", "message": str(exc)})

        return json.dumps({"results": results}, indent=2)
