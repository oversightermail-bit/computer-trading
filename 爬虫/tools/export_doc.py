# -*- coding: utf-8 -*-
"""导出功能整理文档全文（UTF-8）到文本文件，便于查看与定位。"""
from docx import Document

DOC = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"
OUT = r"D:\AI电脑购买指导项目\爬虫\tools\doc_full.txt"

doc = Document(DOC)
lines = []
lines.append("== 段落总数: %d  表格数: %d ==" % (len(doc.paragraphs), len(doc.tables)))
for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if not text:
        continue
    style = p.style.name if p.style else ""
    lines.append("[%d] (%s) %s" % (i, style, text))

# 表格内容也导出（订阅额度/套餐表可能在表格里）
for ti, t in enumerate(doc.tables):
    lines.append("== 表格 %d（%d 行 x %d 列） ==" % (ti, len(t.rows), len(t.columns)))
    for row in t.rows:
        cells = [c.text.strip().replace("\n", " / ") for c in row.cells]
        lines.append("  | " + " | ".join(cells))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("OK ->", OUT)
