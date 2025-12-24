"""
Walkman: Intelligent Music Discovery System

Setup configuration for pip installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / 'README.md'
with open(readme_path, 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / 'requirements.txt'
with open(requirements_path, 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='walkman-music',
    version='1.0.0',
    author='Kieran',
    author_email='your.email@example.com',
    description='Intelligent Music Discovery System for Spotify, YouTube, and iTunes/iPod',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/Walkman',
    project_urls={
        'Documentation': 'https://github.com/yourusername/Walkman/blob/main/docs/API.md',
        'Source': 'https://github.com/yourusername/Walkman',
        'Tracker': 'https://github.com/yourusername/Walkman/issues',
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'docs']),
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'walkman-sync=src.spotify_sync:main',
            'walkman-discover=src.music_discovery:main',
            'walkman-integrate=src.itunes_integrator:main',
            'walkman-embed=src.metadata_embedder:main',
            'walkman-download=src.youtube_downloader:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    keywords='music discovery spotify youtube itunes metadata mp3 recommendations',
    license='MIT',
    include_package_data=True,
    package_data={
        'src': ['py.typed'],
    },
    zip_safe=False,
)
