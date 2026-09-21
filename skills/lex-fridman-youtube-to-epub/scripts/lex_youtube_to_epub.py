#!/usr/bin/env python3
"""Resolve a Lex Fridman YouTube episode and build an EPUB from its official transcript."""

import argparse
import html
import io
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from build_lex_podcast_epub import parse_transcript, slugify
from translate_to_language import object_schema, run_codex, string_schema


INDEX_URL = "https://lexfridman.com/podcast"
RSS_URL = "https://lexfridman.com/feed/podcast/"
SCRIPT_DIR = Path(__file__).resolve().parent


def video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urllib.parse.urlparse(value)
    host = (parsed.hostname or "").lower()
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        path = parsed.path.strip("/").split("/")
        candidate = urllib.parse.parse_qs(parsed.query).get("v", [""])[0] if path[0] == "watch" else path[1] if len(path) > 1 and path[0] in {"live", "embed"} else ""
    elif host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/")[0]
    else:
        candidate = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise ValueError("Provide a YouTube watch/live/youtu.be URL or an 11-character video ID.")
    return candidate


def read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Lex EPUB skill)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def read_source(path: Path | None, url: str) -> bytes:
    return path.read_bytes() if path else read_url(url)


def lex_url(url: str) -> str:
    result = urllib.parse.urljoin("https://lexfridman.com/", html.unescape(url))
    if urllib.parse.urlparse(result).hostname not in {"lexfridman.com", "www.lexfridman.com"}:
        return ""
    return result


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = {"href": dict(attrs).get("href", ""), "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def anchors(page: str) -> list[dict[str, str]]:
    parser = AnchorParser()
    parser.feed(page)
    return parser.links


def find_index_match(page: str, target_id: str) -> dict[str, str] | None:
    links = anchors(page)
    matches = []
    for index, link in enumerate(links):
        try:
            current_id = video_id(link["href"])
        except ValueError:
            continue
        if current_id != target_id:
            continue
        episode = ""
        transcript = ""
        for candidate in links[index + 1:index + 16]:
            try:
                next_id = video_id(candidate["href"])
            except ValueError:
                next_id = ""
            if next_id and next_id != target_id:
                break
            label = candidate["text"].strip().lower()
            url = lex_url(candidate["href"])
            if not url:
                continue
            if "transcript" in label or "-transcript" in urllib.parse.urlparse(url).path:
                transcript = url
                break
            if label == "episode" and not episode:
                episode = url
        if transcript:
            matches.append({"episode_url": episode, "transcript_url": transcript})
    unique = {(item["episode_url"], item["transcript_url"]) for item in matches}
    if len(unique) > 1:
        raise RuntimeError(f"Official index has ambiguous matches for video {target_id}: {sorted(unique)}")
    return matches[0] if matches else None


def strip_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def rss_items(data: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item"):
        image = item.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
        items.append({
            "title": item.findtext("title", ""),
            "episode_url": item.findtext("link", "").strip(),
            "description": strip_markup(item.findtext("description", "")),
            "published": item.findtext("pubDate", ""),
            "image_url": image.get("href", "") if image is not None else "",
            "raw_description": item.findtext("description", ""),
        })
    return items


def find_rss_match(items: list[dict[str, str]], episode_url: str, target_id: str) -> dict[str, str] | None:
    target_path = urllib.parse.urlparse(episode_url).path.rstrip("/")
    for item in items:
        item_path = urllib.parse.urlparse(item["episode_url"]).path.rstrip("/")
        if target_path and item_path == target_path:
            return item
    for item in items:
        if target_id in item["raw_description"]:
            return item
    return None


def episode_metadata(page: str) -> tuple[str, str]:
    title_match = re.search(r'<h1\b[^>]*class=["\'][^"\']*\bentry-title\b[^"\']*["\'][^>]*>(.*?)</h1>', page, re.I | re.S)
    title = strip_markup(title_match.group(1)) if title_match else ""
    transcript = ""
    for link in anchors(page):
        url = lex_url(link["href"])
        if url and ("transcript" in link["text"].lower() or "-transcript" in urllib.parse.urlparse(url).path):
            transcript = url
            break
    return title, transcript


def clean_title(raw: str) -> tuple[str, str, str]:
    raw = re.sub(r"\s*\|\s*Lex Fridman Podcast.*$", "", raw, flags=re.I).strip()
    match = re.match(r"^#?(\d+)\s*[–—-]\s*(.+)$", raw)
    number, title = (match.group(1), match.group(2)) if match else ("", raw)
    guest = title.split(":", 1)[0].strip() if ":" in title else ""
    return title, guest, number


def language_spec(value: str) -> tuple[str, str]:
    known = {
        "en": ("en", "English"), "english": ("en", "English"), "英语": ("en", "English"), "英文": ("en", "English"),
        "zh": ("zh", "Simplified Chinese"), "zh-cn": ("zh", "Simplified Chinese"), "chinese": ("zh", "Simplified Chinese"), "中文": ("zh", "Simplified Chinese"), "简体中文": ("zh", "Simplified Chinese"),
        "fr": ("fr", "French"), "french": ("fr", "French"), "法语": ("fr", "French"),
        "de": ("de", "German"), "german": ("de", "German"), "德语": ("de", "German"),
        "es": ("es", "Spanish"), "spanish": ("es", "Spanish"), "西班牙语": ("es", "Spanish"),
        "ja": ("ja", "Japanese"), "japanese": ("ja", "Japanese"), "日语": ("ja", "Japanese"), "日本語": ("ja", "Japanese"),
        "ko": ("ko", "Korean"), "korean": ("ko", "Korean"), "韩语": ("ko", "Korean"), "한국어": ("ko", "Korean"),
        "pt": ("pt", "Portuguese"), "portuguese": ("pt", "Portuguese"), "葡萄牙语": ("pt", "Portuguese"),
        "it": ("it", "Italian"), "italian": ("it", "Italian"), "意大利语": ("it", "Italian"),
        "ru": ("ru", "Russian"), "russian": ("ru", "Russian"), "俄语": ("ru", "Russian"),
        "ar": ("ar", "Arabic"), "arabic": ("ar", "Arabic"), "阿拉伯语": ("ar", "Arabic"),
        "hi": ("hi", "Hindi"), "hindi": ("hi", "Hindi"), "印地语": ("hi", "Hindi"),
    }
    requested = value.strip()
    if not requested:
        raise ValueError("--language must name a target language.")
    if requested.lower() in known:
        return known[requested.lower()]
    if re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", requested, re.I):
        tag = requested.lower()
        return tag, known.get(tag, (tag, requested))[1]
    if not shutil.which("codex"):
        raise RuntimeError("Resolving this language name requires the Codex CLI. Use a BCP 47 language tag instead.")
    schema = object_schema({"tag": string_schema(), "name": string_schema()})
    result = run_codex(
        f"Identify the target language named {requested!r}. Return its BCP 47 language tag and English language name as JSON. "
        "Reject non-language requests by returning empty strings. Do not translate any content.",
        schema, None,
    )
    tag = result["tag"].strip()
    name = result["name"].strip()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", tag, re.I) or not name:
        raise ValueError(f"Could not resolve target language: {requested}")
    return tag.lower(), name


def save_cover_image(source: Path, target_id: str, supplied: Path | None, rss_image_url: str) -> str:
    from PIL import Image

    candidates = [str(supplied)] if supplied else [
        f"https://img.youtube.com/vi/{target_id}/{size}.jpg"
        for size in ("maxresdefault", "sddefault", "hqdefault")
    ] + ([rss_image_url] if rss_image_url else [])
    for url in candidates:
        try:
            data = supplied.read_bytes() if supplied else read_url(url)
            with Image.open(io.BytesIO(data)) as image:
                if min(image.size) < 360:
                    continue
                image.convert("RGB").save(source / "youtube-thumbnail.jpg", "JPEG", quality=93)
                return url
        except (OSError, ValueError):
            continue
    raise RuntimeError("No usable YouTube thumbnail or RSS episode image found. Supply --thumbnail-image after checking it belongs to this episode.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("youtube", help="Full Lex episode YouTube URL or video ID")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--language", default="en", metavar="LANGUAGE", help="Target language name or BCP 47 tag; default en. Non-English languages use Codex translation.")
    parser.add_argument("--index-html", type=Path, help="Saved official podcast index HTML")
    parser.add_argument("--rss-xml", type=Path, help="Saved podcast RSS XML")
    parser.add_argument("--episode-html", type=Path, help="Saved official episode HTML")
    parser.add_argument("--transcript-html", type=Path, help="Saved official transcript HTML")
    parser.add_argument("--thumbnail-image", type=Path, help="Saved thumbnail image for offline builds")
    parser.add_argument("--transcript-url", help="Official Lex transcript URL override")
    parser.add_argument("--episode-url", help="Official Lex episode URL override")
    parser.add_argument("--title", help="Book title override")
    parser.add_argument("--guest", help="Guest name override")
    parser.add_argument("--guest-intro", help="Factual one-sentence guest introduction")
    parser.add_argument("--episode", help="Episode number override")
    parser.add_argument("--translation-cache", type=Path, help="Existing aligned translation cache for the requested language")
    parser.add_argument("--translated-title", help="Override the model-translated book title")
    parser.add_argument("--translated-guest-intro", help="Override the model-translated guest introduction")
    parser.add_argument("--title-zh")
    parser.add_argument("--guest-intro-zh")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    language_tag, language_name = language_spec(args.language)
    if language_tag == "en" and args.translation_cache:
        parser.error("--translation-cache requires a non-English --language")

    target_id = video_id(args.youtube)
    index_match = None
    if not args.transcript_url:
        index_page = read_source(args.index_html, INDEX_URL).decode("utf-8")
        index_match = find_index_match(index_page, target_id)
        if not index_match:
            raise RuntimeError(f"Video {target_id} was not found with a transcript in the official podcast index. Supply --transcript-url only after verifying the episode manually.")
    episode_url = args.episode_url or (index_match or {}).get("episode_url", "")
    transcript_url = args.transcript_url or (index_match or {}).get("transcript_url", "")
    if not lex_url(transcript_url) or (episode_url and not lex_url(episode_url)):
        raise ValueError("Episode and transcript URLs must be on lexfridman.com")

    rss_match = None
    try:
        rss_match = find_rss_match(rss_items(read_source(args.rss_xml, RSS_URL)), episode_url, target_id)
    except (OSError, ET.ParseError) as exc:
        print(f"RSS metadata unavailable: {exc}", file=sys.stderr)

    official_title = ""
    if episode_url or args.episode_html:
        try:
            episode_page = read_source(args.episode_html, episode_url).decode("utf-8")
            official_title, episode_transcript = episode_metadata(episode_page)
            if episode_transcript and urllib.parse.urlparse(episode_transcript).path.rstrip("/") != urllib.parse.urlparse(transcript_url).path.rstrip("/"):
                raise RuntimeError("Podcast index and episode page disagree about the transcript URL.")
        except OSError as exc:
            print(f"Episode page metadata unavailable: {exc}", file=sys.stderr)
    title, guest, number = clean_title(args.title or official_title or (rss_match or {}).get("title", ""))
    guest = args.guest or guest
    number = args.episode or number
    if not title:
        raise RuntimeError("No official title found; supply --title.")
    if not guest:
        raise RuntimeError("Guest could not be identified from the title; supply --guest.")

    output = args.output_dir.resolve()
    source = output / "source"
    dist = output / "dist"
    source.mkdir(parents=True, exist_ok=True)
    transcript_data = read_source(args.transcript_html, transcript_url)
    transcript_path = source / "transcript.html"
    transcript_path.write_bytes(transcript_data)
    published, chapters = parse_transcript(transcript_data.decode("utf-8"))
    segments = sum(len(chapter["segments"]) for chapter in chapters)
    if segments == 0:
        raise RuntimeError("Official transcript has no parsed text segments.")

    slug = slugify(f"lex-{number}-{title}" if number else f"lex-{title}")
    metadata = {
        "youtube_url": f"https://www.youtube.com/watch?v={target_id}",
        "youtube_id": target_id,
        "episode_url": episode_url,
        "transcript_url": transcript_url,
        "rss_url": RSS_URL,
        "rss_episode_found": bool(rss_match),
        "rss_image_url": (rss_match or {}).get("image_url", ""),
        "cover_source": "",
        "published": published or (rss_match or {}).get("published", ""),
        "title": title,
        "guest": guest,
        "episode": number,
        "chapters": len(chapters),
        "segments": segments,
        "slug": slug,
        "language": language_tag,
        "language_name": language_name,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.metadata_only:
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return

    metadata["cover_source"] = save_cover_image(source, target_id, args.thumbnail_image, metadata["rss_image_url"])
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    guest_intro = args.guest_intro or f"{guest} is the guest in this episode of the Lex Fridman Podcast."
    command = [
        sys.executable, str(SCRIPT_DIR / "build_lex_podcast_epub.py"),
        "--transcript-url", transcript_url,
        "--transcript-html", str(transcript_path),
        "--youtube-id", target_id,
        "--video-url", metadata["youtube_url"],
        "--title", title,
        "--guest", guest,
        "--episode", number or "?",
        "--guest-intro", guest_intro,
        "--output-dir", str(dist),
        "--slug", slug,
    ]
    if language_tag != "en":
        command.extend(["--language", "target", "--target-language", language_tag, "--target-language-name", language_name])
        default_cache = output / "translation" / f"{slug}.{language_tag}.translation.json"
        cache_path = args.translation_cache or default_cache
        seed_cache = None
        if language_tag == "zh":
            old_default = output / "translation" / f"{slug}.zh.json"
            if not args.translation_cache and old_default.exists() and not cache_path.exists():
                seed_cache = old_default
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if language_tag == "zh" and cached.get("segments") and "chinese" in cached["segments"][0]:
                seed_cache = cache_path
                cache_path = default_cache
        translation_command = [
            sys.executable, str(SCRIPT_DIR / "translate_to_language.py"),
            "--transcript-url", transcript_url,
            "--transcript-html", str(transcript_path),
            "--output-cache", str(cache_path),
            "--language-tag", language_tag,
            "--language-name", language_name,
            "--title", title,
            "--host-intro", "Lex Fridman hosts long-form conversations about science, technology, history, philosophy, and the human condition.",
            "--guest-intro", guest_intro,
            "--series-label", f"Lex Fridman Podcast #{number}" if number else "Lex Fridman Podcast",
            "--host-role", "Host · Researcher · Podcast Interview",
        ]
        if seed_cache:
            translation_command.extend(["--seed-cache", str(seed_cache)])
        translated_title = args.translated_title or (args.title_zh if language_tag == "zh" else None)
        translated_intro = args.translated_guest_intro or (args.guest_intro_zh if language_tag == "zh" else None)
        if translated_title:
            translation_command.extend(["--target-title", translated_title])
        if translated_intro:
            translation_command.extend(["--target-guest-intro", translated_intro])
        subprocess.run(translation_command, check=True)
        command.extend(["--translation-cache", str(cache_path)])
    else:
        command.extend(["--language", "en"])
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
