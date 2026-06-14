from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


PZ_DIR = Path(__file__).resolve().parent
BASE_NAME = "Приложение_Б_Блок-схема"
SVG_PATH = PZ_DIR / f"{BASE_NAME}.svg"
MD_PATH = PZ_DIR / f"{BASE_NAME}.md"
DOCX_PATH = PZ_DIR / f"{BASE_NAME}.docx"
MMD_PATH = PZ_DIR / "block_scheme.mmd"

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


def text_run(text: str, bold: bool = False, font_name: str = "Times New Roman", size: str = "26"):
    run = el("w:r")
    rpr = el("w:rPr")
    rpr.append(el("w:rFonts", fonts_attrs(font_name)))
    rpr.append(el("w:sz", {"w:val": size}))
    rpr.append(el("w:szCs", {"w:val": size}))
    if bold:
        rpr.append(el("w:b"))
    run.append(rpr)
    t = el("w:t", text=text)
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    run.append(t)
    return run


def paragraph(text: str = "", style: str | None = None, align: str | None = None, bold: bool = False):
    p = el("w:p")
    ppr = el("w:pPr")
    if style:
        ppr.append(el("w:pStyle", {"w:val": style}))
    if align:
        ppr.append(el("w:jc", {"w:val": align}))
    if len(ppr):
        p.append(ppr)
    if text:
        p.append(text_run(text, bold=bold, size="28" if style == "Title" else "26"))
    return p


def code_paragraph(text: str):
    p = el("w:p")
    ppr = el("w:pPr")
    ppr.append(el("w:pStyle", {"w:val": "Code"}))
    p.append(ppr)
    p.append(text_run(text, font_name="Courier New", size="18"))
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

    def style(style_id: str, name: str, ppr=None, rpr=None, default=False):
        st = el("w:style", {"w:type": "paragraph", "w:styleId": style_id})
        if default:
            st.set(qn("w:default"), "1")
        st.append(el("w:name", {"w:val": name}))
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
    style("Normal", "Normal", normal_ppr, normal_rpr, default=True)

    title_ppr = el("w:pPr")
    title_ppr.append(el("w:jc", {"w:val": "center"}))
    title_ppr.append(el("w:spacing", {"w:after": "240"}))
    title_rpr = el("w:rPr")
    title_rpr.append(el("w:b"))
    title_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    title_rpr.append(el("w:sz", {"w:val": "28"}))
    style("Title", "Title", title_ppr, title_rpr)

    caption_ppr = el("w:pPr")
    caption_ppr.append(el("w:jc", {"w:val": "center"}))
    caption_ppr.append(el("w:spacing", {"w:before": "120", "w:after": "120"}))
    caption_rpr = el("w:rPr")
    caption_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    caption_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Caption", "Caption", caption_ppr, caption_rpr)

    code_ppr = el("w:pPr")
    code_ppr.append(el("w:spacing", {"w:line": "240", "w:lineRule": "auto", "w:after": "0"}))
    code_ppr.append(el("w:ind", {"w:firstLine": "0"}))
    code_rpr = el("w:rPr")
    code_rpr.append(el("w:rFonts", fonts_attrs("Courier New")))
    code_rpr.append(el("w:sz", {"w:val": "18"}))
    style("Code", "Code", code_ppr, code_rpr)
    return styles


def section_properties():
    sect = el("w:sectPr")
    sect.append(el("w:pgSz", {"w:w": "11906", "w:h": "16838"}))
    sect.append(el("w:pgMar", {"w:top": "1134", "w:right": "850", "w:bottom": "1417", "w:left": "1701", "w:header": "708", "w:footer": "708", "w:gutter": "0"}))
    borders = el("w:pgBorders", {"w:offsetFrom": "page"})
    for side in ["top", "left", "bottom", "right"]:
        borders.append(el(f"w:{side}", {"w:val": "single", "w:sz": "8", "w:space": "24", "w:color": "000000"}))
    sect.append(borders)
    return sect


