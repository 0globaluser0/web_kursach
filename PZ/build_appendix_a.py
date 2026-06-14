from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


PZ_DIR = Path(__file__).resolve().parent
ROOT_DIR = PZ_DIR.parent
SITE_DIR = ROOT_DIR / "site"
BASE_NAME = "Приложение_А_Описание_файлов_и_текст_программы"
MD_PATH = PZ_DIR / f"{BASE_NAME}.md"
DOCX_PATH = PZ_DIR / f"{BASE_NAME}.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

NSMAP = {"w": W, "r": R}

SOURCE_FILES = [
    ("site/README.md", "Описание проекта, запуск, демо-доступ и структура файлов."),
    ("site/start_cryptotrade.bat", "Командный файл для запуска локального сервера и открытия сайта."),
    ("site/backend.py", "Python backend/API, статический сервер, работа с SQLite, курсы и свечи."),
    ("site/index.html", "Страница входа и регистрации."),
    ("site/dashboard.html", "Страница обзора портфеля и состояния пользователя."),
    ("site/market.html", "Страница рынка криптовалют."),
    ("site/trade.html", "Страница покупки, продажи и расширенного графика."),
    ("site/portfolio.html", "Страница портфеля пользователя."),
    ("site/history.html", "Страница истории операций."),
    ("site/admin.html", "Административная панель."),
    ("site/privacy.html", "Политика конфиденциальности."),
    ("site/terms.html", "Пользовательское соглашение."),
    ("site/assets/css/style.css", "Стили интерфейса, адаптивность и темная тема."),
    ("site/assets/js/app.js", "Логика клиентского интерфейса, API-запросы, торговля, графики и симуляция."),
]


def qn(tag: str) -> str:
    prefix, name = tag.split(":")
    namespaces = {"w": W, "r": R}
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


def clean_text(text: str) -> str:
    allowed = []
    for char in text.replace("\t", "    "):
        code = ord(char)
        if char in "\n\r" or code == 9 or code >= 32:
            allowed.append(char)
    return "".join(allowed)


def text_run(text: str, bold: bool = False, font_name: str = "Times New Roman", size: str = "26"):
    run = el("w:r")
    rpr = el("w:rPr")
    rpr.append(el("w:rFonts", fonts_attrs(font_name)))
    rpr.append(el("w:sz", {"w:val": size}))
    rpr.append(el("w:szCs", {"w:val": size}))
    if bold:
        rpr.append(el("w:b"))
    run.append(rpr)
    t = el("w:t", text=clean_text(text))
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    run.append(t)
    return run


def paragraph(
    text: str = "",
    style: str | None = None,
    align: str | None = None,
    bold: bool = False,
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
        p.append(text_run(text, bold=bold, size="28" if style == "Title" else "26"))
    return p


def code_paragraph(text: str):
    p = el("w:p")
    ppr = el("w:pPr")
    ppr.append(el("w:pStyle", {"w:val": "Code"}))
    p.append(ppr)
    p.append(text_run(text[:280], font_name="Courier New", size="18"))
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

    heading_ppr = el("w:pPr")
    heading_ppr.append(el("w:spacing", {"w:before": "240", "w:after": "120"}))
    heading_ppr.append(el("w:ind", {"w:firstLine": "0"}))
    heading_rpr = el("w:rPr")
    heading_rpr.append(el("w:b"))
    heading_rpr.append(el("w:rFonts", fonts_attrs("Times New Roman")))
    heading_rpr.append(el("w:sz", {"w:val": "26"}))
    style("Heading", "Heading", heading_ppr, heading_rpr)

    code_ppr = el("w:pPr")
    code_ppr.append(el("w:spacing", {"w:line": "220", "w:lineRule": "auto", "w:after": "0"}))
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


def read_source(relative_path: str) -> str:
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def write_markdown():
    lines = [
        "# ПРИЛОЖЕНИЕ А",
        "",
        "## Описание файлов и текст программы",
        "",
        "В приложении приведена структура программной части проекта CryptoTrade и тексты основных файлов сайта. В листинг не включены служебные runtime-файлы: `cryptotrade.db`, `__pycache__` и временные файлы Word.",
        "",
        "## Структура проекта",
        "",
    ]
    for path, description in SOURCE_FILES:
        lines.append(f"- `{path}` - {description}")
    lines.extend(["", "## Текст программы", ""])
    for path, description in SOURCE_FILES:
        language = "text"
        if path.endswith(".py"):
            language = "python"
        elif path.endswith(".js"):
            language = "javascript"
        elif path.endswith(".css"):
            language = "css"
        elif path.endswith(".html"):
            language = "html"
        elif path.endswith(".md"):
            language = "markdown"
        elif path.endswith(".bat"):
            language = "bat"
        lines.extend([
            f"### {path}",
            "",
            description,
            "",
            f"```{language}",
            read_source(path).rstrip(),
            "```",
            "",
        ])
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def document_doc():
    doc = el("w:document")
    body = el("w:body")
    body.append(paragraph("ПРИЛОЖЕНИЕ А", style="Title"))
    body.append(paragraph("Описание файлов и текст программы", style="Title"))
    body.append(paragraph("В приложении приведены структура программной части проекта CryptoTrade, назначение основных файлов и полный текст исходных файлов сайта. Приложение оформлено отдельно от пояснительной записки, чтобы листинг программы не перегружал основной текст."))
    body.append(paragraph("В текст программы не включены автоматически создаваемая база данных site/cryptotrade.db, каталог __pycache__ и временные файлы офисного редактора, так как они не являются исходным кодом проекта."))

    body.append(paragraph("СОДЕРЖАНИЕ", style="Heading", page_break_before=True))
    body.append(paragraph("1. Структура программной части проекта"))
    body.append(paragraph("2. Текст программы"))

    body.append(paragraph("1. Структура программной части проекта", style="Heading", page_break_before=True))
    for path, description in SOURCE_FILES:
        body.append(paragraph(f"{path} - {description}"))

    body.append(paragraph("2. Текст программы", style="Heading", page_break_before=True))
    for index, (path, description) in enumerate(SOURCE_FILES, 1):
        body.append(paragraph(f"Листинг А.{index} - {path}", style="Heading", page_break_before=index > 1))
        body.append(paragraph(description))
        for line in read_source(path).splitlines():
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


def content_types():
    root = etree.Element("Types", nsmap={None: CONTENT_TYPES})
    for ext, ctype in [
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
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
        write_part(zf, "word/document.xml", document_doc())
        write_part(zf, "word/styles.xml", style_doc())
        write_part(zf, "word/settings.xml", settings_doc())


def main():
    write_markdown()
    write_docx()
    print(DOCX_PATH)
    print(MD_PATH)


if __name__ == "__main__":
    main()
