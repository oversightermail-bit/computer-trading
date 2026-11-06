# -*- coding: utf-8 -*-
"""修正技术栈表：数据库行第二列 10 张表 -> 11 张表。"""
from docx import Document

DOC = r"D:\AI电脑购买指导项目\硬件比价网站_功能整理文档.docx"
doc = Document(DOC)

t0 = doc.tables[0]
for row in t0.rows:
    if row.cells[0].text.strip() == "数据库":
        cell = row.cells[1]
        p = cell.paragraphs[0]
        if p.runs:
            p.runs[0].text = "MySQL 8（hw_price 库，11 张表）"
            for r in p.runs[1:]:
                r._element.getparent().remove(r._element)
        else:
            p.add_run("MySQL 8（hw_price 库，11 张表）")
        print("fixed:", row.cells[1].text)
        break

doc.save(DOC)
print("SAVED OK")
