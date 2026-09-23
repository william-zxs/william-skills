# Lex Fridman YouTube → EPUB

[简体中文](README.zh-CN.md)

Turn a full Lex Fridman Podcast YouTube episode into an EPUB. The tool finds the exact episode in the [official Lex Fridman Podcast index](https://lexfridman.com/podcast) and uses its **official transcript** as the book text—it never substitutes YouTube auto-generated captions.

It creates an English-source EPUB by default. When a target language is specified, Codex translates the title, chapter headings, body text, and reader-facing book metadata before creating a translated edition.

## Features

- Accepts a YouTube URL or 11-character video ID.
- Resolves the official episode and transcript from the podcast index, then enriches metadata from the RSS feed.
- Uses the matching YouTube thumbnail as the preferred cover, falling back to the RSS episode image when necessary.
- Saves the original transcript, source URLs, metadata, and cover image for review and reproducible builds.
- Builds the original English edition or a translated edition in any requested language; translation caches resume interrupted work.
- Validates parsed transcript content and EPUB structure during the build.

## Requirements

- Python 3
- Pillow: `python3 -m pip install Pillow`
- Network access for the first online build, to reach the Lex website, RSS feed, and YouTube thumbnail
- Codex CLI with model access, only for non-English translations

## Install for an agent

Install this skill for Codex from GitHub:

```bash
npx skills add william-zxs/william-skills \
  --skill lex-fridman-youtube-to-epub \
  --agent codex
```

This installs it for the current project. Add `--global` to make it available to Codex in every project:

```bash
npx skills add william-zxs/william-skills \
  --skill lex-fridman-youtube-to-epub \
  --agent codex --global
```

## Ask the agent to build an EPUB

Copy this paragraph, replacing the bracketed values:

```text
Use the lex-fridman-youtube-to-epub skill.
Video: [Lex Fridman Podcast YouTube URL or 11-character video ID]
Target language: [target language, or English]
Use the exactly matched official Lex transcript and matching cover image. Verify both before reporting the EPUB path.
```

For example, replace the values with `https://www.youtube.com/watch?v=NYFGCESmikA` and `Simplified Chinese`. If the video cannot be exactly matched to an official transcript, the skill stops rather than substituting YouTube captions.
