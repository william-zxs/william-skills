#!/usr/bin/env python3
"""Translate a Lex transcript and book metadata to a requested language with Codex."""

import argparse
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from build_lex_podcast_epub import expected_translation_records, parse_transcript


def chunks(items: list[dict], max_chars: int):
    batch = []
    batch_chars = 0
    for item in items:
        size = sum(len(str(value)) for value in item.values()) + 80
        if batch and batch_chars + size > max_chars:
            yield batch
            batch = []
            batch_chars = 0
        batch.append(item)
        batch_chars += size
    if batch:
        yield batch


LABELS = {
    "edition": "Translated Edition",
    "source_transcript": "Source transcript",
    "people": "People",
    "website": "Website",
    "about": "About This Transcript",
    "mode_note": "This edition translates the original transcript and preserves its paragraph order.",
    "editor_credit": "Prepared from the public transcript for offline reading.",
    "timestamp_note": "Timestamp links point to the original video when supported by the reader.",
    "no_timestamp_note": "The source does not provide reliable timestamps; this book preserves paragraph order.",
    "toc": "Table of Contents",
    "title_page": "Title Page",
    "published": "Published",
}


def string_schema() -> dict:
    return {"type": "string"}


def object_schema(properties: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def metadata_schema() -> dict:
    chapter = object_schema({"chapter_id": string_schema(), "title": string_schema()})
    return object_schema({
        "title": string_schema(),
        "host_intro": string_schema(),
        "guest_intro": string_schema(),
        "series_label": string_schema(),
        "host_role": string_schema(),
        "labels": object_schema({key: string_schema() for key in LABELS}),
        "chapter_titles": {"type": "array", "items": chapter},
    })


def batch_schema() -> dict:
    item = object_schema({"segment_id": string_schema(), "translation": string_schema()})
    return object_schema({"translations": {"type": "array", "items": item}})


def run_codex(prompt: str, schema: dict, model: str | None) -> dict:
    with tempfile.TemporaryDirectory() as temporary:
        schema_path = Path(temporary) / "schema.json"
        output_path = Path(temporary) / "response.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        command = [
            "codex", "-c", 'model_reasoning_effort="low"', "--ask-for-approval", "never",
            "exec", "--ephemeral", "--skip-git-repo-check", "-s", "read-only",
            "--output-schema", str(schema_path), "-o", str(output_path),
        ]
        if model:
            command.extend(["-m", model])
        command.append("-")
        try:
            result = subprocess.run(command, input=prompt, text=True, capture_output=True)
        except FileNotFoundError as exc:
            raise RuntimeError("Codex CLI is required to translate this language or complete the cache.") from exc
        if result.returncode:
            raise RuntimeError(f"Codex translation failed: {result.stderr[-3000:] or result.stdout[-3000:]}")
        return json.loads(output_path.read_text(encoding="utf-8"))


def translate_metadata(args, chapters) -> dict:
    source = {
        "title": args.title,
        "host_intro": args.host_intro,
        "guest_intro": args.guest_intro,
        "series_label": args.series_label,
        "host_role": args.host_role,
        "labels": LABELS,
        "chapter_titles": [{"chapter_id": chapter["id"], "title": chapter["title"]} for chapter in chapters],
    }
    prompt = (
        f"Translate this book metadata from English into {args.language_name} ({args.language_tag}). "
        "Keep the JSON keys, chapter_id values, proper names, and factual meaning unchanged. "
        "Translate every user-visible string naturally for readers of the target language. "
        "Return only JSON matching the provided schema.\n\n"
        + json.dumps(source, ensure_ascii=False)
    )
    metadata = run_codex(prompt, metadata_schema(), args.model)
    expected_ids = [chapter["id"] for chapter in chapters]
    actual_ids = [item.get("chapter_id") for item in metadata["chapter_titles"]]
    if actual_ids != expected_ids:
        raise RuntimeError("Translated chapter headings do not match the source chapter IDs.")
    for key in ("title", "host_intro", "guest_intro", "series_label", "host_role"):
        if not metadata.get(key, "").strip():
            raise RuntimeError(f"Empty translated metadata field: {key}")
    for key in LABELS:
        if not metadata["labels"].get(key, "").strip():
            raise RuntimeError(f"Empty translated label: {key}")
    if any(not item.get("title", "").strip() for item in metadata["chapter_titles"]):
        raise RuntimeError("Empty translated chapter title.")
    return metadata


