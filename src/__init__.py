"""
Walkman: Intelligent Music Discovery System

A sophisticated pipeline for discovering, downloading, and managing music
across Spotify, YouTube, and iTunes/iPod.

Modules:
    spotify_sync: Sync Spotify liked songs with local metadata
    music_discovery: Generate personalized music recommendations
    youtube_downloader: Search and download songs from YouTube
    metadata_embedder: Embed ID3 tags into MP3 files
    itunes_integrator: Sync with iTunes and manage approval workflow
    utils: Common utilities and helper functions

Author: Kieran
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Kieran"

from .utils import (
    setup_logging,
    normalize_string,
    similarity_ratio,
    sanitize_filename,
)

__all__ = [
    "setup_logging",
    "normalize_string",
    "similarity_ratio",
    "sanitize_filename",
]
