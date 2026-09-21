# Translation to a requested language

The Lex transcript is in English. Omitting `--language` or specifying English preserves the source text. Any other target language uses the same Codex translation pipeline for paragraphs, chapter headings, title, introductions, and reader-facing labels, then builds one EPUB marked with that language's BCP 47 tag.

```bash
python scripts/lex_youtube_to_epub.py 'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output --language 中文

python scripts/lex_youtube_to_epub.py 'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output --language Japanese
```

The first translation creates `translation/<slug>.<language-tag>.translation.json`; reruns resume matching completed segments. The model must preserve one translation per source paragraph. The builder checks language, segment count, IDs, exact source English, nonempty translated text, and translated chapter headings before packaging. If a legacy Chinese cache is supplied with `--translation-cache`, the command copies its matching body translations into the generic format and uses the model for missing metadata, leaving the legacy file intact.

Use `--translated-title` or `--translated-guest-intro` to override a model translation after review. The former `--title-zh` and `--guest-intro-zh` options remain aliases for Chinese. Review the resulting language, cover font rendering, proper names, chapter titles, and sampled paragraphs before delivery. A full episode can require many model calls; the cache makes interrupted runs resumable.
