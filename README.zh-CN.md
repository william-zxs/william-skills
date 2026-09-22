# Lex Fridman YouTube → EPUB

[English](README.md)

将完整的 Lex Fridman Podcast YouTube 视频转换为 EPUB。工具会在 [Lex Fridman Podcast 官网](https://lexfridman.com/podcast) 精确匹配该视频，并使用对应的**官方逐字稿**作为书籍正文；不会用 YouTube 自动字幕替代。

默认生成英文原文 EPUB；指定目标语言后，会通过 Codex 翻译标题、章节、正文和书籍说明，再生成对应语言的 EPUB。

## 功能

- 支持 YouTube 视频链接或 11 位视频 ID。
- 从官网播客索引定位单集和 Transcript，并从 RSS 补充发布日期、简介等元数据。
- 优先使用对应 YouTube 视频的缩略图作为封面；无可用缩略图时回退到 RSS 单集图片。
- 保存原始逐字稿、来源 URL、元数据和封面，便于复核与重建。
- 支持英文原文及任意目标语言的翻译版；翻译缓存可在中断后续跑。
- 在构建时校验逐字稿解析结果和 EPUB 内容结构。

## 前置条件

- Python 3
- Pillow：`python3 -m pip install Pillow`
- 网络访问：首次在线构建需要访问 Lex 官网、RSS 和 YouTube 缩略图
- Codex CLI 及模型访问权限：仅翻译到非英语语言时需要

## 通过 Agent 安装

通过 GitHub 为 Codex 安装此 skill：

```bash
npx skills add william-zxs/william-skills \
  --skill lex-fridman-youtube-to-epub \
  --agent codex
```

上述命令安装到当前项目；若希望所有 Codex 项目都可使用，请附加 `--global`：

```bash
npx skills add william-zxs/william-skills \
  --skill lex-fridman-youtube-to-epub \
  --agent codex --global
```

## 给 Agent 的任务信息

复制下面这段文字给 Agent，并替换方括号中的内容：

```text
请使用 lex-fridman-youtube-to-epub skill，将 [Lex Fridman Podcast YouTube 链接或 11 位视频 ID] 转换为 [目标语言；如不翻译则填英文] EPUB，并将所有生成文件写入 [输出目录]。请使用精确匹配的 Lex 官方 Transcript 和对应封面，交付前核对两者，然后报告 EPUB 路径；不要发送邮件。
```

例如，将方括号内容替换为 `https://www.youtube.com/watch?v=NYFGCESmikA`、`简体中文` 和 `/path/to/output`。若视频无法精确匹配官方逐字稿，skill 会停止并报错，不会替换为 YouTube 字幕。

## 快速开始

从仓库根目录运行：

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  'https://www.youtube.com/watch?v=NYFGCESmikA' \
  --output-dir /path/to/output
```

也可以直接传入视频 ID：

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py \
  NYFGCESmikA \
  --output-dir /path/to/output
```

翻译为中文、法语或日语：

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

`--language` 支持常见语言名称（如 `中文`、`日语`、`French`）和 BCP 47 标签（如 `zh`、`fr`、`ja`）。省略该参数或传入 `en` / `English` 时保留英文原文。

## 输出内容

每次构建会写入指定的输出目录：

```text
output/
├── metadata.json                    # 视频、逐字稿、语言、章节数等可追溯元数据
├── source/
│   ├── transcript.html              # 官网逐字稿快照
│   └── youtube-thumbnail.jpg        # 实际使用的封面来源图
├── translation/                     # 非英文构建的可续跑翻译缓存
└── dist/
    └── lex-<episode>-<title>[-<language>].epub
```

英文 EPUB 采用基础文件名；翻译版会附带语言标签。`metadata.json` 中记录了封面、YouTube、单集页和 Transcript 的来源地址。

## 常用参数

```bash
python3 skills/lex-fridman-youtube-to-epub/scripts/lex_youtube_to_epub.py --help
```

- `--metadata-only`：只解析并写入元数据及官方逐字稿快照，不下载封面或生成 EPUB。
- `--translation-cache FILE`：为翻译版指定已有的对齐缓存，适合复用或恢复构建。
- `--translated-title TEXT`、`--translated-guest-intro TEXT`：覆盖模型生成的书名或嘉宾简介。
- `--index-html`、`--rss-xml`、`--episode-html`、`--transcript-html`：使用已保存的官方页面进行离线构建。
- `--thumbnail-image FILE`：离线构建时提供已核实属于该视频的封面图片。
- `--transcript-url`、`--episode-url`、`--title`、`--guest`、`--episode`：在已核对来源的例外情况下覆盖自动发现的元数据。

## 翻译说明

翻译任务会为每段英文正文生成一段对应译文，并校验段落数量、ID、原文和译文不为空后才会打包。首次处理一整期节目可能需要较多模型调用；缓存位于 `translation/`，再次运行同一语言会继续使用已完成的内容。

生成后建议抽查书名、人名、章节标题和若干正文段落，并确认阅读器中的封面字体显示正常。详见 [翻译说明](skills/lex-fridman-youtube-to-epub/references/translation.md)。

## 限制与安全边界

- 仅支持能在 Lex 官网索引中精确匹配到**官方 Transcript** 的完整节目。匹配不到的链接可能是片段、尚未发布逐字稿的节目，或不属于该播客。
- 不能解析官方逐字稿、逐字稿为空或来源存在歧义时，工具会报错而不会猜测或替换为其他字幕。
- 邮件发送目前未实现；构建 EPUB 不会自动发送文件。后续投递需要明确的收件人和单独授权。

## Skill 目录

可供 Codex 安装或引用的 skill 位于 [skills/lex-fridman-youtube-to-epub](skills/lex-fridman-youtube-to-epub/SKILL.md)。其中的 `SKILL.md` 包含面向 Agent 的执行约束及交付前检查要求。
