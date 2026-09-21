#!/usr/bin/env python3
"""Build English and Chinese EPUBs from a Lex Fridman transcript page."""

import argparse
import html
import json
import os
import re
import shutil
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


@dataclass
class BookConfig:
    transcript_url: str
    youtube_id: str
    title: str
    title_zh: str
    guest: str
    guest_zh: str
    episode: str
    output_dir: Path
    slug: str
    slug_zh: str
    host_avatar: Path | None
    host_name: str
    host_name_zh: str
    host_site: str
    host_youtube: str
    guest_intro: str
    guest_intro_zh: str
    host_intro: str
    host_intro_zh: str
    podcast_name: str
    podcast_name_zh: str
    creator: str
    creator_zh: str
    series_label: str
    series_label_zh: str
    host_role: str
    host_role_zh: str
    video_url: str
    cover_backdrop_image: Path | None = None
    published: str | None = None
    target_language: str = ""
    target_language_name: str = ""
    target_slug: str = ""
    target_metadata: dict | None = None


EDITOR_CREDIT_EN = "Prepared from the public transcript, preserving its chapter and paragraph order for offline reading."
EDITOR_CREDIT_ZH = "根据公开逐字稿整理，保留原文的章节与段落顺序，便于离线阅读。"


CHAPTER_TITLE_ZH = {
    "Episode highlight": "节目亮点",
    "Programming with AI agents": "使用 AI 智能体编程",
    "How software will change": "软件将如何改变",
    "AI impact on open source": "AI 对开源的影响",
    "Building Omarchy Linux distro": "构建 Omarchy Linux 发行版",
    "Vibe coding vs agentic engineering": "氛围编程与智能体工程",
    "The end of manual programming": "手工编程的终结",
    "Advice for programmers": "给程序员的建议",
    "Surviving Internet Hate": "应对互联网恶意",
    "Programming setup for AI Agents": "AI 智能体的编程环境",
    "Obsessing about speed": "对速度的执着",
    "Voice prompting vs typing": "语音提示与键盘输入",
    "Best AI coding models": "最好的 AI 编程模型",
    "Best AI coding harnesses": "最好的 AI 编程框架",
    "AI video generation and filmmaking": "AI 视频生成与电影制作",
    "Fatherhood": "父亲身份",
    "Linux will win the desktop": "Linux 将赢得桌面端",
    "PewDiePie": "PewDiePie",
    "Future of programming": "编程的未来",
    "Politics and immigration": "政治与移民",
    "Longevity, over-optimization, and fear of death": "长寿、过度优化与对死亡的恐惧",
    "Eternal recurrence and future of human civization": "永恒轮回与人类文明的未来",
    "Introduction": "引言",
    "War and human nature": "战争与人性",
    "Israel-Hamas war": "以色列-哈马斯战争",
    "Military-Industrial Complex": "军工复合体",
    "War in Ukraine": "乌克兰战争",
    "China": "中国",
    "xAI Grok": "xAI Grok",
    "Aliens": "外星生命",
    "God": "上帝",
    "Diablo 4 and video games": "暗黑破坏神 4 与电子游戏",
    "Dystopian worlds: 1984 and Brave New World": "反乌托邦世界：1984 与美丽新世界",
    "AI and useful compute per watt": "AI 与每瓦有效算力",
    "AI regulation": "AI 监管",
    "Should AI be open-sourced?": "AI 应该开源吗？",
    "X algorithm": "X 算法",
    "2024 presidential elections": "2024 年总统大选",
    "Politics": "政治",
    "Trust": "信任",
    "Tesla’s Autopilot and Optimus robot": "Tesla 自动驾驶与 Optimus 机器人",
    "Hardships": "艰难时刻",
    "Introduction and Design": "引言与设计",
    "Autopilot Sensor Display": "Autopilot 传感器显示",
    "Data, Hardware, and Algorithms": "数据、硬件与算法",
    "Edge Cases and Navigate on Autopilot": "边缘案例与 Navigate on Autopilot",
    "Full Self-Driving Roadblocks": "全自动驾驶的障碍",
    "Safety and Supervision": "安全与监督",
    "Regulation and Autopilot Safety": "监管与 Autopilot 安全",
    "Driver Monitoring and Human Intervention": "驾驶员监控与人工介入",
    "Adversarial Examples and General Intelligence": "对抗样本与通用智能",
    "AI Love, Simulation, and AGI": "AI 之爱、模拟与 AGI",
    "Consciousness": "意识",
    "Regulation of AI Safety": "AI 安全监管",
    "Neuralink - understanding the human brain": "Neuralink：理解人脑",
    "Neuralink - expanding the capacity of the human mind": "Neuralink：扩展心智能力",
    "Neuralink - future challenges, solutions, and impact": "Neuralink：未来挑战、解决方案与影响",
    "Smart Summon": "智能召唤",
    "Tesla Autopilot and Full Self-Driving": "Tesla Autopilot 与全自动驾驶",
    "Carl Sagan and the Pale Blue Dot": "卡尔·萨根与暗淡蓝点",
    "Elon singing": "Elon 唱歌",
    "SpaceX human spaceflight": "SpaceX 载人航天",
    "Starship": "Starship",
    "Quitting is not in my nature": "放弃不在我的本性里",
    "Thinking process": "思考过程",
    "Humans on Mars": "人类登陆火星",
    "Colonizing Mars": "殖民火星",
    "Wormholes": "虫洞",
    "Forms of government on Mars": "火星上的政府形式",
    "Smart contracts": "智能合约",
    "Dogecoin": "Dogecoin",
    "Cryptocurrency and Money": "加密货币与金钱",
    "Bitcoin vs Dogecoin": "Bitcoin 与 Dogecoin",
    "Satoshi Nakamoto": "中本聪",
    "Tesla Autopilot": "Tesla Autopilot",
    "Tesla Self-Driving": "Tesla 自动驾驶",
    "Neural networks": "神经网络",
    "When will Tesla solve self-driving?": "Tesla 何时解决自动驾驶？",
    "Tesla FSD v11": "Tesla FSD v11",
    "Tesla Bot": "Tesla Bot",
    "History": "历史",
    "Putin": "普京",
    "Meme Review": "Meme 点评",
    "Stand-up comedy": "单口喜剧",
    "Rick and Morty": "Rick and Morty",
    "Advice for young people": "给年轻人的建议",
    "Love": "爱",
    "Meaning of life": "生命的意义",
    "Ranch": "牧场",
    "Space": "太空",
    "Physics": "物理学",
    "New Glenn": "New Glenn 火箭",
    "Lunar program": "登月计划",
    "Amazon": "Amazon",
    "Principles": "原则",
    "Productivity": "生产力",
    "Future of humanity": "人类的未来",
    "Opening and Endowment": "开场与捐赠基金",
    "Your Future: Character and Habits": "你的未来：品格与习惯",
    "Japan and Wonderful Businesses": "日本与优秀企业",
    "Long-Term Capital and Risk": "长期资本管理与风险",
    "Moats, Brands, and Business Quality": "护城河、品牌与企业质量",
    "See's, Disney, and Pricing Power": "See's、Disney 与定价权",
    "Quantitative and Qualitative Judgment": "定量与定性判断",
    "Coca-Cola and International Growth": "Coca-Cola 与国际增长",
    "Mistakes, Macro, and Wall Street": "错误、宏观与华尔街",
    "Berkshire, Dividends, and Holding Forever": "Berkshire、分红与长期持有",
    "Salomon, Arbitrage, and Diversification": "Salomon、套利与多元化",
    "Consumer Franchises": "消费品特许经营权",
    "Utilities, Real Estate, and Market Declines": "公用事业、房地产与市场下跌",
    "Happiness, Luck, and Life Design": "幸福、运气与人生设计",
    "1 billion views and 1 billion subscribers": "10 亿观看与 10 亿订阅者",
    "Mortality": "死亡与有限性",
    "Improving YouTube": "改进 YouTube",
    "Twitter": "Twitter",
    "Brand deals": "品牌合作",
    "Audience retention": "观众留存",
    "Hiring": "招聘",
    "Talking to the camera": "对着镜头说话",
    "Brainstorming": "头脑风暴",
    "TikTok": "TikTok",
    "Advice for beginners": "给新手的建议",
    "How to grow on YouTube": "如何在 YouTube 上增长",
    "Elon Musk and Twitter": "Elon Musk 与 Twitter",
    "10 million dollars vs 10 million subscribers": "1000 万美元与 1000 万订阅者",
    "Going to Antarctica": "去南极",
    "Process of making a video": "视频制作流程",
    "Overcoming depression": "走出抑郁",
    "Building a business": "打造一家公司",
    "MrBeast Burger and Feastables": "MrBeast Burger 与 Feastables",
    "Creating video games": "制作电子游戏",
    "Making billions of dollars": "赚取数十亿美元",
    "Money vs Happiness": "金钱与幸福",
    "Mental health": "心理健康",
    "Legacy": "遗产",
}


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str, fallback: str = "lex-podcast") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def xhtml_escape(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def load_transcript_html(config: BookConfig, transcript_html: Path | None) -> str:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    if transcript_html:
        return transcript_html.read_text(encoding="utf-8")
    html_path = config.output_dir.parent / "source" / "transcript.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    page = fetch_url(config.transcript_url).decode("utf-8")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(page, encoding="utf-8")
    return page


def parse_transcript(page: str):
    published_match = re.search(r'property="article:published_time" content="([^"]+)"', page)
    published = published_match.group(1)[:10] if published_match else None
    content_match = re.search(
        r'<div class="entry-content">(.*?)</div><!-- \.entry-content -->',
        page,
        re.S,
    )
    if not content_match:
        raise RuntimeError("Could not find Lex transcript entry-content.")

    content = content_match.group(1)
    item_pattern = re.compile(
        r'<h2 id="([^"]+)">(.*?)</h2>|<div class="ts-segment">(.*?)</div>',
        re.S,
    )
    name_pattern = re.compile(r'<span class="ts-name">(.*?)</span>', re.S)
    time_pattern = re.compile(r'<span class="ts-timestamp">\s*<a href="([^"]+)">\(([^<]+)\)</a>', re.S)
    text_pattern = re.compile(r'<span class="ts-text">(.*?)</span>', re.S)

    chapters = []
    current = None
    last_speaker = ""
    segment_index = 0
    for match in item_pattern.finditer(content):
        chapter_id, chapter_title, segment = match.groups()
        if chapter_id:
            current = {"id": chapter_id, "title": strip_tags(chapter_title), "segments": []}
            chapters.append(current)
            last_speaker = ""
            continue
        if not current or not segment:
            continue
        text_match = text_pattern.search(segment)
        if not text_match:
            continue
        time_match = time_pattern.search(segment)
        name_match = name_pattern.search(segment)
        raw_name = strip_tags(name_match.group(1)) if name_match else ""
        if raw_name:
            last_speaker = raw_name
        text = strip_tags(text_match.group(1))
        if not text:
            continue
        segment_index += 1
        current["segments"].append(
            {
                "id": f"seg-{segment_index:04d}",
                "speaker": raw_name or last_speaker or "Transcript",
                "timestamp": strip_tags(time_match.group(2)) if time_match else "",
                "href": html.unescape(time_match.group(1)) if time_match else "",
                "text": text,
            }
        )

    if not chapters:
        raise RuntimeError("No transcript chapters parsed.")
    return published, chapters


def segment_number(segment_id: str) -> int:
    match = re.search(r"(\d+)$", segment_id)
    if not match:
        raise ValueError(f"Invalid segment id: {segment_id}")
    return int(match.group(1))


def resolve_speaker_name(name: str, config: BookConfig) -> str:
    normalized = name.strip().lower()
    if normalized in {"host", "lex", "lex fridman"}:
        return config.host_name
    if normalized in {"guest", "mrbeast", "mr. beast", "jimmy", "jimmy donaldson"}:
        return config.guest
    return name.strip()


def apply_speaker_overrides(chapters, override_path: Path | None, config: BookConfig):
    if not override_path:
        return
    payload = json.loads(override_path.read_text(encoding="utf-8"))
    ranges = payload.get("ranges", [])
    segments = payload.get("segments", {})
    by_id = {segment["id"]: segment for _, segment in iter_segments(chapters)}

    for item in ranges:
        speaker = resolve_speaker_name(item["speaker"], config)
        start = segment_number(item["start"])
        end = segment_number(item.get("end", item["start"]))
        for segment in by_id.values():
            number = segment_number(segment["id"])
            if start <= number <= end:
                segment["speaker"] = speaker

    for segment_id, speaker_name in segments.items():
        if segment_id not in by_id:
            raise RuntimeError(f"Speaker override references unknown segment: {segment_id}")
        by_id[segment_id]["speaker"] = resolve_speaker_name(speaker_name, config)


def iter_segments(chapters):
    for chapter in chapters:
        for segment in chapter["segments"]:
            yield chapter, segment


def display_speaker_name(config: BookConfig, speaker: str, mode: str) -> str:
    if mode != "zh":
        return speaker
    if speaker == config.guest:
        return config.guest_zh
    if speaker == config.host_name:
        return config.host_name_zh
    return speaker


def is_placeholder_speaker(speaker: str) -> bool:
    return speaker.strip().lower() in {"", "transcript"}


def expected_translation_records(chapters):
    return [
        {
            "chapter_id": chapter["id"],
            "chapter_title": chapter["title"],
            "segment_id": segment["id"],
            "speaker": segment["speaker"],
            "timestamp": segment["timestamp"],
            "english": segment["text"],
            "translation": "",
        }
        for chapter, segment in iter_segments(chapters)
    ]


def load_translations(chapters, cache_path: Path):
    if not cache_path.exists():
        raise RuntimeError(f"Missing translation cache: {cache_path}")
    records = json.loads(cache_path.read_text(encoding="utf-8")).get("segments", [])
    expected = list(iter_segments(chapters))
    if len(records) != len(expected):
        raise RuntimeError(f"Translation cache has {len(records)} segments, expected {len(expected)}.")

    translations = {}
    for record, (chapter, segment) in zip(records, expected):
        if (
            record.get("chapter_id") != chapter["id"]
            or record.get("segment_id") != segment["id"]
            or record.get("english") != segment["text"]
        ):
            raise RuntimeError(f"Translation cache out of sync at {segment['id']}.")
        chinese = (record.get("chinese") or "").strip()
        if not chinese:
            raise RuntimeError(f"Empty Chinese translation at {segment['id']}.")
        translations[segment["id"]] = chinese
    return translations


def load_target_translations(chapters, cache_path: Path, language: str):
    if not cache_path.exists():
        raise RuntimeError(f"Missing translation cache: {cache_path}")
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    if cache.get("target_language") != language:
        raise RuntimeError(f"Translation cache language is {cache.get('target_language')!r}, expected {language!r}.")
    records = cache.get("segments", [])
    expected = list(iter_segments(chapters))
    if len(records) != len(expected):
        raise RuntimeError(f"Translation cache has {len(records)} segments, expected {len(expected)}.")
    translations = {}
    for record, (chapter, segment) in zip(records, expected):
        if (record.get("chapter_id") != chapter["id"] or
                record.get("segment_id") != segment["id"] or
                record.get("english") != segment["text"]):
            raise RuntimeError(f"Translation cache out of sync at {segment['id']}.")
        translated = (record.get("translation") or "").strip()
        if not translated:
            raise RuntimeError(f"Empty translation at {segment['id']}.")
        translations[segment["id"]] = translated
    metadata = cache.get("metadata") or {}
    if not metadata.get("title") or not metadata.get("chapter_titles"):
        raise RuntimeError("Translation cache is missing translated book metadata.")
    titles = {item.get("chapter_id"): item.get("title", "").strip() for item in metadata["chapter_titles"]}
    if any(not titles.get(chapter["id"]) for chapter in chapters):
        raise RuntimeError("Translation cache is missing one or more translated chapter titles.")
    return translations, metadata


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def xhtml_page(title: str, body: str, lang: str = "en") -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{xhtml_escape(lang)}" xml:lang="{xhtml_escape(lang)}">
<head>
  <title>{xhtml_escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="styles/book.css"/>
</head>
<body>
{body}
</body>
</html>
'''


def ensure_thumbnail(config: BookConfig) -> Path | None:
    source_thumb = config.output_dir.parent / "source" / "youtube-thumbnail.jpg"
    if source_thumb.exists() and source_thumb.stat().st_size > 1000:
        return source_thumb
    if not config.youtube_id:
        return None
    thumb = config.output_dir / f"{config.slug}.youtube-thumbnail.jpg"
    if thumb.exists() and thumb.stat().st_size > 1000:
        return thumb
    for name in ["maxresdefault", "sddefault", "hqdefault"]:
        try:
            data = fetch_url(f"https://img.youtube.com/vi/{config.youtube_id}/{name}.jpg")
            if len(data) > 1000:
                thumb.write_bytes(data)
                return thumb
        except Exception:
            continue
    return None


def font_loader(ImageFont):
    sans = [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    sans_bold = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    serif_bold = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ]
    cjk_serif = [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    def font(candidates, size):
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except Exception:
                continue
        return ImageFont.load_default()

    return sans, sans_bold, serif_bold, cjk_serif, font


def default_cover_backdrop() -> Path | None:
    return None


def is_lex_podcast(config: BookConfig) -> bool:
    return config.podcast_name.strip().lower() == "lex fridman podcast"


def default_host_avatar(config: BookConfig) -> Path | None:
    candidate = config.output_dir.parent / "assets" / "lex-fridman-avatar.jpg"
    return candidate if candidate.exists() else None


def generate_cover(config: BookConfig, thumbnail_path: Path | None, mode: str) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
    except Exception as exc:
        raise RuntimeError("Pillow is required to generate the cover PNG.") from exc

    if is_lex_podcast(config):
        return generate_lex_podcast_cover(config, thumbnail_path, mode, Image, ImageDraw, ImageFilter, ImageFont, ImageOps)

    width, height = 1600, 2560
    backdrop = config.cover_backdrop_image if config.cover_backdrop_image and config.cover_backdrop_image.exists() else default_cover_backdrop()
    if backdrop:
        img = ImageOps.fit(Image.open(backdrop).convert("RGB"), (width, height), method=Image.Resampling.LANCZOS).convert("RGBA")
    else:
        img = Image.new("RGBA", (width, height), "#07111f")
    if not backdrop and thumbnail_path and thumbnail_path.exists():
        bg = Image.open(thumbnail_path).convert("RGB")
        bg = ImageOps.fit(bg, (width, height), method=Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(34))
        img = Image.alpha_composite(bg.convert("RGBA"), Image.new("RGBA", (width, height), (3, 10, 20, 205)))

    draw = ImageDraw.Draw(img, "RGBA")
    sans, sans_bold, serif_bold, cjk_serif, font = font_loader(ImageFont)

    def shadow_text(x, y, text, fill, fnt):
        draw.text((x + 5, y + 7), text, fill=(0, 0, 0, 190), font=fnt)
        draw.text((x, y), text, fill=fill, font=fnt)

    def wrap_text(text, fnt, max_width):
        words = text.split() if " " in text else list(text)
        lines = []
        current = ""
        for word in words:
            separator = " " if " " in text else ""
            candidate = f"{current}{separator}{word}".strip()
            if current and draw.textbbox((0, 0), candidate, font=fnt)[2] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def shadow_wrapped_text(x, y, text, fill, fnt, max_width, line_height):
        for line in wrap_text(text, fnt, max_width):
            shadow_text(x, y, line, fill, fnt)
            y += line_height
        return y

    is_zh = mode == "zh"
    is_target = mode == "target"
    target = config.target_metadata or {}
    cover_guest = config.guest_zh if is_zh else config.guest
    cover_title = (target.get("title", config.title) if is_target else config.title_zh if is_zh else config.title)
    cover_title = cover_title.replace(f"{cover_guest}：", "").replace(f"{cover_guest}: ", "")
    cover_podcast = target.get("series_label", config.series_label) if is_target else config.series_label_zh if is_zh else config.series_label
    cover_host = config.host_name_zh if is_zh else config.host_name
    cover_role = target.get("host_role", config.host_role) if is_target else config.host_role_zh if is_zh else config.host_role
    published_label = target.get("labels", {}).get("published", "Published") if is_target else "发布于" if is_zh else "Published"

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    for y0 in range(height):
        alpha = int(100 * (y0 / height) ** 1.25)
        odraw.line((0, y0, width, y0), fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    gold = (210, 168, 82, 235)
    cream = (246, 239, 218, 255)
    muted = (183, 194, 196, 235)

    guest_font = font(cjk_serif if is_zh else serif_bold, 118 if is_zh else 138)
    subtitle_font = font(cjk_serif if is_zh else serif_bold, 58 if is_zh else 68)
    shadow_text(120, 150, cover_guest, cream, guest_font)
    y = shadow_wrapped_text(120, 330, cover_title, (246, 241, 226, 248), subtitle_font, 1360, 76 if is_zh else 82)
    y += 24
    draw.text((120, y), cover_podcast, fill=muted, font=font(sans_bold, 44))
    y += 86
    draw.line((120, y, 1480, y), fill=gold, width=5)

    thumb_y = 840 if y < 760 else y + 86
    if thumbnail_path and thumbnail_path.exists():
        source = Image.open(thumbnail_path).convert("RGB")
        if config.podcast_name == "Lex Fridman Podcast":
            w, h = source.size
            left, top, right, bottom = LEX_THUMBNAIL_SUBJECT_CROPS.get(
                config.youtube_id,
                (0.46, 0.02, 0.92, 0.98),
            )
            source = source.crop((int(w * left), int(h * top), int(w * right), int(h * bottom)))
            frame_w, frame_h = 820, 920
            thumb = ImageOps.fit(source, (frame_w, frame_h), method=Image.Resampling.LANCZOS, centering=(0.52, 0.45))
            x = (width - frame_w) // 2
            thumb_y = 780 if y < 700 else y + 70
        else:
            frame_w, frame_h = 1240, 698
            thumb = ImageOps.fit(source, (frame_w, frame_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            x = 180
        shadow = Image.new("RGBA", (frame_w + 76, frame_h + 76), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow, "RGBA")
        sdraw.rectangle((30, 30, frame_w + 46, frame_h + 46), fill=(0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        img.alpha_composite(shadow, (x - 38, thumb_y - 38))
        draw.rectangle((x - 18, thumb_y - 18, x + frame_w + 18, thumb_y + frame_h + 18), fill=(7, 13, 22, 220), outline=gold, width=4)
        img.alpha_composite(thumb.convert("RGBA"), (x, thumb_y))
        draw = ImageDraw.Draw(img, "RGBA")
        draw.rectangle((x, thumb_y, x + frame_w, thumb_y + frame_h), outline=(246, 232, 190, 145), width=2)

    info_y = 1910
    draw.line((120, info_y, 1480, info_y), fill=(210, 168, 82, 190), width=3)
    draw.text((120, info_y + 78), cover_host, fill=(236, 228, 207, 245), font=font(cjk_serif if is_zh else serif_bold, 48))
    draw.text((120, info_y + 154), cover_role, fill=muted, font=font(sans, 35))
    if config.published:
        draw.text((120, 2376), f"{published_label} {config.published}", fill=(199, 207, 205, 230), font=font(sans, 34))
    draw.line((120, 2430, 1480, 2430), fill=(210, 168, 82, 185), width=3)
    draw.rectangle((0, height - 12, width, height), fill=(210, 168, 82, 220))

    cover_stem = config.slug_zh if mode == "zh" else config.target_slug if mode == "target" else config.slug
    cover_suffix = "封面" if mode == "zh" else "cover"
    cover = config.output_dir / f"{cover_stem}-{cover_suffix}.png"
    img.convert("RGB").save(cover, "PNG", optimize=True)
    return cover


def generate_lex_podcast_cover(config: BookConfig, thumbnail_path: Path | None, mode: str, Image, ImageDraw, ImageFilter, ImageFont, ImageOps) -> Path:
    width, height = 1600, 2560
    img = Image.new("RGBA", (width, height), "#090f15")
    if thumbnail_path and thumbnail_path.exists():
        bg = Image.open(thumbnail_path).convert("RGB")
        bg = ImageOps.fit(bg, (width, height), method=Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(34))
        img = Image.alpha_composite(bg.convert("RGBA"), Image.new("RGBA", (width, height), (3, 10, 18, 198)))

    draw = ImageDraw.Draw(img, "RGBA")
    sans, sans_bold, serif_bold, cjk_serif, font = font_loader(ImageFont)

    def shadow_text(x, y, text, fill, fnt):
        draw.text((x + 5, y + 7), text, fill=(0, 0, 0, 190), font=fnt)
        draw.text((x, y), text, fill=fill, font=fnt)

    def wrap_text(text, fnt, max_width):
        words = text.split() if " " in text else list(text)
        lines = []
        current = ""
        for word in words:
            separator = " " if " " in text else ""
            candidate = f"{current}{separator}{word}".strip()
            if current and draw.textbbox((0, 0), candidate, font=fnt)[2] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def shadow_wrapped_text(x, y, text, fill, fnt, max_width, line_height):
        for line in wrap_text(text, fnt, max_width):
            shadow_text(x, y, line, fill, fnt)
            y += line_height
        return y

    is_zh = mode == "zh"
    is_target = mode == "target"
    target = config.target_metadata or {}
    cover_guest = config.guest_zh if is_zh else config.guest
    cover_title = target.get("title", config.title) if is_target else config.title_zh if is_zh else config.title
    cover_title = cover_title.replace(f"{cover_guest}：", "").replace(f"{cover_guest}: ", "")
    cover_podcast = target.get("series_label", config.series_label) if is_target else config.series_label_zh if is_zh else config.series_label
    cover_host = config.host_name_zh if is_zh else config.host_name
    cover_role = target.get("host_role", config.host_role) if is_target else config.host_role_zh if is_zh else config.host_role
    published_label = target.get("labels", {}).get("published", "Published") if is_target else "发布于" if is_zh else "Published"

    gold = (210, 168, 82, 226)
    pale_gold = (238, 213, 152, 238)
    cream = (246, 239, 218, 255)
    muted = (202, 207, 202, 235)
    card_fill = (13, 19, 25, 198)

    use_cjk_font = is_zh or (is_target and config.target_language.split("-")[0] in {"ja", "ko", "zh"})
    guest_font = font(cjk_serif if use_cjk_font else serif_bold, 118 if use_cjk_font else 142)
    subtitle_font = font(cjk_serif if use_cjk_font else serif_bold, 58 if use_cjk_font else 72)
    shadow_text(120, 160, cover_guest, cream, guest_font)
    y = shadow_wrapped_text(120, 340, cover_title, cream, subtitle_font, 1360, 76 if use_cjk_font else 88)
    y += 24
    draw.text((120, y), cover_podcast, fill=pale_gold, font=font(sans_bold, 52))
    y += 92
    draw.line((120, y, 1480, y), fill=gold, width=8)
    draw.line((120, y + 16, 1480, y + 16), fill=(238, 213, 152, 145), width=4)

    thumb_y = max(740, y + 70)
    if thumbnail_path and thumbnail_path.exists():
        source = Image.open(thumbnail_path).convert("RGB")
        fitted = ImageOps.contain(source, (1280, 720), method=Image.Resampling.LANCZOS)
        thumb = Image.new("RGB", (1280, 720), (8, 12, 18))
        thumb.paste(fitted, ((1280 - fitted.width) // 2, (720 - fitted.height) // 2))
        shadow = Image.new("RGBA", (1352, 792), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow, "RGBA")
        sdraw.rectangle((36, 36, 1316, 756), fill=(0, 0, 0, 165))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        img.alpha_composite(shadow, (124, thumb_y - 36))
        img.alpha_composite(thumb.convert("RGBA"), (160, thumb_y))
        draw = ImageDraw.Draw(img, "RGBA")
        draw.rectangle((160, thumb_y, 1440, thumb_y + 720), outline=(246, 232, 190, 145), width=4)
        draw.rectangle((154, thumb_y - 6, 1446, thumb_y + 726), outline=gold, width=3)

    draw.rectangle((0, 1540, width, height), fill=(7, 12, 18, 214))
    info_y = 1980
    draw.rounded_rectangle((120, info_y, 1480, 2340), radius=24, fill=card_fill, outline=(210, 168, 82, 92), width=2)
    avatar_path = config.host_avatar or default_host_avatar(config)
    if avatar_path and avatar_path.exists():
        avatar = Image.open(avatar_path).convert("RGB")
        avatar = ImageOps.fit(avatar, (210, 210), method=Image.Resampling.LANCZOS, centering=(0.5, 0.22))
        mask = Image.new("L", (210, 210), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 210, 210), fill=255)
        img.paste(avatar, (170, info_y + 54), mask)
        draw = ImageDraw.Draw(img, "RGBA")
        draw.ellipse((170, info_y + 54, 380, info_y + 264), outline=(238, 213, 152, 165), width=4)
    draw.text((430, info_y + 58), cover_host, fill=cream, font=font(sans_bold, 52))
    draw.text((430, info_y + 132), cover_role, fill=muted, font=font(sans, 34))
    links = [value.replace("https://", "").strip("/") for value in [config.host_site, config.host_youtube] if value]
    if links:
        draw.text((430, info_y + 196), "  ·  ".join(links), fill=pale_gold, font=font(sans, 32))
    if config.published:
        draw.text((120, 2410), f"{published_label} {config.published}", fill=(205, 209, 203, 230), font=font(sans, 34))
    draw.rectangle((0, height - 18, width, height), fill=(210, 168, 82, 220))
    draw.rectangle((0, height - 8, width, height), fill=(238, 213, 152, 190))

    cover_stem = config.slug_zh if mode == "zh" else config.target_slug if mode == "target" else config.slug
    cover_suffix = "封面" if mode == "zh" else "cover"
    cover = config.output_dir / f"{cover_stem}-{cover_suffix}.png"
    img.convert("RGB").save(cover, "PNG", optimize=True)
    return cover


def cover_svg(config: BookConfig, mode: str) -> str:
    is_zh = mode == "zh"
    target = config.target_metadata or {}
    podcast = target.get("series_label", config.series_label) if mode == "target" else config.series_label_zh if is_zh else config.series_label.upper()
    guest = config.guest_zh if is_zh else config.guest
    title = target.get("title", config.title) if mode == "target" else config.title_zh if is_zh else config.title.replace(config.guest + ": ", "")
    host = config.host_name_zh if is_zh else config.host_name
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2560" viewBox="0 0 1600 2560" role="img">
  <rect width="1600" height="2560" fill="#101820"/>
  <rect x="112" y="112" width="1376" height="2336" fill="none" stroke="#d2a852" stroke-width="6" opacity="0.55"/>
  <text x="160" y="284" fill="#f4f0e8" font-family="Helvetica, Arial, sans-serif" font-size="54" font-weight="600">{xhtml_escape(podcast)}</text>
  <text x="160" y="500" fill="#ffffff" font-family="Georgia, Times, serif" font-size="142" font-weight="700">{xhtml_escape(guest)}</text>
  <text x="160" y="650" fill="#ffffff" font-family="Georgia, Times, serif" font-size="76" font-weight="700">{xhtml_escape(title)}</text>
  <rect x="160" y="760" width="560" height="8" fill="#d2a852"/>
  <text x="160" y="2200" fill="#f4f0e8" font-family="Helvetica, Arial, sans-serif" font-size="46" font-weight="600">{xhtml_escape(host)}</text>
</svg>
'''


def css(mode: str) -> str:
    if mode == "zh":
        body_rule = 'body { color: #202124; font-family: "Songti SC", "STSong", "Noto Serif CJK SC", serif; line-height: 1.78; margin: 0; padding: 1.2em; }'
        text_rules = '''
.text-zh { color: #202124; font-family: "Songti SC", "STSong", "Noto Serif CJK SC", serif; font-size: 1.04em; line-height: 1.78; margin: 0; padding: 0; text-align: justify; text-indent: 2em; }
.text-zh-only { background: transparent; border-left: 0; }
'''.strip()
    else:
        body_rule = 'body { color: #202124; font-family: Georgia, "Times New Roman", serif; line-height: 1.62; margin: 0; padding: 1.2em; }'
        text_rules = '''
.text-en { hyphens: auto; line-height: 1.62; margin: 0 0 0.15em; text-align: justify; text-indent: 1.25em; }
.text-target { hyphens: auto; line-height: 1.7; margin: 0 0 0.15em; text-align: justify; text-indent: 1.25em; }
'''.strip()

    common_rules = '''
h1, h2, h3 { color: #121820; font-family: Helvetica, Arial, "PingFang SC", sans-serif; line-height: 1.15; }
h1 { font-size: 1.8em; margin: 1.2em 0 0.4em; }
h2 { font-size: 1.45em; margin: 1.5em 0 0.75em; }
a { color: #245f8f; text-decoration: none; }
.subtitle, .source-note { color: #555; font-family: Helvetica, Arial, "PingFang SC", sans-serif; }
.source-note { border-top: 1px solid #ddd; margin-top: 2em; padding-top: 1em; }
.toc li { margin: 0.45em 0; }
.segment { margin: 0 0 0.2em; padding: 0; }
.speaker { color: #101820; font-family: Helvetica, Arial, "PingFang SC", sans-serif; font-weight: 700; }
.time { color: #667; font-family: Helvetica, Arial, sans-serif; font-size: 0.86em; margin-left: 0.35em; }
.chapter-zh { color: #60717d; display: block; font-size: 0.65em; margin-top: 0.35em; }
.profile { border-top: 1px solid #ddd; margin-top: 1.4em; padding-top: 1.1em; }
.cover { margin: 0; padding: 0; text-align: center; }
.cover img { height: 100%; max-height: 100vh; max-width: 100%; width: auto; }
'''.strip()
    return "\n".join([body_rule, common_rules, text_rules])


def build_epub(config: BookConfig, chapters, translations, cover_png: Path, mode: str) -> Path:
    if mode not in {"en", "zh", "target"}:
        raise ValueError(f"Unsupported EPUB mode: {mode}")

    is_zh = mode == "zh"
    is_target = mode == "target"
    target = config.target_metadata or {}
    target_labels = target.get("labels", {})
    target_chapters = {item["chapter_id"]: item["title"] for item in target.get("chapter_titles", [])}
    lang = config.target_language if is_target else "zh-CN" if is_zh else "en"
    book_title = target.get("title", config.title) if is_target else config.title_zh if is_zh else config.title
    has_timestamps = any(segment["timestamp"] and segment["href"] for _, segment in iter_segments(chapters))
    label = target_labels.get("edition", config.target_language_name) if is_target else "中文版" if is_zh else "English Edition"
    title_subtitle = f"{target.get('series_label', config.series_label)} · {label}" if is_target else f"{config.series_label_zh} · {label}" if is_zh else f"Transcript of {config.series_label} · {label}"
    source_label = target_labels.get("source_transcript", "Source transcript") if is_target else "原始 transcript" if is_zh else "Source transcript"
    people_title = target_labels.get("people", "People") if is_target else "人物介绍" if is_zh else "People"
    site_label = target_labels.get("website", "Website") if is_target else "网站" if is_zh else "Website"
    host_intro = target.get("host_intro", config.host_intro) if is_target else config.host_intro_zh if is_zh else config.host_intro
    guest_intro = target.get("guest_intro", config.guest_intro) if is_target else config.guest_intro_zh if is_zh else config.guest_intro
    host_name = config.host_name_zh if is_zh else config.host_name
    guest_name = config.guest_zh if is_zh else config.guest
    about_title = target_labels.get("about", "About This Transcript") if is_target else "关于本书" if is_zh else "About This Transcript"
    mode_note = target_labels.get("mode_note", "This edition follows the source transcript paragraph structure.") if is_target else "本版为简体中文译文版，按原 transcript 段落结构排版。" if is_zh else "This edition contains the original English transcript, arranged by the source transcript paragraph structure."
    editor_credit = target_labels.get("editor_credit", EDITOR_CREDIT_EN) if is_target else EDITOR_CREDIT_ZH if is_zh else EDITOR_CREDIT_EN
    if has_timestamps:
        timestamp_note = target_labels.get("timestamp_note", "Timestamp links point to the original video when supported by the reader.") if is_target else "时间戳链接会在阅读器支持时跳转到原视频。" if is_zh else "Timestamp links point to the original video when supported by the reader."
    else:
        timestamp_note = target_labels.get("no_timestamp_note", "The source does not provide reliable timestamps; this book preserves paragraph order.") if is_target else "原始 PDF 未提供可靠时间戳；本书按原稿段落顺序排版。" if is_zh else "The source PDF does not provide reliable timestamps; this book preserves the source paragraph order."
    toc_title = target_labels.get("toc", "Table of Contents") if is_target else "目录" if is_zh else "Table of Contents"
    title_page_label = target_labels.get("title_page", "Title Page") if is_target else "标题页" if is_zh else "Title Page"
    published_label = target_labels.get("published", "Published") if is_target else "发布日期" if is_zh else "Published"
    published_line = f'<p>{xhtml_escape(published_label)}: {xhtml_escape(config.published)}</p>' if config.published else ""
    video_url = config.video_url or (f"https://youtube.com/watch?v={config.youtube_id}" if config.youtube_id else "")
    video_line = f'<p>Video: <a href="{xhtml_escape(video_url)}">{xhtml_escape(video_url)}</a></p>' if video_url else ""

    build_dir = config.output_dir.parent / "build" / f"{config.slug}-epub-build-{mode}"
    oebps = build_dir / "OEBPS"
    meta_inf = build_dir / "META-INF"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    oebps.mkdir(parents=True)
    meta_inf.mkdir(parents=True)
    write(build_dir / "mimetype", "application/epub+zip")
    write(meta_inf / "container.xml", '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
''')
    (oebps / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(cover_png, oebps / "images" / "cover.png")
    write(oebps / "images" / "cover.svg", cover_svg(config, mode))
    write(oebps / "styles" / "book.css", css(mode))
    write(oebps / "cover.xhtml", xhtml_page("Cover", '<div class="cover"><img src="images/cover.png" alt="Book cover"/></div>', lang))

    write(oebps / "titlepage.xhtml", xhtml_page(book_title, f'''
<section>
  <h1>{xhtml_escape(book_title)}</h1>
  <p class="subtitle">{xhtml_escape(title_subtitle)}</p>
  <p>{xhtml_escape(target.get('series_label', config.podcast_name) if is_target else config.podcast_name_zh if is_zh else config.podcast_name)}</p>
  {published_line}
  <p class="source-note">{xhtml_escape(source_label)}: <a href="{config.transcript_url}">{config.transcript_url}</a></p>
</section>
''', lang))
    host_site_line = f'<p>{xhtml_escape(site_label)}: <a href="{config.host_site}">{config.host_site}</a></p>' if config.host_site else ""
    host_youtube_line = f'<p>YouTube: <a href="{config.host_youtube}">{config.host_youtube}</a></p>' if config.host_youtube else ""
    write(oebps / "intro-people.xhtml", xhtml_page(people_title, f'''
<section>
  <h1>{xhtml_escape(people_title)}</h1>
  <div class="profile"><h2>{xhtml_escape(host_name)}</h2><p>{xhtml_escape(host_intro)}</p>{host_site_line}{host_youtube_line}</div>
  <div class="profile"><h2>{xhtml_escape(guest_name)}</h2><p>{xhtml_escape(guest_intro)}</p></div>
</section>
''', lang))
    write(oebps / "intro.xhtml", xhtml_page(about_title, f'''
<section>
  <h1>{xhtml_escape(about_title)}</h1>
  <p>{mode_note}</p>
  <p>{xhtml_escape(editor_credit)}</p>
  <p>{xhtml_escape(timestamp_note)}</p>
  {video_line}
</section>
''', lang))

    chapter_items = []
    nav_items = []
    for index, chapter in enumerate(chapters, start=1):
        filename = f"chapter-{index:02d}-{slugify(chapter['title'], str(index))}.xhtml"
        rows = []
        for segment in chapter["segments"]:
            if is_zh:
                body = f'<p class="text-zh text-zh-only">{xhtml_escape(translations[segment["id"]])}</p>'
            elif is_target:
                body = f'<p class="text-target">{xhtml_escape(translations[segment["id"]])}</p>'
            else:
                body = f'<p class="text-en">{xhtml_escape(segment["text"])}</p>'
            show_speaker = not is_placeholder_speaker(segment["speaker"])
            speaker_name = display_speaker_name(config, segment["speaker"], mode)
            if segment["timestamp"] and segment["href"]:
                time_link = f'<a class="time" href="{xhtml_escape(segment["href"])}">({xhtml_escape(segment["timestamp"])})</a>'
                if show_speaker:
                    speaker_line = f'<p><span class="speaker">{xhtml_escape(speaker_name)}</span> {time_link}</p>'
                else:
                    speaker_line = f'<p>{time_link}</p>'
            elif show_speaker:
                speaker_line = f'<p><span class="speaker">{xhtml_escape(speaker_name)}</span></p>'
            else:
                speaker_line = ""
            rows.append(f'''<div class="segment" id="{xhtml_escape(segment["id"])}">
  {speaker_line}
  {body}
</div>''')
        chapter_zh = CHAPTER_TITLE_ZH.get(chapter["title"], "")
        chapter_title = target_chapters[chapter["id"]] if is_target else chapter_zh if is_zh and chapter_zh else chapter["title"]
        heading = xhtml_escape(chapter_title)
        write(oebps / filename, xhtml_page(chapter_title, f'<section id="{xhtml_escape(chapter["id"])}"><h1>{heading}</h1>{"".join(rows)}</section>', lang))
        chapter_items.append(f'<item id="chapter{index:02d}" href="{filename}" media-type="application/xhtml+xml"/>')
        nav_label = chapter_title
        nav_items.append(f'<li><a href="{filename}">{xhtml_escape(nav_label)}</a></li>')

    nav_body = f'''<nav epub:type="toc" id="toc">
  <h1>{xhtml_escape(toc_title)}</h1>
  <ol class="toc"><li><a href="titlepage.xhtml">{xhtml_escape(title_page_label)}</a></li><li><a href="intro-people.xhtml">{xhtml_escape(people_title)}</a></li><li><a href="intro.xhtml">{xhtml_escape(about_title)}</a></li>{os.linesep.join(nav_items)}</ol>
</nav>'''
    write(oebps / "toc.xhtml", f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{xhtml_escape(lang)}" xml:lang="{xhtml_escape(lang)}"><head><title>{xhtml_escape(toc_title)}</title><link rel="stylesheet" type="text/css" href="styles/book.css"/></head><body>{nav_body}</body></html>
''')

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, config.transcript_url + '#' + mode)}"
    spine = "\n    ".join(["<itemref idref=\"cover\"/>", "<itemref idref=\"titlepage\"/>", "<itemref idref=\"intro-people\"/>", "<itemref idref=\"intro\"/>"] + [f'<itemref idref="chapter{i:02d}"/>' for i in range(1, len(chapters) + 1)])
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">{identifier}</dc:identifier><dc:title>{xhtml_escape(book_title)} · {xhtml_escape(label)}</dc:title><dc:creator>{xhtml_escape(config.creator_zh if is_zh else config.creator)}</dc:creator><dc:language>{lang}</dc:language><dc:date>{xhtml_escape(config.published or "")}</dc:date><dc:source>{config.transcript_url}</dc:source><meta property="dcterms:modified">{modified}</meta></metadata>
  <manifest><item id="nav" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/><item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/><item id="intro-people" href="intro-people.xhtml" media-type="application/xhtml+xml"/><item id="intro" href="intro.xhtml" media-type="application/xhtml+xml"/><item id="css" href="styles/book.css" media-type="text/css"/><item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/><item id="cover-svg" href="images/cover.svg" media-type="image/svg+xml"/>{os.linesep.join(chapter_items)}</manifest>
  <spine>{spine}</spine>
