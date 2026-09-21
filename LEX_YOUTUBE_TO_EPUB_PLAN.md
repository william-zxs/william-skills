# Lex Fridman YouTube → EPUB skill 方案

## 目标

在 `skills/lex-fridman-youtube-to-epub/` 提供可独立分发的 Codex skill。用户给出 Lex Fridman 完整播客的 YouTube 链接或视频 ID，agent 能定位官网 transcript，并按用户指定语言生成 EPUB；未指定时保留原文英语。生成物放在用户指定的目录，不混进 skill 本身。

## 来源与匹配

1. 解析并校验 YouTube 视频 ID，拒绝任意网址及非完整播客的误匹配。
2. 从 `https://lexfridman.com/podcast` 的视频、单集、Transcript 链接关系寻找精确视频 ID；以官网单集页核对标题与 transcript 链接。RSS `https://lexfridman.com/feed/podcast/` 补充发布时间、简介和可用的单集图片信息。不能假定每个 RSS 条目都有单集图片或能独立建立 YouTube ID 与 transcript 的对应关系。
3. 下载官网 transcript HTML 并保存原始快照。只有能解析出章节和正文段落时才继续构建；缺失时报告具体缺口，不把 YouTube 自动字幕当作官网 transcript。
4. 封面优先采用对应视频的高分辨率 YouTube 缩略图；不可用时才考虑 RSS 单集图片，并记录来源。RSS 图片是素材来源，不保证适合作为竖版 EPUB 封面。

## 实现

- 复用 `podcast2epub` 已验证的 Lex transcript 解析、EPUB 打包、封面绘制与校验逻辑，但把运行所需脚本随 skill 一起发布，避免依赖兄弟仓库。
- 增加一个从 YouTube 输入发现官网来源、生成元数据清单并调用构建器的入口。原文英语直接构建；指定其他语言时用 Codex 翻译正文和书籍元数据，建立逐段对齐的缓存后构建。
- 用 Python 标准库处理发现与 RSS；图像处理依赖 Pillow。保留来源 URL、原始 HTML、缩略图、元数据和最终 EPUB 以便复核与重建。
- 对用户可提供的标题、嘉宾、简介、transcript URL 和本地源文件留覆盖入口，以处理网站结构变化；覆盖时仍校验 transcript 可解析。

## 验收

- skill frontmatter 与结构通过 `quick_validate.py`。
- 离线夹具覆盖 YouTube ID 与官网索引匹配、RSS 元数据、无匹配/歧义情况。
- 用仓库已有 Lex transcript 快照做一次英文 EPUB 构建，检查章节、正文、封面、ZIP/OPF/XML 结构；中文路径检查缓存对齐与构建能力。
- 记录网络受限时未完成的在线端到端验证，不将本地夹具结果描述为实时网站验证。

## 实施记录（2026-09-21）

- 已实现独立 skill、YouTube → 官网索引匹配、RSS 元数据补充、Transcript 快照、YouTube 缩略图及 RSS 图片回退、英文构建和可选中文构建。
- skill 结构通过 `quick_validate.py`；离线索引/RSS 夹具匹配通过。
- 使用项目现存 DHH #501 的官方 Transcript 快照与视频缩略图完成英文和中文构建：23 章、1080 段；两个 EPUB 各自包含对应语言的 1080 段，文件名不同，封面尺寸为 1600×2560；英文 EPUB 的 ZIP/XML/OPF 检查通过，构建器同时校验了两个 EPUB。
- 获得网络权限后，用 `https://www.youtube.com/watch?v=NYFGCESmikA` 完成实时端到端验证：官网索引精确匹配 `dhh-2` 单集及 `dhh-2-transcript`，RSS 匹配 #501 条目，下载实时 transcript HTML（662534 字节）及 `maxresdefault.jpg`（188407 字节），构建英文 EPUB（23 章、1080 段）。EPUB ZIP/OPF/XML、正文计数和 1600×2560 封面均通过检查，并目视确认封面。在线验证发现单集页有站点标题与文章标题两个 `h1`，已修正为读取 `entry-title`。
- 本次 RSS 条目的单集图片字段为空，因此使用 YouTube 缩略图；RSS 图片回退逻辑尚未通过真实含图片的单集验证。

## 语言参数演进（2026-09-22）

- 最初版本只支持英语和中文；随后统一为语言参数流程。未指定语言或指定英语时保留原文；指定任意其他目标语言时通过 Codex 模型翻译。常见语言名称直接识别，其余名称由模型解析为 BCP 47 标签。
- 翻译缓存统一记录目标语言、译文、书名、章节名和前言信息。旧版中文缓存可作为种子复用正文，转换后的缓存写入新文件，不修改旧缓存。
- 模型实际完成了一个法语单段 transcript 的元数据及正文翻译；通用构建路径用该缓存生成法语 EPUB。DHH #501 的旧中文缓存迁移后，通用构建路径生成 23 章、1080 段中文版；默认英语路径也完成回归。完整 1080 段的新语言全量翻译仍需在实际使用时按需运行。
