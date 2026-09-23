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
请使用 lex-fridman-youtube-to-epub skill。
视频：[Lex Fridman Podcast YouTube 链接或 11 位视频 ID]
目标语言：[目标语言；如不翻译则填英文]
请使用精确匹配的 Lex 官方 Transcript 和对应封面；交付前核对两者，然后报告 EPUB 路径。
```

例如，将方括号内容替换为 `https://www.youtube.com/watch?v=NYFGCESmikA` 和 `简体中文`。若视频无法精确匹配官方逐字稿，skill 会停止并报错，不会替换为 YouTube 字幕。