def svg_diagram() -> str:
    nodes = [
        ("A", 60, 30, 300, 56, "Запуск start_cryptotrade.bat\\nили backend.py", "round"),
        ("B", 60, 115, 300, 56, "Инициализация SQLite\\ncryptotrade.db", "rect"),
        ("C", 60, 200, 300, 56, "Открытие index.html\\nчерез локальный сервер", "rect"),
        ("D", 115, 295, 190, 80, "Пользователь\\nвошел?", "diamond"),
        ("E", 450, 305, 285, 56, "Ввод email и пароля\\nили регистрация", "rect"),
        ("F", 450, 390, 285, 56, "Запрос состояния\\nчерез /api/state", "rect"),
        ("G", 498, 485, 190, 80, "Данные\\nкорректны?", "diamond"),
        ("H", 450, 600, 285, 56, "Сохранение локальной\\nсессии браузера", "rect"),
        ("I", 60, 420, 300, 56, "Открытие\\ndashboard.html", "rect"),
        ("J", 60, 505, 300, 70, "Загрузка рынка, портфеля\\nи истории из SQLite\\nчерез API", "rect"),
        ("K", 60, 610, 300, 56, "Просмотр рынка\\nи графиков", "rect"),
        ("L", 60, 695, 300, 56, "Запрос свечей\\nчерез /api/klines", "rect"),
        ("M", 115, 790, 190, 80, "Свечи\\nполучены?", "diamond"),
        ("N", 450, 725, 285, 56, "Построение\\nTradingView-графика", "rect"),
        ("O", 450, 840, 285, 70, "Построение fallback-графика\\nпо price_history", "rect"),
        ("P", 840, 790, 300, 56, "Выбор актива\\nна trade.html", "rect"),
        ("Q", 840, 880, 300, 56, "Ввод количества\\nи типа операции", "rect"),
        ("R", 895, 980, 190, 90, "Средств или\\nмонет достаточно?", "diamond"),
        ("S", 1225, 995, 260, 56, "Сообщение\\nоб ошибке", "rect"),
        ("T", 840, 1110, 300, 56, "Обновление\\nusers и wallets", "rect"),
        ("U", 840, 1195, 300, 56, "Создание записи\\ntransactions", "rect"),
        ("V", 840, 1280, 300, 70, "Сохранение изменений\\nв SQLite через\\nPOST /api/state", "rect"),
        ("W", 840, 1390, 300, 56, "Просмотр portfolio.html\\nи history.html", "round"),
    ]
    arrows = [
        ("A", "B", ""),
        ("B", "C", ""),
        ("C", "D", ""),
        ("D", "E", "Нет"),
        ("E", "F", ""),
        ("F", "G", ""),
        ("G", "E", "Нет"),
        ("G", "H", "Да"),
        ("D", "I", "Да"),
        ("H", "I", ""),
        ("I", "J", ""),
        ("J", "K", ""),
        ("K", "L", ""),
        ("L", "M", ""),
        ("M", "N", "Да"),
        ("M", "O", "Нет"),
        ("N", "P", ""),
        ("O", "P", ""),
        ("P", "Q", ""),
        ("Q", "R", ""),
        ("R", "S", "Нет"),
        ("S", "Q", ""),
        ("R", "T", "Да"),
        ("T", "U", ""),
        ("U", "V", ""),
        ("V", "W", ""),
    ]
    node_map = {node[0]: node for node in nodes}

    def center(node_id: str):
        _, x, y, w, h, *_ = node_map[node_id]
        return x + w / 2, y + h / 2

    def edge_points(start: str, end: str):
        sx, sy = center(start)
        ex, ey = center(end)
        _, x1, y1, w1, h1, *_ = node_map[start]
        _, x2, y2, w2, h2, *_ = node_map[end]
        if abs(ex - sx) > abs(ey - sy):
            sx = x1 + (w1 if ex > sx else 0)
            ex = x2 + (0 if ex > sx else w2)
        else:
            sy = y1 + (h1 if ey > sy else 0)
            ey = y2 + (0 if ey > sy else h2)
        return sx, sy, ex, ey

    def text_lines(text: str, x: float, y: float, width: float, height: float, size: int = 16) -> str:
        lines = text.split("\\n")
        start_y = y + height / 2 - (len(lines) - 1) * size * 0.62
        parts = []
        for index, line in enumerate(lines):
            parts.append(f'<text x="{x + width / 2}" y="{start_y + index * size * 1.2:.1f}" text-anchor="middle" dominant-baseline="middle">{line}</text>')
        return "\\n".join(parts)

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1540" height="1485" viewBox="0 0 1540 1485">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#111827"/>',
        "</marker>",
        "</defs>",
        '<rect width="1540" height="1485" fill="#ffffff"/>',
        '<style>text{font-family:Times New Roman,serif;font-size:16px;fill:#111827}.label{font-size:15px;font-weight:bold}.node{fill:#f8fafc;stroke:#111827;stroke-width:2}.term{fill:#ecfeff}.decision{fill:#fff7ed}.arrow{stroke:#111827;stroke-width:2;fill:none;marker-end:url(#arrow)}</style>',
    ]
    for start, end, label in arrows:
        sx, sy, ex, ey = edge_points(start, end)
        if start == "G" and end == "E":
            path = f"M {sx:.1f} {sy:.1f} C 390 {sy:.1f}, 390 330, {ex:.1f} {ey:.1f}"
            lx, ly = 380, 440
        elif start == "S" and end == "Q":
            path = f"M {sx:.1f} {sy:.1f} C 1510 {sy:.1f}, 1510 910, {ex:.1f} {ey:.1f}"
            lx, ly = 1495, 955
        elif abs(ex - sx) > 1 and abs(ey - sy) > 1:
            mid_x = (sx + ex) / 2
            path = f"M {sx:.1f} {sy:.1f} L {mid_x:.1f} {sy:.1f} L {mid_x:.1f} {ey:.1f} L {ex:.1f} {ey:.1f}"
            lx, ly = mid_x, sy - 8
        else:
            path = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
            lx, ly = (sx + ex) / 2, (sy + ey) / 2 - 8
        svg.append(f'<path class="arrow" d="{path}"/>')
        if label:
            svg.append(f'<text class="label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle">{label}</text>')
    for node_id, x, y, width, height, text, shape in nodes:
        if shape == "diamond":
            points = f"{x + width / 2},{y} {x + width},{y + height / 2} {x + width / 2},{y + height} {x},{y + height / 2}"
            svg.append(f'<polygon class="node decision" points="{points}"/>')
        elif shape == "round":
            svg.append(f'<rect class="node term" x="{x}" y="{y}" width="{width}" height="{height}" rx="24" ry="24"/>')
        else:
            svg.append(f'<rect class="node" x="{x}" y="{y}" width="{width}" height="{height}" rx="4" ry="4"/>')
        svg.append(text_lines(text, x, y, width, height))
    svg.append("</svg>")
    return "\\n".join(svg)