def translate_batch(args, batch: list[dict]) -> list[dict]:
    source = [
        {key: item[key] for key in ("chapter_id", "chapter_title", "segment_id", "speaker", "timestamp", "english")}
        for item in batch
    ]
    prompt = (
        f"Translate these Lex Fridman Podcast transcript paragraphs from English into {args.language_name} ({args.language_tag}).\n"
        "Translate faithfully and naturally, paragraph by paragraph. Do not summarize, omit, merge, or add commentary. "
        "Keep proper names and technical terms accurate. Preserve quoted meaning and numbers. "
        "Return exactly one nonempty translation for each segment_id, in the same order, as JSON matching the schema.\n\n"
        + json.dumps(source, ensure_ascii=False)
    )
    result = run_codex(prompt, batch_schema(), args.model)["translations"]
    if [item.get("segment_id") for item in result] != [item["segment_id"] for item in batch]:
        raise RuntimeError("Translated segment IDs are missing or out of order.")
    if any(not item.get("translation", "").strip() for item in result):
        raise RuntimeError("A translated transcript segment is empty.")
    return result


def write_cache(cache: dict, path: Path) -> None:
    cache["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript-url", required=True)
    parser.add_argument("--transcript-html", type=Path, required=True)
    parser.add_argument("--output-cache", type=Path, required=True)
    parser.add_argument("--seed-cache", type=Path, help="Existing cache to reuse matching translated segments")
    parser.add_argument("--language-tag", required=True)
    parser.add_argument("--language-name", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--target-title")
    parser.add_argument("--host-intro", required=True)
    parser.add_argument("--guest-intro", required=True)
    parser.add_argument("--target-guest-intro")
    parser.add_argument("--series-label", required=True)
    parser.add_argument("--host-role", required=True)
    parser.add_argument("--batch-chars", type=int, default=20000)
    parser.add_argument("--model")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", args.language_tag):
        parser.error("--language-tag must be a BCP 47 language tag")
    _, chapters = parse_transcript(args.transcript_html.read_text(encoding="utf-8"))
    expected = expected_translation_records(chapters)
    cache = {
        "source_url": args.transcript_url,
        "source_title": args.title,
        "target_language": args.language_tag,
        "target_language_name": args.language_name,
        "translation_engine": "codex-model",
        "metadata": None,
        "segments": expected,
    }
    for prior_path in (args.seed_cache, args.output_cache):
        if prior_path is None or not prior_path.exists():
            continue
        old = json.loads(prior_path.read_text(encoding="utf-8"))
        old_language = old.get("target_language", "").lower()
        if old_language != args.language_tag.lower() and not (args.language_tag == "zh" and old_language == "zh-cn"):
            raise RuntimeError(f"Cache {prior_path} belongs to a different target language.")
        if prior_path == args.output_cache and old.get("source_url") != args.transcript_url:
            raise RuntimeError("Existing cache belongs to a different source transcript.")
        if old.get("source_title") == args.title:
            cache["metadata"] = old.get("metadata") or cache["metadata"]
        old_segments = {item.get("segment_id"): item for item in old.get("segments", [])}
        for item in expected:
            prior = old_segments.get(item["segment_id"])
            if prior and prior.get("english") == item["english"]:
                item["translation"] = prior.get("translation") or (prior.get("chinese") if args.language_tag == "zh" else "") or item["translation"]
    if not cache["metadata"]:
        cache["metadata"] = translate_metadata(args, chapters)
        write_cache(cache, args.output_cache)
    if args.target_title:
        cache["metadata"]["title"] = args.target_title
    if args.target_guest_intro:
        cache["metadata"]["guest_intro"] = args.target_guest_intro
    pending = [item for item in expected if not item["translation"].strip()]
    for batch in chunks(pending, args.batch_chars):
        results = translate_batch(args, batch)
        for item, result in zip(batch, results):
            item["translation"] = result["translation"].strip()
        write_cache(cache, args.output_cache)
        print(f"Translated {len(expected) - sum(not item['translation'] for item in expected)}/{len(expected)} segments", flush=True)
    write_cache(cache, args.output_cache)
    print(f"Wrote {args.output_cache}")


if __name__ == "__main__":
    main()
