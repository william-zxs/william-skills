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

Give the agent these details:

- A full Lex Fridman Podcast YouTube URL or its 11-character video ID (required)
- An output directory for the generated EPUB (required)
- The target language, if you want a translation; omit it for the original English text
- Optional, verified overrides for the transcript URL, title, guest, or cover image when automatic discovery is unavailable

For example:

```text
Use the lex-fridman-youtube-to-epub skill to turn
https://www.youtube.com/watch?v=NYFGCESmikA into a Simplified Chinese EPUB.
Write all generated files to /path/to/output. Verify the official transcript
and cover before reporting the EPUB path. Do not send email.
```

For the English source edition, replace “Simplified Chinese EPUB” with “English EPUB” or omit the target language. The skill will report a clear error if the video cannot be exactly matched to an official transcript; do not ask it to substitute YouTube captions.

## Quick start

Run from the repository root:

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output
```

You can also pass the video ID directly:

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  NYFGCESmikA \
  --output-dir /path/to/output
```

Translate to Chinese, French, or Japanese:

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output \
  --language 中文

python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  NYFGCESmikA --output-dir /path/to/output --language French

python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  NYFGCESmikA --output-dir /path/to/output --language ja
```

`--language` accepts common language names (such as `中文`, `日语`, and `French`) and BCP 47 tags (such as `zh`, `fr`, and `ja`). Omit the option, or pass `en` / `English`, to keep the original English text.

## Output

Each build writes to the output directory you specify:

```text
output/
├── metadata.json                    # Traceable video, transcript, language, and count metadata
├── source/
│   ├── transcript.html              # Official transcript snapshot
│   └── youtube-thumbnail.jpg        # Source image used for the cover
├── translation/                     # Resumable cache for non-English builds
└── dist/
    └── lex-<episode>-<title>[-<language>].epub
```

The English EPUB uses the base filename; a translated edition includes its language tag. `metadata.json` records the cover, YouTube, episode, and transcript source URLs.

## Common options

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py --help
```

- `--metadata-only`: Parse and write metadata and the official transcript snapshot only; do not download a cover or create an EPUB.
- `--translation-cache FILE`: Use an existing aligned translation cache for a translated edition, including recovery or reuse scenarios.
- `--translated-title TEXT`, `--translated-guest-intro TEXT`: Override a model-generated title or guest introduction.
- `--index-html`, `--rss-xml`, `--episode-html`, `--transcript-html`: Use saved official pages for an offline build.
- `--thumbnail-image FILE`: Provide a verified cover image for an offline build.
- `--transcript-url`, `--episode-url`, `--title`, `--guest`, `--episode`: Override automatic discovery for a verified exceptional case.

## Translation

The translation pipeline produces one target-language paragraph for every English source paragraph. Before packaging, it checks paragraph counts, IDs, original source text, non-empty translations, and translated chapter headings. A full episode can require many model calls on its first run; the cache in `translation/` lets later runs continue from completed work.

Review the title, names, chapter headings, and a sample of body paragraphs after building. Also confirm that the cover font renders correctly in your reading app. See the [translation guide](skills/lex-fridman-youtube-to-epub/references/translation.md) for details.

## Limits and safety boundaries

- Only full episodes that can be exactly matched to an **official transcript** in the Lex website index are supported. An unmatched URL may be a clip, an episode without a transcript, or content outside this podcast.
- If the official transcript cannot be parsed, has no text, or has ambiguous provenance, the tool stops rather than guessing or substituting another caption source.
- Email delivery is not implemented. EPUB creation never sends a file automatically; a future delivery action must have an explicit recipient and separate authorization.

## Skill directory

The distributable Codex skill is in [skills/lex-fridman-youtube-to-epub](skills/lex-fridman-youtube-to-epub/SKILL.md). Its `SKILL.md` provides agent-facing execution constraints and pre-delivery checks.
