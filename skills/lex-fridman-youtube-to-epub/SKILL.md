---
name: lex-fridman-youtube-to-epub
description: Turn a full Lex Fridman Podcast YouTube episode into an EPUB in its original English or a requested target language, using the official Lex transcript and Codex model translation.
---

# Lex Fridman YouTube to EPUB

Accept a full Lex Fridman Podcast YouTube link or video ID. Resolve it against the [official podcast index](https://lexfridman.com/podcast) and use the matching official transcript as the book text. With no `--language`, preserve the source English. An explicit target language uses the same pipeline: English keeps the original; any other language uses the Codex model to translate. The [podcast RSS](https://lexfridman.com/feed/podcast/) enriches metadata when the episode appears there; the YouTube thumbnail is the preferred cover image. Never infer a transcript from a similar title or silently substitute YouTube captions.

Run `scripts/lex_youtube_to_epub.py` with the input and an output directory. It writes `metadata.json`, `source/transcript.html`, one EPUB (`dist/<slug>.epub` for the original or `dist/<slug>-<language-tag>.epub` for a translation), and its cover PNG. An unmatched video, missing transcript, or unparseable transcript requires a clear report to the user. It may be a clip or an episode without an official transcript.

```bash
python scripts/lex_youtube_to_epub.py 'https://www.youtube.com/watch?v=NYFGCESmikA' --output-dir /path/to/output

python scripts/lex_youtube_to_epub.py 'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output --language French
```

Requires Python 3 and Pillow (`python -m pip install Pillow`). Translation additionally requires the Codex CLI and model access. Internet access is needed for fresh source pages and thumbnails. `--language` accepts common language names (including `中文`, `日语`, and `French`) or BCP 47 tags; the model resolves less common language names. `--transcript-url`, `--episode-url`, `--title`, `--guest`, `--episode`, `--guest-intro`, and local HTML/image inputs are available for verified exceptions or offline work; inspect the source association before overriding discovery. The script records URLs and saves the source HTML for reproducibility.

For any translated edition, read [references/translation.md](references/translation.md). The command creates or resumes an aligned translation cache with Codex; an existing cache can be supplied with `--translation-cache`. Do not create a translated EPUB by merely changing the language metadata. For script arguments, run `python scripts/lex_youtube_to_epub.py --help`.

Before delivery, confirm the metadata points to the intended video and transcript, chapter and segment counts are nonzero, the EPUB validates, and the cover visibly uses the correct episode image. Use the generated EPUB and cover paths in the response.
