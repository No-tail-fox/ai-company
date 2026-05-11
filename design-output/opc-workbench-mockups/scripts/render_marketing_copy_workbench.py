# -*- coding: utf-8 -*-
"""Render the Chinese marketing copy workbench concept mockup as a PNG."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 2048
HEIGHT = 1152
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "15-marketing-copy-workbench.png"
FONT_DIR = Path(r"C:\Windows\Fonts")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


FONTS = {
    "logo": load_font("msyhbd.ttc", 42),
    "tab": load_font("msyhbd.ttc", 20),
    "h1": load_font("msyhbd.ttc", 34),
    "h2": load_font("msyhbd.ttc", 24),
    "h3": load_font("msyhbd.ttc", 20),
    "body": load_font("msyh.ttc", 18),
    "small": load_font("msyh.ttc", 15),
    "tiny": load_font("msyh.ttc", 13),
    "bold": load_font("msyhbd.ttc", 18),
    "bold20": load_font("msyhbd.ttc", 20),
    "bold16": load_font("msyhbd.ttc", 16),
}

COLORS = {
    "bg": "#f6f8fc",
    "bar": "#f7f8fb",
    "line": "#dde3ee",
    "line2": "#e8ecf4",
    "text": "#101827",
    "muted": "#667085",
    "muted2": "#8a93a5",
    "purple": "#6657f5",
    "purple_light": "#f0edff",
    "red": "#ff2f3d",
    "orange": "#ff6a4d",
    "gold": "#f2a900",
    "navy": "#172154",
    "green": "#1bbf83",
    "white": "#ffffff",
    "soft": "#fbfcff",
}


image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg"])
draw = ImageDraw.Draw(image)


def rounded(x: int, y: int, w: int, h: int, radius: int = 8, fill: str = "white", outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)


def line(points: list[tuple[int, int]], fill: str, width: int = 2) -> None:
    draw.line(points, fill=fill, width=width, joint="curve")


def text(x: float, y: float, value: str, font_key: str = "body", fill: str | None = None, anchor: str | None = None) -> None:
    draw.text((x, y), value, font=FONTS[font_key], fill=fill or COLORS["text"], anchor=anchor)


def text_size(value: str, font_key: str = "body") -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), value, font=FONTS[font_key])
    return right - left, bottom - top


def ellipsize(value: str, max_width: int, font_key: str = "body") -> str:
    if text_size(value, font_key)[0] <= max_width:
        return value
    result = value
    while result and text_size(result + "…", font_key)[0] > max_width:
        result = result[:-1]
    return result + "…"


def wrap_by_width(value: str, max_width: int, font_key: str = "body", max_lines: int = 3) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in value:
        candidate = current + char
        if text_size(candidate, font_key)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines:
        lines[-1] = ellipsize(lines[-1], max_width, font_key)
    return lines[:max_lines]


def chip(x: int, y: int, label: str, fill: str = "#f0edff", color: str = "#6657f5", outline: str | None = None, font_key: str = "small", pad: int = 12) -> int:
    width, _ = text_size(label, font_key)
    rounded(x, y, width + pad * 2, 30, 15, fill=fill, outline=outline)
    text(x + pad, y + 5, label, font_key, color)
    return width + pad * 2


def button(x: int, y: int, w: int, h: int, label: str, fill: str = "white", color: str | None = None, outline: str | None = None, font_key: str = "bold16") -> None:
    rounded(x, y, w, h, 8, fill=fill, outline=outline or ("#cfc8ff" if fill == "white" else None))
    tw, th = text_size(label, font_key)
    text(x + w / 2 - tw / 2, y + h / 2 - th / 2 - 2, label, font_key, color or (COLORS["white"] if fill != "white" else COLORS["purple"]))


def field(x: int, y: int, w: int, label: str, value: str = "", h: int = 72, multiline: bool = False) -> None:
    text(x, y, label, "small", COLORS["muted"])
    rounded(x, y + 24, w, h - 24, 8, COLORS["soft"], COLORS["line"])
    if multiline:
        cursor_y = y + 38
        for line_text in wrap_by_width(value, w - 28, "body", 3):
            text(x + 14, cursor_y, line_text, "body", COLORS["text"])
            cursor_y += 25
    else:
        text(x + 14, y + 39, ellipsize(value, w - 28, "body"), "body", COLORS["text"])


def icon_tile(x: int, y: int, kind: str = "pen", fill: str = "#f0edff", color: str = "#6657f5", size: int = 44) -> None:
    rounded(x, y, size, size, 8, fill=fill)
    cx = int(x + size / 2)
    cy = int(y + size / 2)
    if kind == "pen":
        line([(cx - 10, cy + 9), (cx + 8, cy - 9)], color, 4)
        line([(cx - 13, cy + 12), (cx - 4, cy + 9)], color, 3)
        draw.ellipse([cx + 5, cy - 13, cx + 13, cy - 5], outline=color, width=3)
    elif kind == "spark":
        line([(cx, cy - 13), (cx, cy + 13)], color, 3)
        line([(cx - 13, cy), (cx + 13, cy)], color, 3)
        line([(cx - 8, cy - 8), (cx + 8, cy + 8)], color, 2)
        line([(cx + 8, cy - 8), (cx - 8, cy + 8)], color, 2)
    elif kind == "chart":
        for i, bar_h in enumerate([12, 22, 16]):
            rounded(x + 12 + i * 9, y + 30 - bar_h, 5, bar_h, 2, fill=color)
        line([(x + 10, y + 33), (x + 35, y + 33)], color, 2)
    elif kind == "clock":
        draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], outline=color, width=3)
        line([(cx, cy), (cx, cy - 8), (cx + 7, cy + 3)], color, 3)
    elif kind == "template":
        rounded(x + 12, y + 10, 20, 24, 4, fill="#ffffff", outline=color, width=3)
        line([(x + 17, y + 18), (x + 30, y + 18)], color, 2)
        line([(x + 17, y + 25), (x + 27, y + 25)], color, 2)
    else:
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=color, width=3)


# Browser bar.
draw.rectangle([0, 0, WIDTH, 52], fill=COLORS["bar"])
draw.line([0, 51, WIDTH, 51], fill=COLORS["line"])
rounded(24, 10, 230, 34, 8, COLORS["white"], COLORS["line"])
icon_tile(36, 15, "pen", "#f0edff", COLORS["purple"], 24)
text(68, 17, "AI 营销", "small", COLORS["text"])
for index, color in enumerate(["#ff5f57", "#ffbd2e", "#28c840"]):
    draw.ellipse([WIDTH - 92 + index * 24, 20, WIDTH - 80 + index * 24, 32], fill=color)
text(WIDTH - 330, 17, "礼物", "small", COLORS["gold"])
rounded(WIDTH - 260, 10, 120, 34, 17, COLORS["white"], COLORS["line"])
text(WIDTH - 238, 17, "管理端", "small", COLORS["text"])

# Brand row.
draw.rectangle([0, 52, WIDTH, 142], fill=COLORS["white"])
draw.line([0, 141, WIDTH, 141], fill=COLORS["line2"])
text(38, 76, "新商机", "logo", COLORS["red"])
text(170, 76, "OPC社区", "logo", COLORS["gold"])
rounded(420, 72, 910, 54, 27, COLORS["white"], "#bdafff", 2)
text(448, 88, "搜索你需要的 AI 助理、工具或模板", "body", "#8790a3")
rounded(1268, 72, 58, 54, 27, COLORS["purple"])
draw.ellipse([1286, 88, 1305, 107], outline=COLORS["white"], width=3)
line([(1301, 103), (1312, 114)], COLORS["white"], 3)
rounded(1365, 73, 420, 52, 26, COLORS["navy"])
rounded(1384, 83, 58, 28, 14, COLORS["navy"], COLORS["gold"], 3)
text(1398, 86, "VIP", "bold16", COLORS["gold"])
text(1460, 88, "开通会员，享100+办公权益", "bold16", COLORS["white"])
rounded(1690, 80, 80, 38, 19, "#ffe6b0")
text(1703, 88, "立即开通", "bold16", "#6b3d00")

# Top tabs.
draw.rectangle([0, 142, WIDTH, 204], fill=COLORS["white"])
tabs = ["首页", "AI 助理", "AI 营销", "AI 图片", "AI 视频", "AI 音频", "AI 编程", "AI 写作"]
tab_x = 42
for tab in tabs:
    tab_color = COLORS["purple"] if tab == "AI 营销" else "#020617"
    text(tab_x, 164, tab, "tab", tab_color)
    tab_width, _ = text_size(tab, "tab")
    if tab == "AI 营销":
        draw.rounded_rectangle([tab_x - 6, 200, tab_x + tab_width + 6, 205], radius=2, fill=COLORS["purple"])
    tab_x += tab_width + 66
draw.line([0, 203, WIDTH, 203], fill=COLORS["line"])

# Main function bar.
draw.rectangle([0, 204, WIDTH, HEIGHT], fill=COLORS["bg"])
rounded(32, 232, 1984, 118, 8, COLORS["white"], COLORS["line"])
text(58, 252, "AI 营销 / 爆款文案生成", "small", COLORS["purple"])
text(58, 282, "爆款文案生成工作台", "h1", COLORS["text"])
text(58, 326, "填写需求 → 生成文案 → 多版本对比 → 一键复制/导出/投放复用", "body", COLORS["muted"])
chip_x = 560
for chip_label in ["社媒投放", "私域转化", "短视频脚本"]:
    chip_x += chip(chip_x, 292, chip_label, COLORS["purple_light"], COLORS["purple"], "#d7d0ff") + 10
chip(930, 292, "消耗 10 积分", "#fff2e8", "#e45b2a", "#ffd9c2")
chip(1075, 292, "VIP 高转化模板可用", "#fff8df", "#835400", "#ffe8a3")
button(1710, 270, 142, 44, "返回营销中心", COLORS["white"], COLORS["purple"], "#cfc8ff")
button(1870, 270, 110, 44, "保存方案", COLORS["purple"], COLORS["white"])

# Three-column body.
left = (32, 372, 500, 732)
center = (552, 372, 960, 732)
right = (1530, 372, 486, 732)

# Left column.
x, y, w, h = left
rounded(x, y, w, h, 8, COLORS["white"], COLORS["line"])
icon_tile(x + 20, y + 20, "pen")
text(x + 78, y + 20, "创作需求", "h2")
text(x + 78, y + 53, "明确产品、渠道与卖点，生成更准的转化文案", "small", COLORS["muted"])
field(x + 22, y + 96, 216, "产品名称", "AI办公效率训练营")
field(x + 262, y + 96, 216, "目标人群", "25-35岁职场新人")
text(x + 22, y + 188, "投放渠道", "small", COLORS["muted"])
for index, label in enumerate(["小红书", "公众号", "短视频", "私域"]):
    fill = COLORS["purple"] if index == 0 else COLORS["soft"]
    color = COLORS["white"] if index == 0 else COLORS["text"]
    rounded(x + 22 + index * 111, y + 214, 104, 38, 8, fill, "#dfe4ee")
    text(x + 46 + index * 111, y + 222, label, "bold16", color)
field(x + 22, y + 274, 216, "文案类型", "新品推广")
field(x + 262, y + 274, 216, "语气风格", "专业、有记忆点")
field(x + 22, y + 366, 456, "核心卖点", "3天掌握AI办公自动化；提供可复用模板；适合零基础上手。", 126, True)
field(x + 22, y + 514, 456, "禁用词", "夸大承诺、绝对化表达、低价冲动", 82, True)
rounded(x + 22, y + 616, 456, 54, 8, "#fff7ed", "#ffd4b5")
icon_tile(x + 40, y + 625, "spark", "#fff0e8", COLORS["orange"], 36)
text(x + 88, y + 626, "建议先选择渠道，再补充 3 个卖点", "bold16", "#9a3412")
text(x + 88, y + 650, "系统会自动适配标题长度、CTA 和转化语气", "tiny", "#a85b2b")
button(x + 22, y + 690, 456, 52, "立即生成文案", COLORS["purple"], COLORS["white"], font_key="bold")

# Center column.
x, y, w, h = center
rounded(x, y, w, h, 8, COLORS["white"], COLORS["line"])
icon_tile(x + 20, y + 20, "spark")
text(x + 78, y + 20, "生成结果", "h2")
text(x + 78, y + 53, "已生成 3 个候选版本，可继续改写、扩写或生成素材", "small", COLORS["muted"])
button(x + w - 372, y + 22, 116, 40, "重新生成", COLORS["white"], COLORS["purple"], "#cfc8ff")
button(x + w - 242, y + 22, 132, 40, "生成投放素材", "#fff2ed", "#d94125", "#ffc5b6")
button(x + w - 94, y + 22, 70, 40, "导出", COLORS["purple"], COLORS["white"])
rounded(x + 22, y + 84, w - 44, 42, 8, "#f7f5ff", "#e1dcff")
rounded(x + 42, y + 99, 620, 12, 6, "#ddd7ff")
rounded(x + 42, y + 99, 475, 12, 6, COLORS["purple"])
text(x + 690, y + 94, "热度模型分析完成 · 适配小红书渠道", "small", COLORS["purple"])

candidates = [
    (
        "版本 A",
        "热度评分 92",
        "把每天 2 小时重复办公，变成 10 分钟自动完成",
        "适合想提升效率的职场新人。3 天训练营带你学会 AI 写邮件、做表格、整理会议纪要，配套模板可直接复用。",
        "立即领取试听课",
    ),
    (
        "版本 B",
        "热度评分 88",
        "不会写提示词，也能做出专业办公成果",
        "从零开始拆解真实办公场景：日报、PPT 大纲、Excel 公式、会议总结，一套流程帮你把 AI 真正用起来。",
        "马上开始训练",
    ),
    (
        "版本 C",
        "热度评分 84",
        "你的第一套 AI 办公自动化模板包来了",
        "不用熬夜摸索工具，跟着案例完成 7 个高频任务，结营即可带走可复制的个人效率工作流。",
        "保存模板包",
    ),
]
candidate_y = y + 148
for version, score, title, body, cta in candidates:
    card_h = 176
    rounded(x + 22, candidate_y, w - 44, card_h, 8, COLORS["white"], "#e2e6ef")
    rounded(x + 42, candidate_y + 18, 76, 30, 15, COLORS["purple_light"])
    text(x + 58, candidate_y + 23, version, "bold16", COLORS["purple"])
    rounded(x + w - 164, candidate_y + 18, 118, 30, 15, "#fff1ed")
    text(x + w - 148, candidate_y + 23, score, "bold16", "#e44124")
    text(x + 42, candidate_y + 62, "标题", "tiny", COLORS["muted2"])
    text(x + 90, candidate_y + 56, ellipsize(title, 660, "bold20"), "bold20", COLORS["text"])
    text(x + 42, candidate_y + 96, "正文", "tiny", COLORS["muted2"])
    body_y = candidate_y + 90
    for body_line in wrap_by_width(body, 620, "body", 2):
        text(x + 90, body_y, body_line, "body", "#263044")
        body_y += 27
    text(x + 42, candidate_y + 138, "CTA", "tiny", COLORS["muted2"])
    rounded(x + 90, candidate_y + 132, 150, 34, 17, "#effaf5", "#b9ead5")
    text(x + 108, candidate_y + 139, cta, "bold16", "#087a52")
    action_x = x + w - 396
    for label in ["复制", "改写", "扩写", "保存"]:
        button(action_x, candidate_y + 124, 78, 34, label, COLORS["white"], COLORS["purple"], "#d6d0ff", "small")
        action_x += 86
    candidate_y += card_h + 18

# Right column.
x, y, w, h = right
rounded(x, y, w, h, 8, COLORS["white"], COLORS["line"])
icon_tile(x + 18, y + 20, "template")
text(x + 76, y + 20, "模板与历史", "h2")
text(x + 76, y + 53, "快速套用成熟场景，复用最近生成内容", "small", COLORS["muted"])
text(x + 22, y + 96, "高频模板", "bold20")
templates = [
    ("短视频口播", "30 秒开场钩子 + 转化收束", "spark"),
    ("小红书种草", "标题、正文、话题标签一键生成", "pen"),
    ("公众号标题", "10 组标题方向与点击理由", "template"),
    ("私域转化话术", "朋友圈、社群、企微跟进话术", "chart"),
]
template_y = y + 132
for name, description, kind in templates:
    rounded(x + 22, template_y, w - 44, 72, 8, COLORS["soft"], "#e5eaf3")
    icon_tile(x + 38, template_y + 14, kind, COLORS["purple_light"], COLORS["purple"], 44)
    text(x + 96, template_y + 13, name, "bold16")
    text(x + 96, template_y + 39, ellipsize(description, w - 150, "small"), "small", COLORS["muted"])
    template_y += 84

rounded(x + 22, y + 474, w - 44, 122, 8, COLORS["orange"])
text(x + 46, y + 498, "高转化模板库开放", "h3", COLORS["white"])
text(x + 46, y + 530, "会员可解锁行业案例、爆款标题库", "small", "#fff1ed")
rounded(x + 46, y + 552, 106, 34, 17, COLORS["white"])
text(x + 64, y + 559, "立即查看", "bold16", "#e44124")
line([(x + w - 106, y + 548), (x + w - 58, y + 500), (x + w - 58, y + 536)], "#ffd6c8", 8)
line([(x + w - 58, y + 500), (x + w - 96, y + 508)], "#ffd6c8", 8)

text(x + 22, y + 626, "最近生成", "bold20")
records = [
    ("智能办公椅新品推广", "今天 10:24", "已保存"),
    ("暑期课程转化文案", "今天 09:41", "已改写"),
    ("社群裂变活动", "昨天 18:20", "已导出"),
    ("AI训练营报名页", "昨天 16:08", "已复制"),
]
record_y = y + 666
for title, time_label, status in records:
    rounded(x + 22, record_y, w - 44, 50, 8, COLORS["white"], "#edf0f6")
    draw.ellipse([x + 38, record_y + 18, x + 48, record_y + 28], fill=COLORS["purple"])
    text(x + 60, record_y + 13, ellipsize(title, 240, "small"), "small", COLORS["text"])
    text(x + w - 150, record_y + 13, time_label, "tiny", COLORS["muted2"])
    text(x + 60, record_y + 32, status, "tiny", COLORS["green"])
    record_y += 58

# Bottom utility strip.
rounded(1600, 1110, 408, 34, 17, COLORS["white"], COLORS["line"])
text(1620, 1116, "生成队列空闲 · 已连接营销模板库", "small", COLORS["muted"])
for index, color in enumerate([COLORS["purple"], "#3b82f6", COLORS["gold"]]):
    draw.ellipse([1930 + index * 22, 1122, 1940 + index * 22, 1132], fill=color)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUTPUT)
print(OUTPUT)
print(f"{OUTPUT.stat().st_size} bytes")
