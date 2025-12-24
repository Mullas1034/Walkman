# Changelog

All notable changes to the Walkman project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-01-XX

### Added - Initial Release

#### Core Features
- **Spotify Sync**: Complete Spotify liked songs synchronization with metadata
  - Audio features (BPM) fetching in batches of 100
  - Artist genres fetching in batches of 50
  - Album artwork URL extraction
  - JSON and text file output formats

- **Music Discovery Engine**: AI-powered recommendation system
  - 4-strategy recommendation engine (40+30+20+10 songs)
  - Genre-based recommendations from top artists
  - Artist exploration for middle-tier artists
  - Temporal diversity through random sampling
  - Random exploration of lesser-known artists
  - Exclusion of liked, approved, pending, and rejected songs

- **YouTube Downloader**: Automated YouTube search and download
  - High-quality MP3 download (320kbps)
  - FFmpeg integration for audio extraction
  - Resume capability via completion tracking
  - Batch download support
  - Cookie file support for age-restricted content

- **Metadata Embedder**: Professional ID3v2.3 tag embedding
  - Title, Artist, Album Artist, Album tags
  - Genre, Year, BPM tags
  - Album artwork embedding (JPEG)
  - Fuzzy string matching (75% threshold)
  - Success/failure reporting

- **iTunes Integrator**: iPod approval workflow automation
  - Windows COM interface integration
  - "On-The-Go" playlist reading
  - Automatic song classification (approved/rejected)
  - File organization (library/staging/discovered)
  - Metadata tracking file updates
  - Playlist clearing after integration

#### Architecture
- Modular Python package structure (`src/` organization)
- Comprehensive logging system throughout
- Type hints on all functions
- Google-style docstrings
- Path management via constants
- Professional error handling

#### Documentation
- Complete README.md with quickstart guide
- Detailed SETUP.md for installation
- Comprehensive WORKFLOW.md for usage
- Full API.md for developers
- CHANGELOG.md for version tracking

#### Data Management
- JSON-based metadata storage
- Separate folders for different music states
- Resume support for long-running operations
- Approval/rejection history tracking

---

## [Unreleased]

### Planned Features
- Web UI for discovery management
- Apple Music API integration
- Collaborative filtering recommendations
- Automatic playlist generation
- Cross-platform iTunes alternative (Linux/Mac)
- Duplicate detection and removal
- Advanced taste profile analytics
- Export to streaming services
- Recommendation explanation system

### Known Issues
- iTunes integration Windows-only (requires pywin32)
- Age-restricted YouTube videos require cookie export
- Large libraries (>5000 songs) may have slow initial sync
- Fuzzy matching occasionally matches wrong songs (rare)

---

## Version History

### Version Numbering

- **Major version (X.0.0)**: Incompatible API changes
- **Minor version (0.X.0)**: New features, backwards-compatible
- **Patch version (0.0.X)**: Bug fixes, backwards-compatible

### Migration Guide

No migrations required yet - this is the initial release.

---

## Credits

### Contributors
- Kieran - Initial development and architecture

### Dependencies
- [spotipy](https://spotipy.readthedocs.io/) - Spotify Web API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [mutagen](https://mutagen.readthedocs.io/) - Audio metadata library
- [pywin32](https://github.com/mhammond/pywin32) - Windows COM automation
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variables
- [requests](https://requests.readthedocs.io/) - HTTP library

---

## Release Process

### For Maintainers

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md with release date
3. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with changelog
6. Build and publish to PyPI (if applicable)

---

**For detailed usage instructions, see [WORKFLOW.md](docs/WORKFLOW.md)**

**For API documentation, see [API.md](docs/API.md)**
