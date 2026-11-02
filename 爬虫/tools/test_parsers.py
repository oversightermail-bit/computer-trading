# -*- coding: utf-8 -*-
"""真实解析函数单元测试：合成 HTML/JSON 样本，不走网络。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hwspider.spiders import jd, taobao, tmall  # noqa: E402


def check(name, cond):
    print("[%s] %s" % ("PASS" if cond else "FAIL", name))
    return cond


ok = True

# 京东：合成搜索结果页（含空价格 → 走价格接口补价的条目）
html = (
    '<html><body><ul>'
    '<li class="gl-item" data-sku="10001"><div class="p-name"><a>'
    '<em>Intel i5-13490F 10核16线程 盒装CPU处理器</em></a></div>'
    '<div class="p-price"><i>1098.00</i></div>'
    '<div class="p-shop"><a title="Intel官方旗舰店">Intel官方旗舰店</a></div></li>'
    '<li class="gl-item" data-sku="10002"><div class="p-name"><a>'
    '<em>AMD R7 7800X3D 8核16线程 处理器</em></a></div>'
    '<div class="p-price"><i></i></div></li>'
    '</ul></body></html>'
)
items, banned = jd.parse_search(html, jd.SEARCH_URL, "cpu")
ok &= check("京东解析命中 2 条目录型号", len(items) == 2)
ok &= check("京东品牌/规格匹配正确",
            items[0].model == "i5-13490F" and items[0].spec == "10核16线程"
            and items[1].model == "R7 7800X3D")
ok &= check("京东封禁信号为否", not banned)

# 淘宝：合成内嵌 JSON
html2 = (
    '<script>g_page_config = {"mods":{"itemlist":{"data":{"auctions":['
    '{"raw_title":"AMD R5 5600 6核12线程 处理器盒装","view_price":"579.00",'
    '"nick":"XX数码","detail_url":"//item.taobao.com/x"}]}}}};</script>'
)
items2, banned2 = taobao.parse_search(html2, taobao.SEARCH_URL, "cpu")
ok &= check("淘宝 JSON 解析命中", len(items2) == 1 and items2[0].model == "R5 5600"
            and items2[0].price_text == "579.00")
ok &= check("淘宝封禁信号为否", not banned2)

# 淘宝：登录跳转封禁信号
ok &= check("淘宝登录跳转识别为封禁",
            taobao.detect_ban("", "https://login.taobao.com/member/login.jhtml?redirectURL=x"))

# 天猫：合成列表页
html4 = (
    '<html><body><div class="product-iWrap">'
    '<p class="productTitle"><a title="三星 990 PRO 1TB NVMe SSD固态硬盘" '
    'href="//detail.tmall.com/x">三星 990 PRO 1TB</a></p>'
    '<p class="productPrice"><em title="729.00">729.00</em></p>'
    '<a class="productShop-name">三星存储旗舰店</a></div></body></html>'
)
items4, banned4 = tmall.parse_search(html4, tmall.SEARCH_URL, "ssd")
ok &= check("天猫 CSS 解析命中", len(items4) == 1 and items4[0].model == "990 PRO"
            and items4[0].price_text == "729.00" and items4[0].spec == "1TB")
ok &= check("天猫 URL 补全 https", items4[0].url == "https://detail.tmall.com/x")

# 噪音标题应被丢弃
items5, _ = jd.parse_search(
    '<li class="gl-item" data-sku="9"><div class="p-name"><a><em>某某杂牌CPU</em></a>'
    '</div><div class="p-price"><i>9.9</i></div></li>', "u", "cpu")
ok &= check("噪音标题被过滤", len(items5) == 0)

# 价格文本标准化（清洗模块）
from hwspider.cleaner import normalize_price  # noqa: E402
ok &= check("价格标准化 ¥1,299.00 -> 1299.0", normalize_price("¥1,299.00") == 1299.0)
ok &= check("价格标准化 到手价 1299 -> 1299.0", normalize_price("到手价 1299") == 1299.0)
ok &= check("价格标准化 非法文本 -> NaN", str(normalize_price("暂无报价")) == "nan")

print("=" * 40)
print("解析/清洗单元测试：%s" % ("ALL PASS" if ok else "HAS FAILURE"))
sys.exit(0 if ok else 1)
