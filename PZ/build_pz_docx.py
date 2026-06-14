from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime
import re

from lxml import etree


PZ_DIR = Path(__file__).resolve().parent
DB_SCHEMA_SVG_PATH = PZ_DIR / "db_schema.svg"
SUBJECT_AREA_SVG_PATH = PZ_DIR / "subject_area_schema.svg"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

NSMAP = {"w": W, "r": R}


def qn(tag: str) -> str:
    prefix, name = tag.split(":")
    namespaces = {"w": W, "r": R, "wp": WP, "a": A, "pic": PIC}
    return f"{{{namespaces[prefix]}}}{name}"


def el(tag: str, attrs: dict[str, str] | None = None, text: str | None = None):
    node = etree.Element(qn(tag), nsmap=NSMAP if tag == "w:document" else None)
    for key, value in (attrs or {}).items():
        node.set(qn(key) if ":" in key else key, value)
    if text is not None:
        node.text = text
    return node


def fonts_attrs(font_name: str):
    return {
        "w:ascii": font_name,
        "w:hAnsi": font_name,
        "w:eastAsia": font_name,
        "w:cs": font_name,
    }


def text_run(
    text: str,
    bold: bool = False,
    italic: bool = False,
    style: str | None = None,
    font_name: str = "Times New Roman",
    size: str = "26",
):
    run = el("w:r")
    rpr = el("w:rPr")
    rpr.append(el("w:rFonts", fonts_attrs(font_name)))
    rpr.append(el("w:sz", {"w:val": size}))
    rpr.append(el("w:szCs", {"w:val": size}))
    if style:
        rpr.append(el("w:rStyle", {"w:val": style}))
    if bold:
        rpr.append(el("w:b"))
    if italic:
        rpr.append(el("w:i"))
    run.append(rpr)
    t = el("w:t", text=text)
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    run.append(t)
    return run


def paragraph(
    text: str = "",
    style: str | None = None,
    align: str | None = None,
    bold: bool = False,
    italic: bool = False,
    page_break_before: bool = False,
):
    p = el("w:p")
    ppr = el("w:pPr")
    if style:
        ppr.append(el("w:pStyle", {"w:val": style}))
    if align:
        ppr.append(el("w:jc", {"w:val": align}))
    if page_break_before:
        ppr.append(el("w:pageBreakBefore"))
    if len(ppr):
        p.append(ppr)
    if text:
        run_font = "Courier New" if style == "Code" else "Times New Roman"
        run_size = "18" if style == "Code" else "28" if style == "Title" else "26"
        p.append(text_run(text, bold=bold, italic=italic, font_name=run_font, size=run_size))
    return p


def page_break():
    p = el("w:p")
    r = el("w:r")
    r.append(el("w:br", {"w:type": "page"}))
    p.append(r)
    return p


def field_paragraph(instr: str, placeholder: str):
    p = el("w:p")
    p.append(text_run(""))
    r1 = el("w:r")
    r1.append(el("w:fldChar", {"w:fldCharType": "begin"}))
    p.append(r1)
    r2 = el("w:r")
    r2_rpr = el("w:rPr")
    r2_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    r2_rpr.append(el("w:sz", {"w:val": "26"}))
    r2_rpr.append(el("w:szCs", {"w:val": "26"}))
    r2.append(r2_rpr)
    instr_node = el("w:instrText", text=instr)
    instr_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r2.append(instr_node)
    p.append(r2)
    r3 = el("w:r")
    r3.append(el("w:fldChar", {"w:fldCharType": "separate"}))
    p.append(r3)
    p.append(text_run(placeholder))
    r4 = el("w:r")
    r4.append(el("w:fldChar", {"w:fldCharType": "end"}))
    p.append(r4)
    return p


def page_field(name: str):
    runs = []
    r1 = el("w:r")
    r1.append(el("w:fldChar", {"w:fldCharType": "begin"}))
    runs.append(r1)
    r2 = el("w:r")
    r2_rpr = el("w:rPr")
    r2_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    r2_rpr.append(el("w:sz", {"w:val": "26"}))
    r2_rpr.append(el("w:szCs", {"w:val": "26"}))
    r2.append(r2_rpr)
    instr = el("w:instrText", text=f" {name} ")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r2.append(instr)
    runs.append(r2)
    r3 = el("w:r")
    r3.append(el("w:fldChar", {"w:fldCharType": "separate"}))
    runs.append(r3)
    runs.append(text_run("1"))
    r4 = el("w:r")
    r4.append(el("w:fldChar", {"w:fldCharType": "end"}))
    runs.append(r4)
    return runs


def cell(*content, width: int = 2000, grid_span: int | None = None):
    tc = el("w:tc")
    tcpr = el("w:tcPr")
    tcpr.append(el("w:tcW", {"w:w": str(width), "w:type": "dxa"}))
    if grid_span:
        tcpr.append(el("w:gridSpan", {"w:val": str(grid_span)}))
    tc.append(tcpr)
    if not content:
        content = (paragraph(""),)
    for item in content:
        tc.append(item if item.tag == qn("w:p") else paragraph(str(item)))
    return tc


def table(rows: list[list[str]], widths: list[int] | None = None, header: bool = False):
    tbl = el("w:tbl")
    tbl_pr = el("w:tblPr")
    tbl_pr.append(el("w:tblW", {"w:w": "0", "w:type": "auto"}))
    borders = el("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        borders.append(el(f"w:{side}", {"w:val": "single", "w:sz": "4", "w:space": "0", "w:color": "000000"}))
    tbl_pr.append(borders)
    tbl.append(tbl_pr)
    widths = widths or [2400] * max(len(row) for row in rows)
    grid = el("w:tblGrid")
    for width in widths:
        grid.append(el("w:gridCol", {"w:w": str(width)}))
    tbl.append(grid)
    for row_index, row in enumerate(rows):
        tr = el("w:tr")
        if header and row_index == 0:
            trpr = el("w:trPr")
            trpr.append(el("w:tblHeader"))
            tr.append(trpr)
        for col_index, value in enumerate(row):
            p = paragraph(value, align="center" if row_index == 0 else None, bold=header and row_index == 0)
            tr.append(cell(p, width=widths[min(col_index, len(widths) - 1)]))
        tbl.append(tr)
    return tbl


def placeholder(text: str):
    return paragraph(f"[ВСТАВИТЬ: {text}]", style="Placeholder")


def content_line(title: str, page: str):
    return paragraph(f"{title} {'.' * max(6, 72 - len(title))} {page}")


def subject_area_svg() -> str:
    nodes = [
        ("trader", 70, 60, 240, 70, "Пользователь\\n(трейдер)", "#ecfeff"),
        ("sources", 480, 60, 240, 70, "Открытые источники\\nрыночных данных", "#fef9c3"),
        ("admin", 890, 60, 240, 70, "Администратор", "#fce7f3"),
        ("client", 70, 190, 240, 78, "Страницы сайта\\nCryptoTrade", "#f8fafc"),
        ("api", 480, 190, 240, 78, "Python backend/API", "#eef2ff"),
        ("admin_panel", 890, 190, 240, 78, "Административная\\nпанель", "#f8fafc"),
        ("market", 70, 330, 220, 78, "Рынок\\nкриптовалют", "#ecfdf5"),
        ("trade", 350, 330, 220, 78, "Сделка\\nпокупки/продажи", "#ecfdf5"),
        ("portfolio", 630, 330, 220, 78, "Портфель\\nпользователя", "#ecfdf5"),
        ("history", 910, 330, 220, 78, "История\\nопераций", "#ecfdf5"),
        ("db", 350, 520, 500, 88, "SQLite-база cryptotrade.db\\nusers, currencies, wallets, transactions, price_history", "#fff7ed"),
        ("agreements", 70, 520, 220, 88, "Политика\\nи соглашение", "#f1f5f9"),
        ("simulation", 910, 520, 220, 88, "Симуляция\\nактивности", "#f1f5f9"),
    ]
    node_map = {node_id: (x, y, w, h) for node_id, x, y, w, h, *_ in nodes}

    def c(node_id: str):
        x, y, w, h = node_map[node_id]
        return x + w / 2, y + h / 2

    def port(node_id: str, side: str):
        x, y, w, h = node_map[node_id]
        return {
            "top": (x + w / 2, y),
            "bottom": (x + w / 2, y + h),
            "left": (x, y + h / 2),
            "right": (x + w, y + h / 2),
        }[side]

    def rounded_rect(node_id: str, x: int, y: int, w: int, h: int, text: str, fill: str):
        lines = text.split("\\n")
        start = y + h / 2 - (len(lines) - 1) * 11
        parts = [f'<rect class="node" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}"/>']
        for index, line in enumerate(lines):
            parts.append(f'<text x="{x + w / 2}" y="{start + index * 22}" text-anchor="middle" dominant-baseline="middle">{line}</text>')
        return parts

    def path(points: list[tuple[float, float]], label: str = "", label_at: tuple[float, float] | None = None):
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
        parts = [f'<path class="arrow" d="{d}"/>']
        if label and label_at:
            parts.append(f'<text class="label" x="{label_at[0]:.1f}" y="{label_at[1]:.1f}" text-anchor="middle">{label}</text>')
        return parts

    arrows: list[str] = []
    arrows += path([port("trader", "bottom"), port("client", "top")], "работает с сайтом", (190, 165))
    arrows += path([port("admin", "bottom"), port("admin_panel", "top")], "управляет", (1010, 165))
    arrows += path([port("sources", "bottom"), port("api", "top")], "курсы и свечи", (600, 165))
    arrows += path([port("client", "right"), (390, 229), port("api", "left")], "API-запросы", (395, 217))
    arrows += path([port("admin_panel", "left"), (810, 229), port("api", "right")], "настройки", (805, 217))
    arrows += path([port("client", "bottom"), (190, 298), port("market", "top")], "", None)
    arrows += path([port("market", "right"), port("trade", "left")], "выбор актива", (320, 363))
    arrows += path([port("trade", "right"), port("portfolio", "left")], "изменяет", (600, 363))
    arrows += path([port("portfolio", "right"), port("history", "left")], "фиксируется", (880, 363))
    arrows += path([port("api", "bottom"), (600, 480), port("db", "top")], "чтение/запись", (660, 470))
    arrows += path([port("trade", "bottom"), (460, 456), (520, 456), (520, 520)], "", None)
    arrows += path([port("portfolio", "bottom"), (740, 456), (680, 456), (680, 520)], "", None)
    arrows += path([port("history", "bottom"), (1020, 456), (850, 456), port("db", "right")], "", None)
    arrows += path([port("client", "bottom"), (190, 456), port("agreements", "top")], "", None)
    arrows += path([port("admin_panel", "bottom"), (1010, 456), port("simulation", "top")], "", None)
    arrows += path([port("simulation", "left"), (850, 564)], "создает учебные данные", (880, 548))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="660" viewBox="0 0 1200 660">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#111827"/>',
        "</marker>",
        "</defs>",
        '<rect width="1200" height="660" fill="#ffffff"/>',
        '<style>text{font-family:Times New Roman,serif;font-size:17px;fill:#111827}.label{font-size:14px;font-weight:bold;fill:#1f2937}.title{font-size:20px;font-weight:bold}.node{stroke:#111827;stroke-width:2}.arrow{stroke:#111827;stroke-width:2;fill:none;marker-end:url(#arrow)}</style>',
        '<text class="title" x="600" y="30" text-anchor="middle">Общая схема предметной области CryptoTrade</text>',
    ]
    parts.extend(arrows)
    for node in nodes:
        parts.extend(rounded_rect(*node))
    parts.append("</svg>")
    return "\n".join(parts)


