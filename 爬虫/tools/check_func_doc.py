# -*- coding: utf-8 -*-
"""校验生成的 docx：标题、段落、表格与关键内容。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document

doc = Document(r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx")
heads = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
print("标题数:", len(heads))
for h in heads:
    print("  ", h)
print("表格数:", len(doc.tables))
for i, t in enumerate(doc.tables):
    print("  表%d: %d 行 × %d 列 | 表头: %s" %
          (i + 1, len(t.rows), len(t.columns),
           " / ".join(c.text for c in t.rows[0].cells)))
all_text = "\n".join(p.text for p in doc.paragraphs)
for key in ["高性价比推荐", "中关村在线", "性价比指数 = 性能分", "perf_score",
            "京东 / 天猫 / 淘宝", "ZOL", "demo / demo123"]:
    print("含 %r:" % key, key in all_text or any(key in c.text for t in doc.tables for r in t.rows for c in r.cells))
print("段落总数:", len(doc.paragraphs))
