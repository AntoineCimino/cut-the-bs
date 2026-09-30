from unittest.mock import Mock

import pytest

import transcript


def test_fetch_video_uses_mocked_youtube_transcript(monkeypatch):
    api = Mock()
    api.fetch.return_value = [Mock(text="Synthetic opening."), Mock(text="Invented fact: 12 units.")]
    monkeypatch.setattr(transcript, "YouTubeTranscriptApi", lambda: api)
    monkeypatch.setattr(transcript, "_fetch_title", lambda _url, _id: "Synthetic video")
    video = transcript.fetch_video("https://youtu.be/abc123")
    assert video.title == "Synthetic video"
    assert video.transcript == "Synthetic opening. Invented fact: 12 units."
    assert video.language == "en"
    api.fetch.assert_called_once_with("abc123", languages=["en"])


def test_fetch_video_falls_back_to_available_language(monkeypatch):
    api = Mock()
    api.fetch.side_effect = RuntimeError("no English captions")
    found = Mock(language_code="fr")
    found.fetch.return_value = [Mock(text="Ouverture synthetique.")]
    api.list.return_value = [found]
    monkeypatch.setattr(transcript, "YouTubeTranscriptApi", lambda: api)
    monkeypatch.setattr(transcript, "_fetch_title", lambda _url, _id: "Synthetic video")
    video = transcript.fetch_video("https://youtu.be/abc123")
    assert video.language == "fr"
    assert video.transcript == "Ouverture synthetique."


def test_fetch_video_reports_missing_transcript(monkeypatch):
    api = Mock()
    api.fetch.side_effect = RuntimeError("captions disabled")
    api.list.side_effect = RuntimeError("no captions at all")
    monkeypatch.setattr(transcript, "YouTubeTranscriptApi", lambda: api)
    with pytest.raises(transcript.TranscriptError, match="No transcript is available"):
        transcript.fetch_video("https://www.youtube.com/watch?v=abc123")