def db_schema_svg() -> str:
    tables = [
        ("roles", 40, 40, ["PK id", "code", "title"]),
        ("users", 360, 40, ["PK id", "FK role_id", "name", "email", "password", "balance_usd", "created_at", "is_simulated"]),
        ("currencies", 720, 40, ["PK id", "symbol", "name", "price", "risk", "price_mode", "market_symbol", "source", "last_sync_at"]),
        ("wallets", 360, 360, ["PK id", "FK user_id", "FK currency_id", "amount", "updated_at", "is_simulated"]),
        ("transactions", 720, 360, ["PK id", "FK user_id", "FK currency_id", "side", "quantity", "price", "total", "status", "created_at", "is_simulated"]),
        ("price_history", 1080, 360, ["PK id", "FK currency_id", "price", "recorded_at", "position"]),
        ("system_settings", 40, 360, ["PK id = main", "simulation_enabled", "simulation_level", "simulation_users_target", "simulation_trades_per_minute", "last_simulation_at", "simulation_carry"]),
    ]
    links = [
        ("roles", "users", "1:N"),
        ("users", "wallets", "1:N"),
        ("currencies", "wallets", "1:N"),
        ("users", "transactions", "1:N"),
        ("currencies", "transactions", "1:N"),
        ("currencies", "price_history", "1:N"),
    ]
    table_map = {name: (x, y, 270, 44 + len(fields) * 24) for name, x, y, fields in tables}

    def center(name: str):
        x, y, w, h = table_map[name]
        return x + w / 2, y + h / 2

    def edge(start: str, end: str):
        sx, sy = center(start)
        ex, ey = center(end)
        x1, y1, w1, h1 = table_map[start]
        x2, y2, w2, h2 = table_map[end]
        if abs(ex - sx) > abs(ey - sy):
            sx = x1 + (w1 if ex > sx else 0)
            ex = x2 + (0 if ex > sx else w2)
        else:
            sy = y1 + (h1 if ey > sy else 0)
            ey = y2 + (0 if ey > sy else h2)
        return sx, sy, ex, ey

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1390" height="650" viewBox="0 0 1390 650">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#111827"/>',
        "</marker>",
        "</defs>",
        '<rect width="1390" height="650" fill="#ffffff"/>',
        '<style>text{font-family:Times New Roman,serif;font-size:16px;fill:#111827}.title{font-size:18px;font-weight:bold}.field{font-size:15px}.table{fill:#f8fafc;stroke:#111827;stroke-width:2}.head{fill:#dbeafe;stroke:#111827;stroke-width:2}.link{stroke:#111827;stroke-width:2;fill:none;marker-end:url(#arrow)}.label{font-weight:bold;font-size:14px;fill:#1d4ed8}</style>',
        '<text class="title" x="695" y="24" text-anchor="middle">Схема базы данных CryptoTrade</text>',
    ]
    for start, end, label in links:
        sx, sy, ex, ey = edge(start, end)
        if abs(ex - sx) > 1 and abs(ey - sy) > 1:
            mid_x = (sx + ex) / 2
            path = f"M {sx:.1f} {sy:.1f} L {mid_x:.1f} {sy:.1f} L {mid_x:.1f} {ey:.1f} L {ex:.1f} {ey:.1f}"
            lx, ly = mid_x, sy - 6
        else:
            path = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
            lx, ly = (sx + ex) / 2, (sy + ey) / 2 - 7
        parts.append(f'<path class="link" d="{path}"/>')
        parts.append(f'<text class="label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle">{label}</text>')
    for name, x, y, fields in tables:
        height = 44 + len(fields) * 24
        parts.append(f'<rect class="table" x="{x}" y="{y}" width="270" height="{height}" rx="4"/>')
        parts.append(f'<rect class="head" x="{x}" y="{y}" width="270" height="34" rx="4"/>')
        parts.append(f'<text class="title" x="{x + 135}" y="{y + 22}" text-anchor="middle">{name}</text>')
        for index, field in enumerate(fields):
            parts.append(f'<text class="field" x="{x + 14}" y="{y + 58 + index * 24}">{field}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def drawing_paragraph(rel_id: str, name: str, cx: str, cy: str):
    p = el("w:p")
    ppr = el("w:pPr")
    ppr.append(el("w:jc", {"w:val": "center"}))
    p.append(ppr)
    r = el("w:r")
    drawing = el("w:drawing")
    inline = el("wp:inline", {"distT": "0", "distB": "0", "distL": "0", "distR": "0"})
    inline.append(el("wp:extent", {"cx": cx, "cy": cy}))
    inline.append(el("wp:effectExtent", {"l": "0", "t": "0", "r": "0", "b": "0"}))
    inline.append(el("wp:docPr", {"id": "2", "name": name}))
    inline.append(el("wp:cNvGraphicFramePr"))
    graphic = el("a:graphic")
    graphic_data = el("a:graphicData", {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"})
    pic = el("pic:pic")
    nv_pic_pr = el("pic:nvPicPr")
    nv_pic_pr.append(el("pic:cNvPr", {"id": "0", "name": name}))
    nv_pic_pr.append(el("pic:cNvPicPr"))
    pic.append(nv_pic_pr)
    blip_fill = el("pic:blipFill")
    blip_fill.append(el("a:blip", {"r:embed": rel_id}))
    stretch = el("a:stretch")
    stretch.append(el("a:fillRect"))
    blip_fill.append(stretch)
    pic.append(blip_fill)
    sp_pr = el("pic:spPr")
    xfrm = el("a:xfrm")
    xfrm.append(el("a:off", {"x": "0", "y": "0"}))
    xfrm.append(el("a:ext", {"cx": cx, "cy": cy}))
    sp_pr.append(xfrm)
    prst_geom = el("a:prstGeom", {"prst": "rect"})
    prst_geom.append(el("a:avLst"))
    sp_pr.append(prst_geom)
    pic.append(sp_pr)
    graphic_data.append(pic)
    graphic.append(graphic_data)
    inline.append(graphic)
    drawing.append(inline)
    r.append(drawing)
    p.append(r)
    return p


def style_doc():
    styles = el("w:styles")

    doc_defaults = el("w:docDefaults")
    rpr_default = el("w:rPrDefault")
    default_rpr = el("w:rPr")
    default_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    default_rpr.append(el("w:sz", {"w:val": "26"}))
    default_rpr.append(el("w:szCs", {"w:val": "26"}))
    rpr_default.append(default_rpr)
    doc_defaults.append(rpr_default)
    ppr_default = el("w:pPrDefault")
    default_ppr = el("w:pPr")
    default_ppr.append(el("w:spacing", {"w:line": "288", "w:lineRule": "auto", "w:after": "0"}))
    default_ppr.append(el("w:ind", {"w:firstLine": "850"}))
    default_ppr.append(el("w:jc", {"w:val": "both"}))
    ppr_default.append(default_ppr)
    doc_defaults.append(ppr_default)
    styles.append(doc_defaults)

    def style(style_id: str, name: str, based_on: str | None = None, next_style: str | None = None, ppr=None, rpr=None, typ="paragraph", default=False):
        st = el("w:style", {"w:type": typ, "w:styleId": style_id})
        if default:
            st.set(qn("w:default"), "1")
        st.append(el("w:name", {"w:val": name}))
        if based_on:
            st.append(el("w:basedOn", {"w:val": based_on}))
        if next_style:
            st.append(el("w:next", {"w:val": next_style}))
        if ppr is not None:
            st.append(ppr)
        if rpr is not None:
            st.append(rpr)
        styles.append(st)

    normal_ppr = el("w:pPr")
    normal_ppr.append(el("w:spacing", {"w:line": "288", "w:lineRule": "auto", "w:after": "0"}))
    normal_ppr.append(el("w:ind", {"w:firstLine": "850"}))
    normal_ppr.append(el("w:jc", {"w:val": "both"}))
    normal_rpr = el("w:rPr")
    normal_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    normal_rpr.append(el("w:sz", {"w:val": "26"}))
    normal_rpr.append(el("w:szCs", {"w:val": "26"}))
    style("Normal", "Normal", ppr=normal_ppr, rpr=normal_rpr, default=True)

    h1_ppr = el("w:pPr")
    h1_ppr.append(el("w:spacing", {"w:before": "0", "w:after": "780"}))
    h1_ppr.append(el("w:ind", {"w:firstLine": "850"}))
    h1_rpr = el("w:rPr")
    h1_rpr.append(el("w:b"))
    h1_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    h1_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Heading1", "heading 1", "Normal", "Normal", h1_ppr, h1_rpr)

    h2_ppr = el("w:pPr")
    h2_ppr.append(el("w:spacing", {"w:before": "0", "w:after": "780"}))
    h2_ppr.append(el("w:ind", {"w:firstLine": "850"}))
    h2_rpr = el("w:rPr")
    h2_rpr.append(el("w:b"))
    h2_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    h2_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Heading2", "heading 2", "Normal", "Normal", h2_ppr, h2_rpr)

    title_ppr = el("w:pPr")
    title_ppr.append(el("w:jc", {"w:val": "center"}))
    title_ppr.append(el("w:spacing", {"w:after": "240"}))
    title_rpr = el("w:rPr")
    title_rpr.append(el("w:b"))
    title_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    title_rpr.append(el("w:sz", {"w:val": "28"}))
    style("Title", "Title", "Normal", "Normal", title_ppr, title_rpr)

    caption_ppr = el("w:pPr")
    caption_ppr.append(el("w:jc", {"w:val": "center"}))
    caption_ppr.append(el("w:spacing", {"w:before": "120", "w:after": "120"}))
    caption_rpr = el("w:rPr")
    caption_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    caption_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Caption", "Caption", "Normal", "Normal", caption_ppr, caption_rpr)

    placeholder_rpr = el("w:rPr")
    placeholder_rpr.append(el("w:i"))
    placeholder_rpr.append(el("w:color", {"w:val": "C00000"}))
    placeholder_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    placeholder_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Placeholder", "Placeholder", "Normal", "Normal", normal_ppr, placeholder_rpr)

    code_ppr = el("w:pPr")
    code_ppr.append(el("w:spacing", {"w:before": "120", "w:after": "120", "w:line": "240", "w:lineRule": "auto"}))
    code_ppr.append(el("w:ind", {"w:firstLine": "850"}))
    code_rpr = el("w:rPr")
    code_rpr.append(el("w:rFonts", fonts_attrs("Courier New")))
    code_rpr.append(el("w:sz", {"w:val": "18"}))
    style("Code", "Code", "Normal", "Normal", code_ppr, code_rpr)
    return styles


def footer_doc(kind: str):
    root = el("w:ftr")
    rows = [
        ["Изм.", "Лист", "№ докум.", "Подп.", "Дата", "CryptoTrade. Пояснительная записка", "Лист", ""],
        ["", "", "", "", "", "КР.WEB.CT-01 81 00", "", "Листов"],
    ]
    if kind == "first":
        rows.insert(0, ["", "", "", "", "", "[ШТАМП 40 мм: заполнить шифр, тему, листы]", "", ""])
    tbl = table(rows, widths=[650, 650, 1200, 800, 800, 4200, 700, 900], header=False)
    root.append(tbl)
    return root


def section_properties(main: bool = False):
    sect = el("w:sectPr")
    if main:
        sect.append(el("w:footerReference", {"w:type": "first", "r:id": "rIdFooterFirst"}))
        sect.append(el("w:footerReference", {"w:type": "default", "r:id": "rIdFooterDefault"}))
        sect.append(el("w:titlePg"))
    sect.append(el("w:pgSz", {"w:w": "11906", "w:h": "16838"}))
    sect.append(el("w:pgMar", {"w:top": "1134", "w:right": "850", "w:bottom": "1417", "w:left": "1701", "w:header": "708", "w:footer": "708", "w:gutter": "0"}))
    if main:
        borders = el("w:pgBorders", {"w:offsetFrom": "page"})
        for side in ["top", "left", "bottom", "right"]:
            borders.append(el(f"w:{side}", {"w:val": "single", "w:sz": "8", "w:space": "24", "w:color": "000000"}))
        sect.append(borders)
    return sect


def section_break_previous():
    p = el("w:p")
    ppr = el("w:pPr")
    ppr.append(section_properties(main=False))
    p.append(ppr)
    return p


def document_doc():
    doc = el("w:document")
    body = el("w:body")

    body.append(paragraph("[ЗАПОЛНИТЬ: полное название учреждения образования]", style="Title"))
    body.append(paragraph("[ЗАПОЛНИТЬ: факультет / кафедра]", align="center"))
    body.append(paragraph("", align="center"))
    body.append(paragraph("КУРСОВАЯ РАБОТА", style="Title"))
    body.append(paragraph("по дисциплине [ЗАПОЛНИТЬ: название дисциплины]", align="center"))
    body.append(paragraph("на тему", align="center"))
    body.append(paragraph("Разработка сайта для симуляции торговли криптовалютой", style="Title"))
    body.append(paragraph("Пояснительная записка", align="center", bold=True))
    body.append(paragraph("", align="center"))
    body.append(placeholder("ФИО студента, группа, номер зачетной книжки"))
    body.append(placeholder("ФИО руководителя, должность"))
    body.append(placeholder("город и год выполнения"))
    body.append(page_break())

    body.append(paragraph("АННОТАЦИЯ", style="Title"))
    annotation = [
        "В курсовой работе разработан сайт CryptoTrade для учебной симуляции торговли криптовалютой.",
        "Сайт реализует регистрацию и авторизацию пользователей, просмотр рынка активов, покупку и продажу криптовалют, отображение портфеля и истории операций.",
        "В системе предусмотрены роли трейдера, администратора и симулируемого пользователя.",
        "Администратор имеет доступ к панели управления, может управлять курсами, добавлять активы, просматривать операции пользователей и запускать симуляцию активности.",
        "Для хранения данных используется SQLite-база cryptotrade.db и логическая модель из связанных сущностей: роли, пользователи, валюты, кошельки, транзакции, история цен и системные настройки.",
        "Практическая часть выполнена средствами HTML, CSS, JavaScript и Python backend/API.",
        "Курсы криптовалют и свечи графиков могут обновляться через открытые источники Binance Spot и Coinbase Exchange с локальной fallback-историей.",
        "В пояснительной записке приведены анализ предметной области, проектирование базы данных, описание разработки сайта и результаты тестирования.",
    ]
    for line in annotation:
        body.append(paragraph(line))
    body.append(placeholder("проверить количество страниц, рисунков, таблиц, источников и приложений после финальной верстки"))
    body.append(page_break())

    body.append(paragraph("ЗАДАНИЕ", style="Title"))
    body.append(placeholder("вставить скан или перепечатанный бланк задания, если его требует преподаватель"))
    body.append(page_break())
    body.append(section_break_previous())

    body.append(paragraph("СОДЕРЖАНИЕ", style="Title"))
    for title, page in [
        ("ВВЕДЕНИЕ", "5"),
        ("ГЛАВА 1. АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ", "6"),
        ("1.1 Характеристика предметной области", "6"),
        ("1.2 Роли пользователей системы", "8"),
        ("1.3 Основные бизнес-процессы", "9"),
        ("1.4 Ограничения учебной модели", "11"),
        ("1.5 Постановка задачи", "12"),
        ("ГЛАВА 2. ПРОЕКТИРОВАНИЕ БАЗЫ ДАННЫХ", "14"),
        ("2.1 Требования к хранению данных", "14"),
        ("2.2 Описание сущностей", "15"),
        ("2.3 Связи между сущностями", "17"),
        ("2.4 Реализация базы данных в SQLite", "18"),
        ("2.5 Схема базы данных", "19"),
        ("ГЛАВА 3. РАЗРАБОТКА САЙТА", "20"),
        ("3.1 Общая архитектура проекта", "20"),
        ("3.2 Пользовательский интерфейс и навигация", "22"),
        ("3.3 Авторизация, регистрация и управление сессией", "24"),
        ("3.4 Пользовательские страницы", "25"),
        ("3.5 Торговая страница и графики", "27"),
        ("3.6 Клиентская логика JavaScript", "29"),
        ("3.7 Backend/API и работа с SQLite", "31"),
        ("3.8 Административная панель и симуляция", "33"),
        ("3.9 Оформление, футер и документы", "35"),
        ("3.10 Алгоритмы работы программы", "36"),
        ("ГЛАВА 4. ТЕСТИРОВАНИЕ", "38"),
        ("4.1 Методика тестирования", "38"),
        ("4.2 Направления проверки", "39"),
        ("4.3 Тестовые сценарии", "41"),
        ("4.4 Анализ результатов тестирования", "44"),
        ("ЗАКЛЮЧЕНИЕ", "46"),
        ("СПИСОК СОКРАЩЕНИЙ", "48"),
        ("СПИСОК ИСТОЧНИКОВ", "50"),
        ("ПРИЛОЖЕНИЕ А", "52"),
        ("ПРИЛОЖЕНИЕ Б", "53"),
        ("ПРИЛОЖЕНИЕ В", "54"),
    ]:
        body.append(content_line(title, page))
    body.append(page_break())

    body.append(paragraph("ВВЕДЕНИЕ", style="Heading1"))
    for text in [
        "В настоящее время веб-приложения широко применяются для автоматизации учебных, коммерческих и информационных процессов. Одной из распространенных предметных областей являются электронные торговые платформы, позволяющие пользователю просматривать активы, выполнять операции покупки и продажи, анализировать состояние портфеля и историю действий.",
        "Криптовалютные сервисы являются наглядным примером информационной системы, в которой одновременно используются учетные записи пользователей, справочники активов, операции с балансами, история транзакций, графики изменения цен и административные функции. Даже в учебной реализации такая система требует продуманной структуры данных и согласованной логики обработки пользовательских действий.",
        "Актуальность темы курсового проекта связана с тем, что разработка торгового веб-сайта позволяет показать сразу несколько важных направлений веб-разработки: создание многостраничного интерфейса, регистрацию и авторизацию пользователей, работу с базой данных, обработку форм, проверку корректности операций, получение данных из внешних источников и отображение динамических графиков.",
        "Целью курсового проекта является разработка сайта CryptoTrade для учебной симуляции торговли криптовалютой. Сайт должен позволять пользователю зарегистрироваться, войти в систему, просматривать рынок криптовалют, выполнять учебные операции покупки и продажи, анализировать портфель и историю операций, а администратору - управлять активами и просматривать общую статистику.",
        "Для достижения поставленной цели необходимо решить следующие задачи: выполнить анализ предметной области; определить роли пользователей; спроектировать логическую и физическую модель базы данных; реализовать хранение данных в SQLite; разработать Python backend/API; создать пользовательские страницы сайта; реализовать торговую форму, портфель, историю, административную панель, графики и симуляцию активности; провести тестирование основных сценариев.",
        "Объектом разработки является веб-сайт CryptoTrade. Предметом разработки является организация пользовательского интерфейса, логики авторизации, торговли, хранения данных, получения рыночных свечей, построения графиков и административного управления рынком активов.",
        "Практическая часть проекта реализована как локальное веб-приложение. Пользовательский интерфейс выполнен средствами HTML, CSS и JavaScript. Серверная часть реализована на Python и предоставляет API для работы с SQLite-базой cryptotrade.db. Такой подход позволяет показать не только внешний вид сайта, но и реальное постоянное хранение пользователей, кошельков, транзакций, истории цен и настроек симуляции.",
        "В рамках проекта используются учебные денежные средства, поэтому сайт не выполняет настоящие финансовые операции и не подключается к реальным криптовалютным кошелькам. При этом для большей наглядности добавлены открытые источники рыночных данных, свечные графики, fallback-история цен, политика конфиденциальности и пользовательское соглашение.",
        "Пояснительная записка включает анализ предметной области, проектирование базы данных, описание разработки сайта, тестирование, заключение, список сокращений, список источников и приложения. В приложениях предполагается разместить описание файлов проекта, блок-схему алгоритма работы программы, схему базы данных и экранные формы сайта.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("ГЛАВА 1. АНАЛИЗ ПРЕДМЕТНОЙ ОБЛАСТИ", style="Heading1", page_break_before=True))
    body.append(paragraph("1.1 Характеристика предметной области", style="Heading2"))
    for text in [
        "Криптовалютная биржа представляет собой информационную систему, предназначенную для организации операций с цифровыми активами. Пользователь такой системы получает сведения о доступных криптовалютах, анализирует текущие цены, выбирает актив и выполняет операции покупки или продажи. Результаты операций отражаются в состоянии счета, портфеля и истории действий пользователя.",
        "Криптовалютные торговые платформы относятся к классу финансово-информационных систем. Их работа связана с обработкой учетных записей пользователей, хранением информации об активах, расчетом стоимости операций и ведением журнала выполненных транзакций. Даже в учебной модели такая система должна поддерживать согласованность данных: при покупке уменьшается денежный баланс и увеличивается количество монет, а при продаже выполняется обратная операция.",
        "В реальных криптовалютных биржах дополнительно используются платежные шлюзы, внешние кошельки, комиссии, механизмы подтверждения личности, биржевые стаканы, ордера разных типов и средства защиты от несанкционированного доступа. В рамках курсового проекта эти механизмы упрощены, так как основная задача состоит не в создании промышленной биржи, а в демонстрации принципов разработки веб-сайта с авторизацией, регистрацией, логической базой данных, пользовательской частью и административной панелью.",
        "Предметная область проекта выбрана таким образом, чтобы показать работу с несколькими связанными сущностями данных. Пользователь взаимодействует с рынком активов, на рынке представлены криптовалюты, каждая операция фиксируется как транзакция, а портфель пользователя формируется на основании кошельков и актуальных цен. Это позволяет построить SQLite-модель данных, содержащую больше пяти связанных таблиц, что соответствует требованиям курсового проекта.",
        "Система CryptoTrade является учебной симуляцией. Пользователь не работает с реальными денежными средствами, а получает демонстрационный баланс в долларах США. Такой подход позволяет безопасно проверить основные функции торговой платформы: регистрацию, вход, выбор актива, покупку, продажу, просмотр портфеля, анализ истории операций и работу с рыночными графиками.",
        "Для приближения учебной модели к реальным торговым платформам в проект добавлены автоматическое обновление курсов, свечные данные, расширенный график на базе TradingView Lightweight Charts, политика конфиденциальности и пользовательское соглашение. При недоступности внешних источников сайт использует локальную историю цен из базы данных.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Общая схема предметной области отражает связь между пользователем, рынком активов, торговой операцией, портфелем, историей, администратором, серверной частью и SQLite-базой данных. Она показывает, что пользователь работает со страницами сайта, торговая операция изменяет портфель и историю, администратор управляет рынком и симуляцией, а постоянное хранение обеспечивается базой данных, как показано на рисунке 1.1."))
    body.append(drawing_paragraph("rIdSubjectArea", "subject_area_schema.svg", "8700000", "4785000"))
    body.append(paragraph("Рисунок 1.1 - Общая схема предметной области", style="Caption"))

    body.append(paragraph("1.2 Роли пользователей системы", style="Heading2"))
    for text in [
        "В проектируемой системе выделяются две пользовательские роли: трейдер и администратор, а также служебная роль simulator для данных, созданных режимом симуляции. Разделение ролей необходимо для разграничения пользовательских и управляющих функций. Обычный пользователь должен выполнять только операции, связанные с личным учебным счетом, а администратор должен иметь возможность управлять рынком и контролировать действия пользователей.",
        "Трейдер является основным пользователем сайта. Он проходит регистрацию, выполняет вход в систему, получает демонстрационный баланс, просматривает рынок криптовалют, выбирает актив и совершает учебные операции покупки или продажи. После выполнения операций трейдер может просматривать собственный портфель и историю своих сделок.",
        "Администратор отвечает за управление учебной биржей. В отличие от трейдера, он имеет доступ к административной панели. В ней отображается общая статистика: количество пользователей, количество сделок и оборот операций. Администратор может обновлять курс существующей криптовалюты, выбирать ручной или автоматический режим цены, добавлять новые активы, просматривать журнал операций всех пользователей и управлять симуляцией активности.",
        "Особенность административной роли заключается в том, что администратор работает не только со своими данными, а с данными системы в целом. Например, обычный пользователь видит только свою историю операций, а администратор видит общий журнал сделок с указанием пользователя, типа операции, актива, количества, цены и суммы.",
        "Роль simulator не предназначена для ручного входа на сайт. Она назначается пользователям, созданным автоматической симуляцией, чтобы отделить учебную нагрузку от реальных зарегистрированных пользователей. При очистке симуляции удаляются только записи с признаком isSimulated.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Роли пользователей системы представлены в таблице 1.1."))
    body.append(paragraph("Таблица 1.1 - Роли пользователей системы", style="Caption"))
    body.append(table([
        ["Роль", "Основные функции", "Ограничения"],
        ["Трейдер", "Регистрация, вход, просмотр рынка, покупка и продажа активов, просмотр портфеля и истории", "Не имеет доступа к административному управлению и операциям других пользователей"],
        ["Администратор", "Просмотр статистики, управление курсами, добавление активов, просмотр операций всех пользователей", "Не предназначен для обычной торговли как основной сценарий работы"],
        ["Simulator", "Создание учебных пользователей и сделок режимом симуляции", "Служебная роль, не используется для ручной авторизации"],
    ], widths=[1800, 5200, 3200], header=True))

    body.append(paragraph("1.3 Основные бизнес-процессы", style="Heading2"))
    for text in [
        "Бизнес-процесс в рамках данного курсового проекта понимается как последовательность действий пользователя или администратора, приводящая к изменению состояния системы. Для учебной криптовалютной биржи основными процессами являются регистрация, авторизация, просмотр рынка, выполнение сделки, просмотр портфеля, просмотр истории и административное управление активами.",
        "Процесс регистрации начинается с ввода имени, электронной почты и пароля. После проверки корректности данных создается новая учетная запись пользователя. Новому пользователю назначается роль трейдера и демонстрационный баланс. После успешной регистрации пользователь автоматически переходит в личный кабинет.",
        "Процесс авторизации выполняется при вводе email и пароля. Система проверяет наличие пользователя и соответствие пароля. Если данные корректны, создается текущая сессия пользователя. Если авторизуется администратор, он направляется в административную панель, а если обычный трейдер - на страницу обзора портфеля.",
        "Процесс покупки актива включает выбор криптовалюты, ввод количества, расчет стоимости операции и проверку доступного USD-баланса. Если денежных средств достаточно, система уменьшает USD-баланс, увеличивает количество монет в кошельке пользователя и фиксирует транзакцию. Если средств недостаточно, пользователь получает сообщение об ошибке.",
        "Процесс продажи актива аналогичен покупке, но проверяется не денежный баланс, а количество монет в кошельке. При успешной продаже количество монет уменьшается, а USD-баланс пользователя увеличивается на сумму сделки. Сведения о продаже сохраняются в таблице транзакций.",
        "Административные процессы включают изменение курса актива, добавление новой монеты, выбор источника цены и запуск симуляции активности. При изменении курса обновляется текущая цена и пополняется история цен. При добавлении монеты администратор указывает символ, название, начальную цену, уровень риска, описание и режим получения цены.",
        "Процесс получения рыночных данных выполняется через Python API. Сайт запрашивает свечи по выбранной торговой паре, сначала используется Binance Spot, затем Coinbase Exchange как запасной источник. Если внешние источники недоступны, графики строятся по локальной истории цен из SQLite.",
        "Процесс симуляции активности управляется вручную из админ-панели. Администратор задает количество симулируемых пользователей и сделок в минуту. Система не догоняет пропущенное время после закрытия сервера, поэтому после нового запуска генерация продолжается только с текущего момента.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Основные процессы системы приведены в таблице 1.2."))
    body.append(paragraph("Таблица 1.2 - Основные бизнес-процессы системы", style="Caption"))
    body.append(table([
        ["Процесс", "Участник", "Результат"],
        ["Регистрация", "Трейдер", "Создание учетной записи и демонстрационного баланса"],
        ["Авторизация", "Трейдер, администратор", "Создание пользовательской сессии и переход в соответствующий раздел"],
        ["Покупка актива", "Трейдер", "Уменьшение USD-баланса, увеличение количества монет, создание операции"],
        ["Продажа актива", "Трейдер", "Уменьшение количества монет, увеличение USD-баланса, создание операции"],
        ["Просмотр портфеля", "Трейдер", "Получение сведений о денежных средствах и криптоактивах"],
        ["Изменение курса", "Администратор", "Обновление цены актива и истории цен"],
        ["Автообновление курсов", "Система, администратор", "Получение цены из открытого источника и сохранение результата в SQLite"],
        ["Построение графика", "Трейдер", "Получение свечей через API и отображение графика на странице торговли"],
        ["Симуляция активности", "Администратор", "Создание отделенных симулируемых пользователей и операций"],
        ["Просмотр операций", "Администратор", "Контроль общего журнала пользовательских сделок"],
    ], widths=[2600, 2400, 5200], header=True))

    body.append(paragraph("1.4 Ограничения учебной модели", style="Heading2"))
    for text in [
        "Проект CryptoTrade является учебной моделью, поэтому в нем сознательно введены ограничения. Система может получать публичные рыночные данные из открытых API, но не обрабатывает банковские карты, не использует реальные кошельки и не выполняет настоящие финансовые операции. Все действия выполняются с демонстрационным балансом.",
        "Данные хранятся в локальной SQLite-базе site/cryptotrade.db. Такое решение выбрано для учебного проекта, потому что SQLite не требует установки отдельного сервера СУБД, но при этом предоставляет реальные таблицы, внешние ключи и постоянное хранение между запусками.",
        "SQLite является файловой СУБД и подходит для локального учебного проекта. Для промышленной эксплуатации криптовалютной биржи потребовалась бы серверная база данных, например PostgreSQL или MySQL, а также полноценная серверная авторизация, хеширование паролей и резервное копирование.",
        "Еще одним ограничением является отсутствие реального механизма безопасности. Пароли в учебной модели сохраняются в открытом виде, потому что целью проекта является демонстрация логики сайта, а не разработка промышленной системы защиты. В реальной системе потребовалось бы хэширование паролей, серверная авторизация, защита от подбора паролей и разграничение доступа на уровне серверной части.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Основные ограничения учебной модели представлены в таблице 1.3."))
    body.append(paragraph("Таблица 1.3 - Ограничения учебной модели", style="Caption"))
    body.append(table([
        ["Ограничение", "Причина использования", "Возможное развитие"],
        ["Демонстрационный баланс", "Безопасная имитация торговых операций", "Подключение платежной системы или тестовой серверной среды"],
        ["Хранение в SQLite", "Реальная файловая база данных без установки отдельного сервера СУБД", "Использование PostgreSQL или MySQL"],
        ["Зависимость автообновления от внешней сети", "Получение публичных рыночных данных из открытых источников", "Кэширование и несколько резервных поставщиков данных"],
        ["Упрощенная авторизация", "Демонстрация принципа входа и регистрации", "Серверная авторизация и хэширование паролей"],
        ["Отсутствие реальных кошельков", "Исключение финансовых рисков", "Интеграция с тестовой блокчейн-сетью"],
    ], widths=[2600, 3600, 4000], header=True))

    body.append(paragraph("1.5 Постановка задачи", style="Heading2"))
    for text in [
        "На основании анализа предметной области необходимо разработать сайт, который обеспечивает работу с учебным торговым счетом и демонстрирует основные функции криптовалютной биржи. Сайт должен быть понятен пользователю, иметь несколько связанных страниц, локальный Python API и обеспечивать сохранение данных в SQLite между посещениями.",
        "В практической части требуется реализовать регистрацию и авторизацию пользователей. Пользователь должен иметь возможность создать учетную запись, войти в систему и выйти из нее. Для проверки работы должны быть предусмотрены демонстрационные учетные записи трейдера и администратора.",
        "Пользовательская часть должна включать просмотр рынка криптовалют, выполнение операций покупки и продажи, отображение текущего портфеля, просмотр истории операций и расширенный график на базе свечных данных. Все операции должны сопровождаться проверкой доступного баланса или количества монет. При ошибке система должна выводить понятное сообщение.",
        "Административная часть должна предоставлять функции управления учебной биржей. Администратор должен видеть статистику системы, общий журнал операций пользователей, список активов, форму обновления курса, форму добавления новой монеты, настройки источника цены и управление симуляцией активности. Доступ к административному разделу должен быть ограничен ролью администратора.",
        "Для выполнения требований по базе данных необходимо спроектировать логическую модель не менее чем из пяти связанных сущностей и реализовать ее в SQLite. В текущем проекте используется семь таблиц: роли, пользователи, валюты, кошельки, транзакции, история цен и системные настройки. Такая структура позволяет показать связи между пользователями, активами, торговыми операциями и режимом симуляции.",
        "Итогом выполнения задачи должен стать работоспособный сайт с локальным Python-сервером, SQLite-базой, API, страницами политики конфиденциальности и пользовательского соглашения, а также пояснительная записка, содержащая анализ предметной области, проектирование данных, описание разработки, алгоритмы работы программы, блок-схему, тестирование, список сокращений, список источников и приложения.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("ГЛАВА 2. ПРОЕКТИРОВАНИЕ БАЗЫ ДАННЫХ", style="Heading1", page_break_before=True))
    body.append(paragraph("2.1 Требования к хранению данных", style="Heading2"))
    for text in [
        "База данных сайта CryptoTrade должна хранить сведения о пользователях, ролях, криптовалютных активах, кошельках пользователей, завершенных операциях, истории изменения курсов и системных настройках симуляции. Эти данные необходимы для авторизации, разграничения прав доступа, расчета портфеля, выполнения сделок, построения локальной fallback-истории цен и вывода отчетной информации в административной панели.",
        "Для учебного проекта используется логическая модель базы данных. Она описывается как набор связанных сущностей, аналогичных таблицам реляционной базы данных. В программной реализации данные сохраняются в SQLite-базе cryptotrade.db. Сайт обращается к базе через Python API в файле backend.py, что позволяет показать основные операции с данными: создание записей, чтение, изменение балансов и формирование истории операций.",
        "К хранению данных предъявляются следующие требования: каждая запись должна иметь уникальный идентификатор; пользователь должен относиться к одной роли; торговая операция должна быть связана с пользователем и выбранной криптовалютой; кошелек должен хранить количество конкретной монеты у конкретного пользователя; история операций должна сохраняться после обновления страницы; симулируемые данные должны отделяться от реальных; администратор должен иметь возможность просматривать операции всех пользователей.",
        "Дополнительно система должна проверять корректность данных перед сохранением. При регистрации проверяется уникальность email и минимальная длина пароля. При покупке проверяется достаточность USD-баланса, при продаже - достаточность количества монет в кошельке. Цена актива и количество в сделке должны быть больше нуля. Эти проверки защищают логическую целостность учебной базы данных.",
        "В SQLite создаются таблицы roles, users, currencies, wallets, transactions, price_history и system_settings. Таблицы связаны внешними ключами. В localStorage остаются только настройки браузера: тема интерфейса, текущая локальная сессия и служебная информация о последнем запросе курса.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("2.2 Описание сущностей", style="Heading2"))
    body.append(paragraph("В логической модели выделено шесть основных сущностей предметной области и служебная сущность настроек. Их назначение и состав полей приведены в таблице 2.1. Названия полей в таблице приведены в учебном SQL-подобном виде. В JavaScript-реализации часть полей записана в стиле camelCase: например, balance_usd соответствует balanceUsd, user_id соответствует userId, currency_id соответствует currencyId, price_mode соответствует priceMode, market_symbol соответствует marketSymbol, is_simulated соответствует isSimulated."))
    body.append(paragraph("Таблица 2.1 - Сущности базы данных и их поля", style="Caption"))
    body.append(table([
        ["Сущность", "Основные поля", "Назначение"],
        ["roles", "id, code, title", "Справочник ролей. В системе используются роли trader, admin и simulator. Роль определяет доступ к обычным страницам, административной панели или принадлежность к симуляции."],
        ["users", "id, role_id, name, email, password, balance_usd, created_at, is_simulated", "Пользователи сайта. Сущность хранит учетные данные, роль, имя пользователя, дату создания, учебный USD-баланс и признак симуляции."],
        ["currencies", "id, symbol, name, price, color, risk, description, price_mode, market_symbol, source, last_sync_at, last_sync_status, last_sync_message", "Криптовалютные активы рынка. Для каждого актива задаются символ, название, текущая цена, уровень риска, описание и источник обновления курса."],
        ["wallets", "id, user_id, currency_id, amount, updated_at, is_simulated", "Кошельки пользователей. Запись показывает, сколько конкретной криптовалюты принадлежит конкретному пользователю."],
        ["transactions", "id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated", "Завершенные операции. Сущность используется для истории пользователя и общего журнала в административной панели."],
        ["price_history", "id, currency_id, price, recorded_at, position", "История изменения курсов. Используется для локальной динамики, fallback-графиков и хранения последних сохраненных цен."],
        ["system_settings", "id, simulation_enabled, simulation_level, simulation_users_target, simulation_trades_per_minute, last_simulation_at, simulation_carry", "Служебные настройки режима симуляции активности: включение, число симулируемых пользователей и частота сделок."],
    ], widths=[1700, 3300, 5000], header=True))
    for text in [
        "Сущность roles нужна для разграничения прав доступа. Обычный трейдер может выполнять операции с собственным счетом, смотреть рынок, портфель и личную историю. Администратор дополнительно получает доступ к статистике, списку всех операций пользователей, обновлению курсов и добавлению новых активов. Роль simulator используется для пользователей, созданных режимом симуляции активности.",
        "Сущность users является центральной для пользовательской части сайта. При регистрации создается новая запись пользователя с ролью trader и стартовым балансом 10000 USD. При входе в систему данные пользователя сопоставляются с email и паролем, после чего идентификатор пользователя сохраняется в сессии.",
        "Сущность currencies хранит рыночные активы. В начальном наборе используются BTC, ETH, SOL, ADA, BNB, XRP, DOGE, AVAX, DOT, LINK, LTC и TRX. Администратор может добавить новую монету, задать ручной курс или включить автоматическое обновление по биржевой паре. Цена актива применяется при расчете суммы сделки и стоимости портфеля. На странице торговли данные используются для построения линейного графика или японских свечей с индикатором SMA.",
        "Сущность wallets связывает пользователя и криптовалюту. Если пользователь впервые покупает актив, запись кошелька создается автоматически. При покупке количество монет увеличивается, а при продаже уменьшается. Если количество становится близким к нулю, в интерфейсе такой актив не отображается в портфеле.",
        "Сущность transactions фиксирует торговый процесс. Так как в учебной модели каждая операция исполняется сразу, отдельная таблица заявок не используется. В транзакции сохраняются тип операции buy или sell, количество, цена, сумма, дата и признак симуляции.",
        "Сущность system_settings хранит состояние симуляции: включена ли она, сколько симулируемых пользователей должно быть создано, сколько сделок в минуту необходимо генерировать и какой дробный остаток сделок перенесен на следующий цикл. Это нужно для равномерной генерации без догоняющего выполнения после закрытия сервера.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("2.3 Связи между сущностями", style="Heading2"))
    body.append(paragraph("Связи между сущностями отражают, какие записи зависят друг от друга. Основные связи приведены в таблице 2.2."))
    body.append(paragraph("Таблица 2.2 - Связи между сущностями", style="Caption"))
    body.append(table([
        ["Связь", "Тип", "Описание"],
        ["users.role_id -> roles.id", "многие к одному", "Каждый пользователь имеет одну роль, а одна роль может быть назначена многим пользователям."],
        ["wallets.user_id -> users.id", "многие к одному", "У одного пользователя может быть несколько кошельков для разных криптовалют."],
        ["wallets.currency_id -> currencies.id", "многие к одному", "Одна криптовалюта может присутствовать в кошельках разных пользователей."],
        ["transactions.user_id -> users.id", "многие к одному", "История операций позволяет получить все сделки конкретного пользователя."],
        ["transactions.currency_id -> currencies.id", "многие к одному", "Операция связана с активом, по которому была выполнена сделка."],
        ["price_history.currency_id -> currencies.id", "многие к одному", "Для одного актива может храниться несколько исторических значений курса."],
        ["system_settings.id", "одна запись настроек", "Служебная запись main управляет параметрами симуляции активности."],
    ], widths=[3000, 2200, 4800], header=True))
    body.append(paragraph("На уровне интерфейса эти связи используются во всех основных разделах. На странице портфеля кошельки фильтруются по идентификатору текущего пользователя и связываются с таблицей активов для расчета стоимости. На странице истории транзакции фильтруются по пользователю и дополняются названием криптовалюты. В административной панели журнал транзакций выводится без фильтра по текущему пользователю, поэтому администратор видит операции всех зарегистрированных участников."))
    body.append(paragraph("2.4 Реализация базы данных в SQLite", style="Heading2"))
    body.append(paragraph("Физически данные размещаются в файле site/cryptotrade.db. База создается автоматически при запуске Python-сервера backend.py. Для работы используется стандартный модуль sqlite3, поэтому проект не требует установки внешней СУБД."))
    body.append(paragraph("Пользователи хранятся отдельно от торговых данных. При входе система читает список пользователей из SQLite, ищет совпадение по email и паролю, а затем записывает текущую локальную сессию в браузере. Валюты, кошельки, транзакции, история цен и настройки симуляции хранятся в отдельных таблицах."))
    body.append(paragraph("Python API предоставляет маршруты /api/state для чтения и сохранения состояния, /api/health для проверки работоспособности и /api/klines для получения рыночных свечей. Файл базы данных не отдается как статический ресурс: запросы к .db блокируются сервером. Это отделяет интерфейс сайта от физического файла базы данных."))
    body.append(paragraph("Для защиты уже созданных данных обновление состояния выполняется не полной перезаписью всех таблиц, а через добавление и обновление записей. При очистке симуляции удаляются только пользователи, кошельки и транзакции с признаком is_simulated. Реальные пользователи и реальные операции при этом сохраняются."))
    body.append(paragraph("SQLite подходит для курсовой работы, потому что является полноценной файловой базой данных с таблицами и внешними ключами. Ограничением является локальный режим работы: для промышленной биржи потребовались бы серверная СУБД, хеширование паролей, миграции, журналирование и резервное копирование."))
    body.append(paragraph("2.5 Схема базы данных", style="Heading2"))
    body.append(paragraph("На рисунке 2.1 показана схема базы данных проекта CryptoTrade. В ней отражены основные таблицы SQLite и связи между ними. Центральными сущностями являются users и currencies, так как через них связаны кошельки, транзакции и история цен. Таблица system_settings является служебной и хранит единственную запись настроек симуляции."))
    body.append(drawing_paragraph("rIdDbSchema", "db_schema.svg", "8700000", "4065000"))
    body.append(paragraph("Рисунок 2.1 - Схема базы данных", style="Caption"))

    body.append(paragraph("ГЛАВА 3. РАЗРАБОТКА САЙТА", style="Heading1", page_break_before=True))
    body.append(paragraph("3.1 Общая архитектура проекта", style="Heading2"))
    for text in [
        "Практическая часть курсового проекта реализована как локальное веб-приложение CryptoTrade. Пользователь работает с HTML-страницами в браузере, клиентская логика выполняется на JavaScript, визуальное оформление задается CSS, а постоянное хранение данных выполняется в SQLite-базе cryptotrade.db через Python backend/API.",
        "Проект запускается через файл start_cryptotrade.bat из корня проекта или напрямую командой python backend.py из папки site. После запуска Python-сервер открывает локальный адрес http://127.0.0.1:8000/index.html, отдает статические файлы сайта и обрабатывает API-запросы. Такой подход выбран потому, что браузер не может напрямую читать и изменять SQLite-файл, а серверная прослойка позволяет безопаснее отделить интерфейс от физической базы данных.",
        "Архитектура проекта разделена на три уровня. Первый уровень - представление: HTML-страницы index.html, dashboard.html, market.html, trade.html, portfolio.html, history.html, admin.html, privacy.html и terms.html. Второй уровень - клиентская логика в assets/js/app.js, где выполняются авторизация, расчеты, обновление интерфейса, торговые операции, работа с графиками и обращение к API. Третий уровень - backend.py, который инициализирует SQLite, отдает состояние приложения и получает свечные данные из внешних источников.",
        "Основной обмен между интерфейсом и сервером выполняется в формате JSON. Клиент загружает состояние через /api/state, после изменений отправляет обновленное состояние POST-запросом на /api/state, а для графиков запрашивает свечи через /api/klines. Благодаря этому страницы остаются обычными HTML-документами, но данные сохраняются не в localStorage как в ранней версии, а в полноценной файловой базе данных SQLite.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("Структура файлов проекта приведена в таблице 3.1."))
    body.append(paragraph("Таблица 3.1 - Структура файлов проекта", style="Caption"))
    body.append(table([
        ["Файл", "Назначение"],
        ["site/index.html", "Страница входа и регистрации"],
        ["site/dashboard.html", "Обзор портфеля пользователя"],
        ["site/market.html", "Рынок криптовалют и лента активности"],
        ["site/trade.html", "Покупка, продажа и расширенный график"],
        ["site/portfolio.html", "Портфель пользователя и распределение активов"],
        ["site/history.html", "История операций текущего пользователя"],
        ["site/admin.html", "Административная панель"],
        ["site/privacy.html", "Политика конфиденциальности"],
        ["site/terms.html", "Пользовательское соглашение"],
        ["site/assets/css/style.css", "Стили сайта, темная тема, адаптивная верстка"],
        ["site/assets/js/app.js", "Клиентская логика, торговля, графики, API-запросы"],
        ["site/backend.py", "Python API, статический сервер и работа с SQLite"],
        ["site/cryptotrade.db", "SQLite-база данных, создается и обновляется сервером"],
        ["site/README.md", "Краткая инструкция по запуску и описанию проекта"],
        ["start_cryptotrade.bat", "Запуск локального сервера и сайта из корня проекта"],
    ], widths=[3500, 5500], header=True))

    body.append(paragraph("3.2 Пользовательский интерфейс и навигация", style="Heading2"))
    for text in [
        "Интерфейс сайта построен как набор связанных страниц с общей навигацией. После входа пользователь видит верхнее меню: Обзор, Рынок, Торговля, Портфель, История. Для администратора дополнительно показывается пункт Админ. В правой части навигации отображается имя пользователя и кнопка выхода.",
        "На всех основных страницах добавлен футер с названием проекта и ссылками на политику конфиденциальности и пользовательское соглашение. Наличие этих страниц делает учебный сайт более похожим на реальный сервис: пользователь может увидеть, какие данные используются, где они хранятся и почему операции не являются настоящими финансовыми сделками.",
        "Визуальное оформление выполнено в темной теме. Для предотвращения белой вспышки при загрузке тема применяется в самом начале загрузки страницы. Переключение темы сохраняется в браузере как локальная настройка и не относится к предметной базе данных.",
        "Для связывания HTML и JavaScript используются data-атрибуты. Например, data-page определяет текущую страницу, data-login-form и data-register-form используются для форм входа и регистрации, data-trade-form - для торговой формы, data-admin-price-form - для формы обновления курса. Такой подход позволяет не привязывать JavaScript к случайным CSS-классам и делает структуру интерфейса более понятной.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("Страницы сайта приведены в таблице 3.2."))
    body.append(paragraph("Таблица 3.2 - Страницы сайта", style="Caption"))
    body.append(table([
        ["Страница", "Основные элементы", "Назначение"],
        ["index.html", "Форма входа, форма регистрации, демо-рынок, ссылки на документы", "Вход пользователя, регистрация трейдера и переход в личный раздел"],
        ["dashboard.html", "Метрики портфеля, график BTC, последние сделки, лента рынка", "Краткий обзор состояния пользователя после входа"],
        ["market.html", "Таблица активов, мини-графики, лента активности", "Просмотр доступных криптовалют, цен, риска и динамики"],
        ["trade.html", "Выбор монеты, расчет суммы, покупка/продажа, TradingView-график", "Выполнение учебных торговых операций"],
        ["portfolio.html", "Итоговая стоимость, USD-баланс, карточки активов", "Отображение текущих средств пользователя"],
        ["history.html", "Таблица операций пользователя", "Просмотр личной истории покупок и продаж"],
        ["admin.html", "Метрики, управление курсами, добавление монет, симуляция, журнал операций", "Административное управление учебной биржей"],
        ["privacy.html", "Текст политики конфиденциальности", "Описание учебного характера данных и хранения"],
        ["terms.html", "Текст пользовательского соглашения", "Фиксация правил использования сайта"],
    ], widths=[2200, 3600, 4200], header=True))

    body.append(paragraph("3.3 Авторизация, регистрация и управление сессией", style="Heading2"))
    for text in [
        "Страница index.html содержит два режима: вход и регистрацию. По умолчанию отображается форма входа, а форма регистрации открывается отдельной кнопкой. Такой интерфейс уменьшает визуальную перегрузку страницы и позволяет пользователю выполнить нужное действие без перехода на отдельную страницу.",
        "При регистрации пользователь вводит имя, email и пароль. JavaScript проверяет длину имени, наличие email, минимальную длину пароля и отсутствие пользователя с таким email. После успешной регистрации создается запись пользователя с ролью trader и стартовым балансом 10000 USD. Затем пользователь автоматически авторизуется и переходит на dashboard.html.",
        "При входе функция authenticate сопоставляет email и пароль с данными пользователей, полученными через API из SQLite. Если данные неверны, выводится сообщение об ошибке. Если вход успешен, идентификатор пользователя сохраняется в локальной сессии браузера, после чего выполняется переход: обычный трейдер открывает страницу обзора, администратор - административную панель.",
        "Проверка доступа выполняется при открытии каждой защищенной страницы. Если пользователь не вошел в систему, он перенаправляется на index.html. Если обычный трейдер пытается открыть admin.html, он возвращается на dashboard.html. Благодаря этому административные функции скрыты не только визуально, но и логически ограничены на уровне клиентского сценария.",
    ]:
        body.append(paragraph(text))
    body.append(placeholder("рисунок 3.1 - скриншот страницы входа и регистрации"))
    body.append(paragraph("Рисунок 3.1 - Страница входа и регистрации", style="Caption"))

    body.append(paragraph("3.4 Пользовательские страницы", style="Heading2"))
    for text in [
        "Страница dashboard.html является личным обзором пользователя. На ней отображаются общая стоимость портфеля, доступный USD-баланс и количество активов в портфеле. Дополнительно выводятся график динамики BTC, последние операции пользователя, краткая лента рынка и карточки популярных активов. Эта страница нужна как стартовая точка после входа.",
        "Страница market.html предназначена для просмотра рынка криптовалют. В таблице отображаются символ, название, текущая цена, изменение, уровень риска, источник цены и ссылка на торговлю выбранным активом. На этой же странице выводится лента активности, где смешиваются реальные и симулируемые операции, что позволяет показать движение учебного рынка.",
        "Страница portfolio.html показывает состояние активов пользователя. В верхней части выводятся общая стоимость, стоимость криптоактивов и свободные USD. Ниже формируются карточки монет, которые есть у пользователя: количество, рыночная стоимость и доля в криптовалютной части портфеля. Если активов нет, выводится пустое состояние с подсказкой.",
        "Страница history.html отображает личный журнал операций. В таблице выводятся дата, тип операции, актив, количество, цена, сумма и статус. В отличие от административной панели, обычный пользователь видит только свои транзакции, что соответствует разграничению доступа по ролям.",
    ]:
        body.append(paragraph(text))
    body.append(placeholder("рисунок 3.2 - скриншот страницы рынка"))
    body.append(paragraph("Рисунок 3.2 - Страница рынка", style="Caption"))
    body.append(placeholder("рисунок 3.3 - скриншот страницы портфеля"))
    body.append(paragraph("Рисунок 3.3 - Страница портфеля", style="Caption"))
    body.append(placeholder("рисунок 3.4 - скриншот истории операций"))
    body.append(paragraph("Рисунок 3.4 - История операций", style="Caption"))

    body.append(paragraph("3.5 Торговая страница и графики", style="Heading2"))
    for text in [
        "Страница trade.html является основным рабочим экраном трейдера. Пользователь выбирает криптовалюту, видит ее текущую цену, описание, уровень риска, доступный USD-баланс и количество выбранной монеты на кошельке. При вводе количества автоматически рассчитывается сумма операции.",
        "Покупка и продажа выполняются одной формой. При отправке формы определяется тип операции: buy или sell. Функция performTrade проверяет наличие пользователя и актива, корректность количества, положительную сумму сделки, достаточность USD при покупке и достаточность монет при продаже. Если проверка не пройдена, пользователь получает понятное сообщение об ошибке.",
        "При успешной покупке USD-баланс пользователя уменьшается, количество монет в кошельке увеличивается, а в таблицу transactions добавляется завершенная операция со статусом Исполнено. При продаже выполняется обратное изменение: количество монет уменьшается, USD-баланс увеличивается, а транзакция также сохраняется в истории. Отдельная таблица заявок не используется, потому что учебная сделка исполняется сразу.",
        "На торговой странице размещен расширенный график. Пользователь может выбрать тип отображения: линия или японские свечи, а также таймфрейм 1м, 5м, 15м или 1ч. Дополнительно можно включить или выключить индикатор SMA(5). Для построения графика используется TradingView Lightweight Charts, а если библиотека или внешние свечи недоступны, используется canvas-график и локальная история цен.",
        "Свечные данные загружаются через API /api/klines. Backend сначала обращается к Binance Spot, а при ошибке использует Coinbase Exchange как запасной источник. Полученные свечи применяются не только для большого графика на странице торговли, но и для мини-графиков на страницах обзора и рынка. Это делает отображение динамики более приближенным к реальным торговым терминалам.",
    ]:
        body.append(paragraph(text))
    body.append(placeholder("рисунок 3.5 - скриншот страницы торговли с графиком"))
    body.append(paragraph("Рисунок 3.5 - Страница торговли", style="Caption"))

    body.append(paragraph("3.6 Клиентская логика JavaScript", style="Heading2"))
    for text in [
        "Основная клиентская логика размещена в файле site/assets/js/app.js. Файл отвечает за нормализацию данных, чтение и сохранение состояния через API, авторизацию, регистрацию, расчеты портфеля, выполнение сделок, отображение страниц, построение графиков и работу административной панели.",
        "В JavaScript-коде используется единая структура состояния: список пользователей и объект data, включающий currencies, wallets, transactions и settings. При загрузке страницы состояние получается из SQLite через backend.py, а после изменений отправляется обратно на сервер. Для удобства интерфейса поля преобразуются в camelCase, например balance_usd становится balanceUsd.",
        "Отдельное внимание уделено производительности торговой страницы и страниц с графиками. Свечи кэшируются на клиенте, повторные запросы ограничиваются интервалом, а при изменении количества в торговой форме пересчитывается только сумма сделки без полной перерисовки страницы. Это уменьшает задержки при работе пользователя.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Основные функции JavaScript приведены в таблице 3.3."))
    body.append(paragraph("Таблица 3.3 - Основные функции JavaScript", style="Caption"))
    body.append(table([
        ["Функция", "Назначение"],
        ["initLoginForm", "Обработка формы входа и переход в нужный раздел"],
        ["initRegisterForm", "Проверка регистрационных данных и создание нового трейдера"],
        ["initSessionUi", "Проверка сессии, прав доступа, навигации и выхода"],
        ["performTrade", "Проверка и выполнение покупки или продажи"],
        ["renderDashboardPage", "Отображение обзора портфеля и последних операций"],
        ["renderMarketTable", "Формирование таблицы криптовалют на странице рынка"],
        ["initTradePage", "Инициализация торговой формы и графика"],
        ["fetchMarketCandlesAsync", "Загрузка свечей через /api/klines и кэширование результата"],
        ["drawTradingViewChart", "Построение расширенного графика с линией, свечами и SMA"],
        ["renderPortfolioPage", "Расчет и отображение портфеля пользователя"],
        ["renderHistoryPage", "Вывод личной истории операций"],
        ["initAdminPage", "Настройка форм админ-панели"],
        ["syncMarketPrices", "Обновление авто-курсов из Binance Spot"],
        ["updateSimulationSettings", "Сохранение ручных параметров симуляции"],
        ["runSimulationTick", "Генерация симулируемых сделок по заданной частоте"],
    ], widths=[3300, 6200], header=True))

    body.append(paragraph("3.7 Backend/API и работа с SQLite", style="Heading2"))
    for text in [
        "Серверная часть реализована в файле site/backend.py с использованием стандартных модулей Python: http.server для локального HTTP-сервера, sqlite3 для работы с базой данных, urllib для обращения к внешним источникам свечей и json для обмена данными с клиентом.",
        "При запуске backend.py вызывается init_db. Эта функция создает таблицы roles, users, currencies, wallets, transactions, price_history и system_settings, если они отсутствуют. Также добавляются демонстрационные роли, начальный набор криптовалют и служебная запись настроек симуляции.",
        "Для совместимости с предыдущими версиями предусмотрена миграция migrate_transactions_without_orders. Если в старой базе присутствовала таблица orders или поле order_id в transactions, данные переносятся в новую структуру, где остается только таблица transactions. Это устраняет дублирование, потому что в учебной модели сделка исполняется сразу.",
        "Маршрут GET /api/state возвращает полное состояние приложения: пользователей, валюты, кошельки, транзакции и настройки. Маршрут POST /api/state принимает измененное состояние и сохраняет его в SQLite. При сохранении используется не полная потеря старых данных, а добавление или обновление записей; отдельно удаляются только симулируемые записи, если они больше не присутствуют в состоянии.",
        "Маршрут GET /api/health используется для простой проверки работоспособности сервера. Маршрут GET /api/klines получает свечи для выбранной торговой пары и таймфрейма. Если запрошен файл с расширением .db, сервер возвращает запрет, чтобы файл базы данных не отдавался как статический ресурс.",
    ]:
        body.append(paragraph(text))
    body.append(paragraph("Основные API-маршруты приведены в таблице 3.4."))
    body.append(paragraph("Таблица 3.4 - API backend.py", style="Caption"))
    body.append(table([
        ["Маршрут", "Метод", "Назначение"],
        ["/api/state", "GET", "Получение текущего состояния из SQLite"],
        ["/api/state", "POST", "Сохранение пользователей, данных рынка, транзакций и настроек"],
        ["/api/klines", "GET", "Получение свечей Binance Spot или Coinbase Exchange"],
        ["/api/health", "GET", "Проверка запуска сервера и пути к базе данных"],
        ["*.db", "GET", "Запрещенный доступ к файлу базы данных"],
    ], widths=[2600, 1600, 5600], header=True))

    body.append(paragraph("3.8 Административная панель и симуляция", style="Heading2"))
    for text in [
        "Страница admin.html доступна только пользователю с ролью admin. В верхней части панели отображаются четыре показателя: количество пользователей, количество завершенных сделок, общий оборот и состояние симуляции. Ниже расположены формы управления курсом, добавления монеты, настройки симуляции, журнал операций пользователей и таблица активов рынка.",
        "Форма Курс и источник позволяет выбрать актив, изменить цену, указать режим цены и биржевую пару. В ручном режиме цена задается администратором и не перезаписывается автообновлением. В автоматическом режиме цена обновляется по публичной паре Binance Spot, например BTCUSDT. Для ручного запуска обновления предусмотрена кнопка Обновить авто-курсы.",
        "Форма Добавить монету позволяет расширить список активов. Администратор вводит символ, название, начальную цену, уровень риска, описание, режим цены и при необходимости биржевую пару. После проверки данные добавляются в currencies, а новая монета появляется на рынке и в торговой форме.",
        "Режим симуляции активности переделан на ручной ввод параметров. Администратор задает, сколько симулируемых пользователей должно существовать и сколько сделок в минуту нужно создавать. Симулируемые пользователи получают роль simulator, а связанные кошельки и транзакции помечаются признаком isSimulated.",
        "Симуляция не догоняет пропущенное время после закрытия сервера. Если сайт или backend были выключены, после нового запуска генерация продолжается с текущего момента. При отключении симуляции удаляются только симулируемые пользователи, кошельки и транзакции, а реальные учетные записи и реальные сделки сохраняются.",
    ]:
        body.append(paragraph(text))
    body.append(placeholder("рисунок 3.6 - скриншот административной панели"))
    body.append(paragraph("Рисунок 3.6 - Административная панель", style="Caption"))

    body.append(paragraph("3.9 Оформление, футер и документы", style="Heading2"))
    for text in [
        "Визуальное оформление проекта находится в файле site/assets/css/style.css. Стиль сайта выполнен в темной теме, потому что такая цветовая схема привычна для финансовых и торговых интерфейсов. На страницах используются панели, таблицы, карточки показателей, компактные формы и цветовые метки риска.",
        "Для адаптивности применяются гибкие сетки и ограничения ширины. Карточки рынка и портфеля перестраиваются в зависимости от ширины экрана, таблицы сохраняют читаемость, а формы остаются доступными на небольших экранах. Это важно, потому что пользователь может открыть учебный сайт как на ноутбуке, так и на мониторе с другой шириной.",
        "Футер присутствует на публичных и защищенных страницах. В нем указано название проекта CryptoTrade и размещены ссылки на privacy.html и terms.html. Политика конфиденциальности объясняет, какие учебные данные используются и где они хранятся. Пользовательское соглашение фиксирует, что операции являются демонстрационными и не имеют финансовой силы.",
        "Юридические страницы не требуют авторизации и доступны как до входа, так и после него. Это сделано специально: пользователь может ознакомиться с правилами до регистрации. Такие страницы не являются обязательными для простой учебной страницы, но делают проект более завершенным и похожим на реальный веб-сервис.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("3.10 Алгоритмы работы программы", style="Heading2"))
    for text in [
        "Основной алгоритм работы сайта начинается с запуска локального сервера. Backend создает или открывает SQLite-базу, проверяет наличие таблиц, добавляет начальные роли и активы, после чего начинает обслуживать HTTP-запросы. Пользователь открывает index.html и выполняет вход или регистрацию.",
        "После авторизации клиент загружает состояние через API, отображает нужную страницу и разрешает пользователю выполнить действие. При покупке или продаже выполняется проверка средств, изменение баланса и кошелька, создание транзакции и сохранение изменений в SQLite. После сохранения интерфейс обновляет портфель, историю и последние операции.",
        "Алгоритм обновления графиков включает выбор актива, определение торговой пары, запрос свечей через /api/klines, нормализацию данных и построение графика. Если API возвращает ошибку или внешняя сеть недоступна, сайт использует локальные значения price_history, поэтому графический блок остается работоспособным.",
        "Алгоритм симуляции использует настройки из system_settings. При включенной симуляции приложение рассчитывает, сколько сделок нужно создать за прошедший короткий интервал, генерирует операции равномерно и сохраняет дробный остаток в simulation_carry. При перезапуске сервера старое время не компенсируется, что предотвращает резкий выброс операций после простоя.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("ГЛАВА 4. ТЕСТИРОВАНИЕ", style="Heading1", page_break_before=True))
    body.append(paragraph("4.1 Методика тестирования", style="Heading2"))
    for text in [
        "Тестирование сайта CryptoTrade выполнялось методом функциональной проверки пользовательских и административных сценариев. Основная цель тестирования состояла в том, чтобы убедиться, что сайт корректно выполняет вход, регистрацию, торговые операции, сохранение данных в SQLite, построение графиков, работу API и отделение симулируемых записей от реальных данных.",
        "Проверка проводилась в локальной среде. Сайт запускался через start_cryptotrade.bat или командой python backend.py из папки site. После запуска открывался адрес http://127.0.0.1:8000/index.html. Такой способ запуска соответствует фактической архитектуре проекта, потому что HTML-страницы обращаются к Python API, а данные сохраняются в SQLite-базе site/cryptotrade.db.",
        "Тестирование выполнялось вручную по контрольным сценариям. Для каждого сценария задавались начальные условия, выполнялось действие пользователя или администратора, затем проверялся ожидаемый результат на странице и в состоянии приложения. Отдельно проверялись ошибочные ситуации: неверный пароль, недостаточный USD-баланс, попытка продажи без монет и недоступность внешних свечных данных.",
        "При тестировании использовались демонстрационные учетные записи: student@cryptotrade.local для трейдера и admin@cryptotrade.local для администратора. Также проверялась регистрация нового пользователя. Для административных сценариев использовалась роль admin, а для проверки симуляции - служебные пользователи с ролью simulator.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("Тестовая среда приведена в таблице 4.1."))
    body.append(paragraph("Таблица 4.1 - Тестовая среда", style="Caption"))
    body.append(table([
        ["Параметр", "Значение"],
        ["Режим запуска", "Локальный сервер backend.py или start_cryptotrade.bat"],
        ["Адрес сайта", "http://127.0.0.1:8000/index.html"],
        ["База данных", "site/cryptotrade.db"],
        ["Основные технологии", "HTML, CSS, JavaScript, Python, SQLite"],
        ["Проверяемые API", "/api/state, /api/klines, /api/health"],
        ["Демо-трейдер", "student@cryptotrade.local / student123"],
        ["Демо-администратор", "admin@cryptotrade.local / admin123"],
    ], widths=[3000, 6500], header=True))

    body.append(paragraph("4.2 Направления проверки", style="Heading2"))
    for text in [
        "Проверка авторизации и регистрации была направлена на подтверждение того, что пользователь может войти в систему, зарегистрировать новый аккаунт, выйти из системы и не получить доступ к защищенным страницам без сессии. Дополнительно проверялось, что обычный трейдер не может открыть административную панель.",
        "Проверка торговых операций включала покупку и продажу активов. Для покупки контролировалось уменьшение USD-баланса и увеличение количества монет в кошельке. Для продажи проверялось обратное изменение: уменьшение количества монет и увеличение USD-баланса. В обоих случаях проверялось создание записи в transactions.",
        "Проверка хранения данных была связана с SQLite. После регистрации, покупки или продажи выполнялся перезапуск backend.py, затем сайт открывался повторно. Если данные пользователя, кошелька и истории операций сохранялись, сценарий считался выполненным.",
        "Проверка графиков включала отображение мини-графиков на страницах обзора и рынка, а также расширенного графика на странице торговли. Проверялись переключение типа графика, таймфрейма и индикатора SMA. Также проверялось, что при недоступности внешних свечей сайт использует fallback-историю из price_history.",
        "Проверка административной панели включала просмотр статистики, обновление ручного курса, настройку автоматического режима цены, добавление новой монеты, запуск обновления курсов, просмотр операций всех пользователей и настройку симуляции активности.",
        "Проверка симуляции была выделена отдельно, потому что симулируемые данные не должны повреждать реальные данные. Проверялось создание пользователей с ролью simulator, генерация заданного количества сделок в минуту, отсутствие догоняющей генерации после перезапуска сервера и удаление только записей с признаком isSimulated при отключении симуляции.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("4.2 Тестовые сценарии", style="Heading2"))
    body.append(paragraph("Результаты тестирования приведены в таблице 4.2."))
    body.append(paragraph("Таблица 4.2 - Тестирование сайта", style="Caption"))
    body.append(table([
        ["№", "Проверка", "Действие", "Ожидаемый результат", "Статус"],
        ["1", "Запуск сервера", "Запустить start_cryptotrade.bat или python backend.py", "Открывается локальный сервер, доступен index.html", "Выполнено"],
        ["2", "Проверка /api/health", "Открыть /api/health", "Возвращается JSON с ok=true и путем к базе данных", "Выполнено"],
        ["3", "Вход трейдера", "Ввести student@cryptotrade.local и student123", "Открывается dashboard.html", "Выполнено"],
        ["4", "Вход администратора", "Ввести admin@cryptotrade.local и admin123", "Открывается admin.html", "Выполнено"],
        ["5", "Неверный пароль", "Ввести неправильный пароль", "Появляется сообщение об ошибке", "Выполнено"],
        ["6", "Регистрация пользователя", "Создать новый аккаунт на index.html", "Создается трейдер с балансом 10000 USD", "Выполнено"],
        ["7", "Защита админ-панели", "Открыть admin.html под трейдером", "Пользователь перенаправляется на dashboard.html", "Выполнено"],
        ["8", "Загрузка состояния", "Открыть страницу после входа", "Данные пользователей, валют и кошельков загружаются через /api/state", "Выполнено"],
        ["9", "Покупка при достаточном балансе", "Купить доступное количество BTC или другой монеты", "USD уменьшается, кошелек увеличивается, создается transaction", "Выполнено"],
        ["10", "Покупка при недостаточном балансе", "Указать слишком большое количество монет", "Операция не выполняется, выводится ошибка", "Выполнено"],
        ["11", "Продажа при наличии монет", "Продать часть купленного актива", "Количество монет уменьшается, USD увеличивается", "Выполнено"],
        ["12", "Продажа без монет", "Попробовать продать актив, которого нет в кошельке", "Операция блокируется, выводится ошибка", "Выполнено"],
        ["13", "История пользователя", "Открыть history.html после сделки", "В таблице отображается личная операция пользователя", "Выполнено"],
        ["14", "Портфель", "Открыть portfolio.html после покупки", "Отображаются активы, стоимость и доли портфеля", "Выполнено"],
        ["15", "Перезапуск backend.py", "Закрыть и снова запустить сервер", "Пользователи, кошельки и транзакции сохраняются в cryptotrade.db", "Выполнено"],
        ["16", "Ручное изменение курса", "В admin.html изменить цену выбранного актива", "Цена обновляется, история цен пополняется", "Выполнено"],
        ["17", "Добавление монеты", "Заполнить форму добавления актива", "Новая монета появляется на рынке и в торговой форме", "Выполнено"],
        ["18", "Автообновление курсов", "Включить авто-режим и нажать обновление", "Цена обновляется по Binance Spot или выводится понятное сообщение", "Выполнено"],
        ["19", "Расширенный график", "Открыть trade.html и переключить тип графика", "Отображаются линия или японские свечи", "Выполнено"],
        ["20", "Таймфрейм и SMA", "Сменить таймфрейм и выключить/включить SMA", "График перестраивается без перезагрузки страницы", "Выполнено"],
        ["21", "Fallback-график", "Открыть график при недоступных внешних свечах", "Используется локальная история price_history", "Выполнено"],
        ["22", "Настройка симуляции", "Задать пользователей и сделки в минуту", "Создаются пользователи simulator и симулируемые сделки", "Выполнено"],
        ["23", "Нет догоняющей симуляции", "Перезапустить сервер после простоя", "Сделки не создаются пачкой за время простоя", "Выполнено"],
        ["24", "Отключение симуляции", "Выключить симуляцию в admin.html", "Удаляются только isSimulated-записи, реальные данные сохраняются", "Выполнено"],
        ["25", "Политика и соглашение", "Открыть privacy.html и terms.html из футера", "Страницы доступны без авторизации", "Выполнено"],
        ["26", "Запрет доступа к базе", "Попробовать открыть файл .db через сервер", "Сервер возвращает запрет доступа к базе как к статическому файлу", "Выполнено"],
    ], widths=[700, 2300, 3300, 4200, 1300], header=True))

    body.append(paragraph("4.4 Анализ результатов тестирования", style="Heading2"))
    for text in [
        "По результатам проверки основные пользовательские сценарии выполнены успешно. Трейдер может зарегистрироваться, войти в систему, просматривать рынок, выполнять покупку и продажу, видеть портфель и историю операций. Ошибочные сценарии также обрабатываются корректно: при неверном пароле, недостаточном USD-балансе или нехватке монет система не изменяет данные и выводит сообщение.",
        "Проверка SQLite подтвердила, что данные сохраняются между запусками backend.py. После перезапуска сервера пользователи, кошельки, транзакции, активы и настройки симуляции остаются доступными. Это подтверждает переход проекта от хранения данных в браузере к полноценной файловой базе данных.",
        "Проверка API показала, что клиентская часть получает состояние через /api/state, сохраняет изменения POST-запросом на /api/state и использует /api/klines для получения свечей. При отсутствии внешних данных интерфейс продолжает работать за счет fallback-истории, поэтому отказ внешнего источника не блокирует торговые страницы.",
        "Проверка административной панели подтвердила возможность управлять активами, обновлять курсы, добавлять монеты и просматривать операции всех пользователей. Режим симуляции работает отдельно от реальных данных: записи получают признак isSimulated и могут быть удалены без потери реальных пользователей и транзакций.",
        "В результате тестирования критических ошибок, мешающих выполнению основных функций курсового проекта, не обнаружено. Оставшиеся ограничения связаны с учебным характером системы: пароли не хешируются, внешние рыночные данные зависят от доступности публичных API, а SQLite используется как локальная файловая база данных, а не промышленная серверная СУБД.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("ЗАКЛЮЧЕНИЕ", style="Heading1", page_break_before=True))
    for text in [
        "В результате выполнения курсового проекта была достигнута поставленная цель: разработан сайт CryptoTrade для учебной симуляции торговли криптовалютой. Сайт позволяет пользователю зарегистрироваться, войти в систему, просматривать рынок активов, выполнять учебные операции покупки и продажи, анализировать портфель и просматривать историю сделок.",
        "В ходе работы был выполнен анализ предметной области и определены основные роли системы: трейдер, администратор и служебная роль simulator для данных, созданных режимом симуляции. Были описаны основные бизнес-процессы: регистрация, авторизация, просмотр рынка, выполнение сделки, просмотр портфеля, просмотр истории, управление курсами, добавление активов и симуляция активности.",
        "Для проекта разработана логическая и физическая модель базы данных. Реализация выполнена на SQLite в файле cryptotrade.db. В базе используются связанные таблицы roles, users, currencies, wallets, transactions, price_history и system_settings. Такая структура соответствует требованию о наличии не менее пяти связанных сущностей и позволяет хранить пользователей, активы, кошельки, операции, историю цен и настройки симуляции.",
        "Проект был переведен с хранения данных в localStorage на локальный Python backend/API и SQLite-базу. Данные пользователей, кошельков, транзакций, цен и настроек симуляции сохраняются между запусками сервера. Отдельная таблица orders не используется, так как учебные сделки исполняются сразу и фиксируются в transactions.",
        "Пользовательская часть сайта включает страницы входа и регистрации, обзора, рынка, торговли, портфеля и истории операций. На странице торговли реализована форма покупки и продажи с проверкой достаточности USD или монет. После успешной операции обновляется баланс, изменяется кошелек и создается запись транзакции.",
        "В проект добавлены расширенные графики на базе TradingView Lightweight Charts. Графики поддерживают линию и японские свечи, несколько таймфреймов и индикатор SMA(5). Свечные данные загружаются через API из открытых источников Binance Spot и Coinbase Exchange, а при недоступности сети используется локальная fallback-история цен.",
        "Административная часть предоставляет функции контроля учебной биржи: просмотр статистики, общий журнал операций пользователей, список активов, ручное изменение цены, автоматическое обновление курсов, добавление новых монет и управление симуляцией активности. Симуляция настраивается вручную по количеству пользователей и числу сделок в минуту, а симулируемые записи отделяются от реальных признаком isSimulated.",
        "Дополнительно были добавлены футер, политика конфиденциальности и пользовательское соглашение. Эти страницы фиксируют учебный характер проекта, отсутствие реальных финансовых операций и особенности локального хранения данных. Темная тема и устранение белой вспышки при загрузке улучшают визуальное восприятие интерфейса.",
        "Проведенное тестирование подтвердило работоспособность основных функций сайта: авторизации, регистрации, торговли, портфеля, истории, административной панели, SQLite-хранения, API, графиков, fallback-истории, симуляции и страниц документов. Ошибочные сценарии, такие как неверный пароль, недостаточный баланс и попытка продажи отсутствующих монет, обрабатываются корректно.",
        "Разработанный проект соответствует требованиям курсовой работы: содержит сайт и пояснительную записку, авторизацию и регистрацию, связанную модель данных, базу данных, административную часть, блок-схему, схему базы данных и результаты тестирования. Проект может быть развит дальше за счет хеширования паролей, перехода на серверную СУБД, добавления миграций, резервного копирования и более строгой серверной авторизации.",
    ]:
        body.append(paragraph(text))

    body.append(paragraph("СПИСОК СОКРАЩЕНИЙ", style="Heading1", page_break_before=True))
    for abbr in [
        "БД - база данных.",
        "ПО - программное обеспечение.",
        "ПЗ - пояснительная записка.",
        "ИС - информационная система.",
        "СУБД - система управления базами данных.",
        "SQL - язык структурированных запросов.",
        "HTML - язык гипертекстовой разметки.",
        "CSS - каскадные таблицы стилей.",
        "JS - JavaScript.",
        "DOM - объектная модель документа.",
        "UI - пользовательский интерфейс.",
        "UX - пользовательский опыт.",
        "API - программный интерфейс приложения.",
        "HTTP - протокол передачи гипертекста.",
        "URL - унифицированный указатель ресурса.",
        "JSON - текстовый формат обмена структурированными данными.",
        "CRUD - операции создания, чтения, изменения и удаления данных.",
        "GET - HTTP-метод получения данных.",
        "POST - HTTP-метод отправки данных.",
        "REST - архитектурный стиль построения веб-API.",
        "Backend - серверная часть приложения.",
        "Frontend - клиентская часть приложения.",
        "SQLite - файловая реляционная система управления базами данных.",
        "DB - database, база данных.",
        "CSV - текстовый формат табличных данных с разделителями.",
        "Kline - свечная запись рыночных данных.",
        "OHLC - open, high, low, close; цены открытия, максимума, минимума и закрытия свечи.",
        "SMA - скользящая средняя.",
        "SMA(5) - скользящая средняя по пяти значениям.",
        "USD - доллар США.",
        "BTC - Bitcoin.",
        "ETH - Ethereum.",
        "SOL - Solana.",
        "ADA - Cardano.",
        "BNB - BNB.",
        "XRP - XRP Ledger.",
        "DOGE - Dogecoin.",
        "AVAX - Avalanche.",
        "DOT - Polkadot.",
        "LINK - Chainlink.",
        "LTC - Litecoin.",
        "TRX - TRON.",
        "BTCUSDT - торговая пара Bitcoin к Tether USD на бирже.",
        "ETHUSDT - торговая пара Ethereum к Tether USD на бирже.",
        "localStorage - локальное хранилище браузера.",
        "Fallback - резервный вариант работы при недоступности основного источника.",
        "TradingView Lightweight Charts - библиотека для построения финансовых графиков.",
        "Binance Spot - спотовый рынок Binance.",
        "Coinbase Exchange - биржевая платформа Coinbase.",
    ]:
        body.append(paragraph(abbr))

    body.append(paragraph("СПИСОК ИСТОЧНИКОВ", style="Heading1", page_break_before=True))
    sources = [
        "ГОСТ 2.105-95. Единая система конструкторской документации. Общие требования к текстовым документам.",
        "ГОСТ 19.101-77. Единая система программной документации. Виды программ и программных документов.",
        "ГОСТ 19.701-90. Единая система программной документации. Схемы алгоритмов, программ, данных и систем. Условные обозначения и правила выполнения.",
        "Binance Open Platform. Spot API Market Data Endpoints [Электронный ресурс]. URL: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints (дата обращения: 11.06.2026).",
        "Coinbase Developer Documentation. Get product candles [Электронный ресурс]. URL: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles (дата обращения: 11.06.2026).",
        "MDN Web Docs. Canvas API [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API (дата обращения: 11.06.2026).",
        "MDN Web Docs. CSS: Cascading Style Sheets [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/CSS (дата обращения: 11.06.2026).",
        "MDN Web Docs. Fetch API [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API (дата обращения: 11.06.2026).",
        "MDN Web Docs. HTML: HyperText Markup Language [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/HTML (дата обращения: 11.06.2026).",
        "MDN Web Docs. JavaScript [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/JavaScript (дата обращения: 11.06.2026).",
        "MDN Web Docs. Window: localStorage property [Электронный ресурс]. URL: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage (дата обращения: 11.06.2026).",
        "Python Documentation. http.server - HTTP servers [Электронный ресурс]. URL: https://docs.python.org/3/library/http.server.html (дата обращения: 11.06.2026).",
        "Python Documentation. json - JSON encoder and decoder [Электронный ресурс]. URL: https://docs.python.org/3/library/json.html (дата обращения: 11.06.2026).",
        "Python Documentation. sqlite3 - DB-API 2.0 interface for SQLite databases [Электронный ресурс]. URL: https://docs.python.org/3/library/sqlite3.html (дата обращения: 11.06.2026).",
        "SQLite Documentation [Электронный ресурс]. URL: https://www.sqlite.org/docs.html (дата обращения: 11.06.2026).",
        "TradingView Lightweight Charts Documentation [Электронный ресурс]. URL: https://tradingview.github.io/lightweight-charts/ (дата обращения: 11.06.2026).",
    ]
    for index, source in enumerate(sources, 1):
        body.append(paragraph(f"{index}. {source}"))

    body.append(paragraph("ПРИЛОЖЕНИЕ А", style="Heading1", page_break_before=True))
    body.append(paragraph("Описание файлов и текст программы", style="Title"))
    body.append(paragraph("Описание структуры проекта и полный текст программы вынесены в отдельный файл приложения: PZ/Приложение_А_Описание_файлов_и_текст_программы.docx. Черновая Markdown-версия приложения хранится в файле PZ/Приложение_А_Описание_файлов_и_текст_программы.md."))
    body.append(paragraph("В приложении А приведены назначение файлов сайта, командный файл запуска, Python backend/API, HTML-страницы, CSS-стили и JavaScript-код клиентской части. Служебные runtime-файлы, включая SQLite-базу site/cryptotrade.db и каталог __pycache__, в листинг не включаются."))

    body.append(paragraph("ПРИЛОЖЕНИЕ Б", style="Heading1", page_break_before=True))
    body.append(paragraph("Блок-схема алгоритма работы программы", style="Title"))
    body.append(paragraph("Блок-схема алгоритма работы программы вынесена в отдельный файл приложения: PZ/Приложение_Б_Блок-схема.docx. Исходное описание схемы хранится в файле PZ/block_scheme.mmd, а графическое представление дополнительно сохранено в файле PZ/Приложение_Б_Блок-схема.svg."))

    body.append(paragraph("ПРИЛОЖЕНИЕ В", style="Heading1", page_break_before=True))
    body.append(paragraph("Схема базы данных и экранные формы", style="Title"))
    body.append(placeholder("вставить схему данных из PZ/data_model.md и скриншоты страниц сайта"))

    body.append(section_properties(main=True))
    doc.append(body)
    return doc


def rels_root():
    root = etree.Element("Relationships", nsmap={None: PKG_REL})
    rel = etree.SubElement(root, "Relationship")
    rel.set("Id", "rId1")
    rel.set("Type", f"{DOC_REL}/officeDocument")
    rel.set("Target", "word/document.xml")
    return root


def doc_rels():
    root = etree.Element("Relationships", nsmap={None: PKG_REL})
    for rel_id, target in [("rIdFooterFirst", "footer1.xml"), ("rIdFooterDefault", "footer2.xml")]:
        rel = etree.SubElement(root, "Relationship")
        rel.set("Id", rel_id)
        rel.set("Type", f"{DOC_REL}/footer")
        rel.set("Target", target)
    rel = etree.SubElement(root, "Relationship")
    rel.set("Id", "rIdSubjectArea")
    rel.set("Type", f"{DOC_REL}/image")
    rel.set("Target", "media/subject_area_schema.svg")
    rel = etree.SubElement(root, "Relationship")
    rel.set("Id", "rIdDbSchema")
    rel.set("Type", f"{DOC_REL}/image")
    rel.set("Target", "media/db_schema.svg")
    return root


def content_types():
    root = etree.Element("Types", nsmap={None: CONTENT_TYPES})
    for ext, ctype in [
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
        ("svg", "image/svg+xml"),
    ]:
        default = etree.SubElement(root, "Default")
        default.set("Extension", ext)
        default.set("ContentType", ctype)
    for part, ctype in [
        ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
        ("/word/footer1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"),
        ("/word/footer2.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"),
    ]:
        override = etree.SubElement(root, "Override")
        override.set("PartName", part)
        override.set("ContentType", ctype)
    return root


def settings_doc():
    root = el("w:settings")
    root.append(el("w:updateFields", {"w:val": "true"}))
    return root


def write_part(zf: ZipFile, path: str, node):
    xml = etree.tostring(node, xml_declaration=True, encoding="UTF-8", standalone="yes")
    zf.writestr(path, xml)


def write_docx(path: Path):
    SUBJECT_AREA_SVG_PATH.write_text(subject_area_svg(), encoding="utf-8")
    DB_SCHEMA_SVG_PATH.write_text(db_schema_svg(), encoding="utf-8")
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        write_part(zf, "[Content_Types].xml", content_types())
        write_part(zf, "_rels/.rels", rels_root())
        write_part(zf, "word/_rels/document.xml.rels", doc_rels())
        write_part(zf, "word/document.xml", document_doc())
        write_part(zf, "word/styles.xml", style_doc())
        write_part(zf, "word/settings.xml", settings_doc())
        write_part(zf, "word/footer1.xml", footer_doc("first"))
        write_part(zf, "word/footer2.xml", footer_doc("default"))
        zf.writestr("word/media/subject_area_schema.svg", SUBJECT_AREA_SVG_PATH.read_text(encoding="utf-8"))
        zf.writestr("word/media/db_schema.svg", DB_SCHEMA_SVG_PATH.read_text(encoding="utf-8"))


def next_version_path() -> Path:
    pattern = re.compile(r"^ПЗ_(\d{3})_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.docx$")
    numbers = []

    for path in PZ_DIR.glob("ПЗ_*.docx"):
        match = pattern.match(path.name)

        if match:
            numbers.append(int(match.group(1)))

    version = max(numbers, default=0) + 1
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return PZ_DIR / f"ПЗ_{version:03d}_{timestamp}.docx"


def main():
    target = next_version_path()
    write_docx(target)
    print(target)


if __name__ == "__main__":
    main()
