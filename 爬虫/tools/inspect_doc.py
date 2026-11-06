# -*- coding: utf-8 -*-
"""查看功能整理文档的结构：标题与段落文本（截断）。"""
import sys
from docx import Document

DOC = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"
doc = Document(DOC)

print("== 段落总数:", len(doc.paragraphs), " 表格数:", len(doc.tables), "==")
for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if not text:
        continue
    style = p.style.name if p.style else ""
    if style.startswith("Heading") or style == "Title":
        print(f"[{i}] ({style}) {text}")
    else:
        print(f"[{i}] {text[:120]}")
