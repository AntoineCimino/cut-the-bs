"""YouTube URL parsing, metadata lookup, and transcript retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptError(RuntimeError):
    pass


@dataclass(frozen=True)
class Video:
    title: str
    transcript: str
    language: str


def extract_youtube_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    video_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.strip("/").split("/")
            video_id = parts[1] if len(parts) > 1 else ""
    if not video_id:
        raise TranscriptError("Unsupported or invalid YouTube URL.")
    return video_id


def _fetch_title(url: str, video_id: str) -> str:
    endpoint = "https://www.youtube.com/oembed?" + urlencode({"url": url, "format": "json"})
    try:
        request = Request(endpoint, headers={"User-Agent": "cut-the-bs/0.1"})
        with urlopen(request, timeout=10) as response:
            title = json.load(response).get("title")
        return str(title).strip() if title else f"YouTube video {video_id}"
    except (OSError, ValueError, json.JSONDecodeError):
        return f"YouTube video {video_id}"


def fetch_video(url: str) -> Video:
    video_id = extract_youtube_id(url)
    try:
        api = YouTubeTranscriptApi()
        try:
            transcript_data = api.fetch(video_id, languages=["en"])
            language = "en"
        except Exception:
            # No English transcript — fall back to whatever is available.
            found = next(iter(api.list(video_id)))
            transcript_data = found.fetch()
            language = found.language_code
        transcript = " ".join(item.text.strip() for item in transcript_data if item.text.strip())
    except Exception as exc:
        # Exception classes vary between youtube-transcript-api releases.
        raise TranscriptError("No transcript is available for this video, or YouTube could not be reached.") from exc
    if not transcript:
        raise TranscriptError("The available transcript is empty.")
    return Video(title=_fetch_title(url, video_id), transcript=transcript, language=language)