def write_markdown():
    mermaid = MMD_PATH.read_text(encoding="utf-8")
    content = "\n".join([
        "# ПРИЛОЖЕНИЕ Б",
        "",
        "## Блок-схема алгоритма работы программы",
        "",
        "```mermaid",
        mermaid.strip(),
        "```",
        "",
        "Рисунок Б.1 - Блок-схема алгоритма работы программы CryptoTrade",
        "",
    ])
    MD_PATH.write_text(content, encoding="utf-8")


def drawing_paragraph():
    cx = "8314000"
    cy = "8019000"
    p = el("w:p")
    ppr = el("w:pPr")
    ppr.append(el("w:jc", {"w:val": "center"}))
    p.append(ppr)
    r = el("w:r")
    drawing = el("w:drawing")
    inline = el("wp:inline", {"distT": "0", "distB": "0", "distL": "0", "distR": "0"})
    inline.append(el("wp:extent", {"cx": cx, "cy": cy}))
    inline.append(el("wp:effectExtent", {"l": "0", "t": "0", "r": "0", "b": "0"}))
    inline.append(el("wp:docPr", {"id": "1", "name": "Рисунок Б.1"}))
    inline.append(el("wp:cNvGraphicFramePr"))
    graphic = el("a:graphic")
    graphic_data = el("a:graphicData", {"uri": "http://schemas.openxmlformats.org/drawingml/2006/picture"})
    pic = el("pic:pic")
    nv_pic_pr = el("pic:nvPicPr")
    nv_pic_pr.append(el("pic:cNvPr", {"id": "0", "name": SVG_PATH.name}))
    nv_pic_pr.append(el("pic:cNvPicPr"))
    pic.append(nv_pic_pr)
    blip_fill = el("pic:blipFill")
    blip_fill.append(el("a:blip", {"r:embed": "rIdImage1"}))
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


def document_doc():
    doc = el("w:document")
    body = el("w:body")
    body.append(paragraph("ПРИЛОЖЕНИЕ Б", style="Title"))
    body.append(paragraph("Блок-схема алгоритма работы программы", style="Title"))
    body.append(paragraph("В приложении приведена блок-схема алгоритма работы сайта CryptoTrade. Схема отражает запуск локального сервера, инициализацию SQLite-базы, авторизацию пользователя, загрузку данных через API, построение графиков, выполнение сделки, сохранение транзакции и переход к портфелю и истории операций."))
    body.append(drawing_paragraph())
    body.append(paragraph("Рисунок Б.1 - Блок-схема алгоритма работы программы CryptoTrade", style="Caption"))
    body.append(paragraph("Исходное описание схемы в формате Mermaid приведено ниже. Оно используется для повторного построения схемы при изменении алгоритма."))
    for line in MMD_PATH.read_text(encoding="utf-8").splitlines():
        body.append(code_paragraph(line))
    body.append(section_properties())
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
    rel = etree.SubElement(root, "Relationship")
    rel.set("Id", "rIdImage1")
    rel.set("Type", f"{DOC_REL}/image")
    rel.set("Target", "media/block_scheme.svg")
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
    ]:
        override = etree.SubElement(root, "Override")
        override.set("PartName", part)
        override.set("ContentType", ctype)
    return root


def settings_doc():
    return el("w:settings")


def write_part(zf: ZipFile, path: str, node):
    xml = etree.tostring(node, xml_declaration=True, encoding="UTF-8", standalone="yes")
    zf.writestr(path, xml)


def write_docx():
    with ZipFile(DOCX_PATH, "w", ZIP_DEFLATED) as zf:
        write_part(zf, "[Content_Types].xml", content_types())
        write_part(zf, "_rels/.rels", rels_root())
        write_part(zf, "word/_rels/document.xml.rels", doc_rels())
        write_part(zf, "word/document.xml", document_doc())
        write_part(zf, "word/styles.xml", style_doc())
        write_part(zf, "word/settings.xml", settings_doc())
        zf.writestr("word/media/block_scheme.svg", SVG_PATH.read_text(encoding="utf-8"))


def main():
    SVG_PATH.write_text(svg_diagram(), encoding="utf-8")
    write_markdown()
    write_docx()
    print(DOCX_PATH)
    print(SVG_PATH)
    print(MD_PATH)


if __name__ == "__main__":
    main()