</package>
'''
    write(oebps / "content.opf", opf)

    output_stem = config.slug_zh if mode == "zh" else config.target_slug if is_target else config.slug
    output = config.output_dir / f"{output_stem}.epub"
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w") as zf:
        zf.write(build_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(build_dir.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            zf.write(path, path.relative_to(build_dir), compress_type=zipfile.ZIP_DEFLATED)
    return output


def validate_epub(path: Path):
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(path) as zf:
        assert zf.namelist()[0] == "mimetype"
        assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        for required in ["META-INF/container.xml", "OEBPS/content.opf", "OEBPS/toc.xhtml", "OEBPS/images/cover.png"]:
            assert required in zf.namelist(), required
        for name in zf.namelist():
            if name.endswith((".xml", ".opf", ".xhtml", ".svg")):
                ET.fromstring(zf.read(name))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript-url", required=True)
    parser.add_argument("--transcript-html", type=Path)
    parser.add_argument("--youtube-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--title-zh")
    parser.add_argument("--guest", required=True)
    parser.add_argument("--guest-zh")
    parser.add_argument("--episode", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    parser.add_argument("--slug")
    parser.add_argument("--slug-zh")
    parser.add_argument("--host-avatar", type=Path)
    parser.add_argument("--host-name", default="Lex Fridman")
    parser.add_argument("--host-name-zh", default="莱克斯·弗里德曼")
    parser.add_argument("--host-site", default="https://lexfridman.com/")
    parser.add_argument("--host-youtube", default="https://youtube.com/lexfridman")
    parser.add_argument("--host-intro", default="Lex Fridman is the host of the Lex Fridman Podcast and a researcher who conducts long-form conversations about AI, science, engineering, philosophy, and the future.")
    parser.add_argument("--host-intro-zh", default="莱克斯·弗里德曼是 Lex Fridman Podcast 的主持人和研究者，长期围绕人工智能、科学、工程、哲学以及未来展开深度访谈。")
    parser.add_argument("--podcast-name", default="Lex Fridman Podcast")
    parser.add_argument("--podcast-name-zh", default="莱克斯·弗里德曼播客")
    parser.add_argument("--creator")
    parser.add_argument("--creator-zh")
    parser.add_argument("--series-label")
    parser.add_argument("--series-label-zh")
    parser.add_argument("--host-role", default="Host · Researcher · Podcast Interview")
    parser.add_argument("--host-role-zh", default="主持人 · 研究者 · 长谈访谈")
    parser.add_argument("--video-url", default="")
    parser.add_argument("--cover-backdrop-image", type=Path)
    parser.add_argument("--guest-intro", required=True)
    parser.add_argument("--guest-intro-zh")
    parser.add_argument("--translation-cache", type=Path)
    parser.add_argument("--language", choices=("en", "zh", "both", "target"), default="en")
    parser.add_argument("--target-language", help="BCP 47 language tag for --language target")
    parser.add_argument("--target-language-name", help="Display name for --language target")
    parser.add_argument("--speaker-overrides", type=Path)
    parser.add_argument("--skip-validate", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.language == "target" and (not args.target_language or not args.translation_cache):
        raise ValueError("--language target requires --target-language and --translation-cache")
    series_label = args.series_label or f"{args.podcast_name} #{args.episode}"
    series_label_zh = args.series_label_zh or f"{args.podcast_name_zh} #{args.episode}"
    config = BookConfig(
        transcript_url=args.transcript_url,
        youtube_id=args.youtube_id,
        title=args.title,
        title_zh=args.title_zh or args.title,
        guest=args.guest,
        guest_zh=args.guest_zh or args.guest,
        episode=args.episode,
        output_dir=args.output_dir,
        slug=args.slug or slugify(args.title),
        slug_zh=args.slug_zh or f"{args.slug or slugify(args.title)}-zh",
        host_avatar=args.host_avatar,
        host_name=args.host_name,
        host_name_zh=args.host_name_zh,
        host_site=args.host_site,
        host_youtube=args.host_youtube,
        guest_intro=args.guest_intro,
        guest_intro_zh=args.guest_intro_zh or args.guest_intro,
        host_intro=args.host_intro,
        host_intro_zh=args.host_intro_zh,
        podcast_name=args.podcast_name,
        podcast_name_zh=args.podcast_name_zh,
        creator=args.creator or args.podcast_name,
        creator_zh=args.creator_zh or args.creator or args.podcast_name_zh,
        series_label=series_label,
        series_label_zh=series_label_zh,
        host_role=args.host_role,
        host_role_zh=args.host_role_zh,
        video_url=args.video_url,
        cover_backdrop_image=args.cover_backdrop_image,
        target_language=args.target_language or "",
        target_language_name=args.target_language_name or args.target_language or "",
        target_slug=f"{args.slug or slugify(args.title)}-{slugify(args.target_language)}" if args.target_language else "",
    )
    page = load_transcript_html(config, args.transcript_html)
    published, chapters = parse_transcript(page)
    apply_speaker_overrides(chapters, args.speaker_overrides, config)
    config.published = published
    cache_path = args.translation_cache or (config.output_dir / f"{config.slug}.zh.json")
    translations = load_translations(chapters, cache_path) if args.language in {"zh", "both"} else {}
    if args.language == "target":
        translations, config.target_metadata = load_target_translations(chapters, cache_path, config.target_language)
    thumbnail = ensure_thumbnail(config)
    if args.language in {"en", "both"}:
        english_cover = generate_cover(config, thumbnail, "en")
        english = build_epub(config, chapters, translations, english_cover, "en")
        if not args.skip_validate:
            validate_epub(english)
        print(f"English EPUB: {english}")
        print(f"English cover PNG: {english_cover}")
    if args.language in {"zh", "both"}:
        chinese_cover = generate_cover(config, thumbnail, "zh")
        chinese = build_epub(config, chapters, translations, chinese_cover, "zh")
        if not args.skip_validate:
            validate_epub(chinese)
        print(f"Chinese EPUB: {chinese}")
        print(f"Chinese cover PNG: {chinese_cover}")
        print(f"Translation cache: {cache_path}")
    if args.language == "target":
        target_cover = generate_cover(config, thumbnail, "target")
        target_book = build_epub(config, chapters, translations, target_cover, "target")
        if not args.skip_validate:
            validate_epub(target_book)
        print(f"{config.target_language_name} EPUB: {target_book}")
        print(f"{config.target_language_name} cover PNG: {target_cover}")
        print(f"Translation cache: {cache_path}")
    print(f"Chapters: {len(chapters)}")
    print(f"Transcript segments: {sum(len(chapter['segments']) for chapter in chapters)}")


if __name__ == "__main__":
    main()
