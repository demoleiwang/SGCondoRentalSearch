"""Internationalization: English / Chinese UI strings."""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Translation table
# Keys are dot-separated paths.  Values are {"en": ..., "zh": ...}.
# ---------------------------------------------------------------------------
_STRINGS: dict[str, dict[str, str]] = {
    # -- Page --
    "page.title": {
        "en": "SG Rental Search",
        "zh": "新加坡租房搜索",
    },
    "page.caption": {
        "en": "URA & HDB official data + PropertyGuru live listings",
        "zh": "URA & HDB 官方数据 + PropertyGuru 实时房源",
    },
    "page.search_placeholder": {
        "en": "Type your search here and press Enter...",
        "zh": "输入搜索条件后按回车...",
    },
    "page.search_label": {
        "en": "Search (e.g. 'Queenstown 1b1b 3300' or 'Bishan 2BR 4000')",
        "zh": "搜索 (例如 'Queenstown 1b1b 3300' 或 '找Bishan附近2房4000')",
    },
    "page.parsed": {
        "en": "Parsed",
        "zh": "已解析",
    },

    # -- Sidebar --
    "sidebar.filters": {
        "en": "Filters",
        "zh": "筛选条件",
    },
    "sidebar.property_type": {
        "en": "Property Type",
        "zh": "房产类型",
    },
    "sidebar.condo": {
        "en": "Condo",
        "zh": "公寓",
    },
    "sidebar.hdb": {
        "en": "HDB",
        "zh": "组屋",
    },
    "sidebar.both": {
        "en": "Both",
        "zh": "全部",
    },
    "sidebar.mrt_station": {
        "en": "MRT Station",
        "zh": "地铁站",
    },
    "sidebar.any": {
        "en": "(Any)",
        "zh": "(不限)",
    },
    "sidebar.condo_filters": {
        "en": "Condo Filters",
        "zh": "公寓筛选",
    },
    "sidebar.condo_bedrooms": {
        "en": "Condo Bedrooms",
        "zh": "公寓卧室数",
    },
    "sidebar.condo_rent": {
        "en": "Condo Monthly Rent (SGD)",
        "zh": "公寓月租 (新币)",
    },
    "sidebar.hdb_filters": {
        "en": "HDB Filters",
        "zh": "组屋筛选",
    },
    "sidebar.flat_type": {
        "en": "Flat Type",
        "zh": "房型",
    },
    "sidebar.hdb_rent": {
        "en": "HDB Monthly Rent (SGD)",
        "zh": "组屋月租 (新币)",
    },
    "sidebar.sort": {
        "en": "Sort by",
        "zh": "排序方式",
    },
    "sidebar.sort_low": {
        "en": "Rent (Low to High)",
        "zh": "租金 (低到高)",
    },
    "sidebar.sort_high": {
        "en": "Rent (High to Low)",
        "zh": "租金 (高到低)",
    },
    "sidebar.sort_popular": {
        "en": "Most Popular",
        "zh": "最受欢迎",
    },
    "sidebar.search_btn": {
        "en": "Search",
        "zh": "搜索",
    },
    "sidebar.browse": {
        "en": "Browse live listings:",
        "zh": "浏览实时房源:",
    },
    "sidebar.language": {
        "en": "Language / 语言",
        "zh": "语言 / Language",
    },

    # -- Bedroom labels --
    "bed.studio": {
        "en": "Studio",
        "zh": "开间",
    },
    "bed.n": {
        "en": "{n} Bedroom{s}",
        "zh": "{n}房",
    },

    # -- Smart search --
    "smart.detected": {
        "en": "Smart Search: detected **{landmark}** — expanded to {n} nearby areas",
        "zh": "智能搜索：识别到 **{landmark}** — 扩展至 {n} 个周边区域",
    },
    "smart.strategies": {
        "en": "Search Strategies",
        "zh": "搜索方向",
    },
    "smart.total_condos": {
        "en": "Total Condos Found",
        "zh": "找到公寓数",
    },
    "smart.rent_range": {
        "en": "Rent Range",
        "zh": "租金范围",
    },
    "smart.map": {
        "en": "Map",
        "zh": "地图",
    },
    "smart.results_by_area": {
        "en": "Results by Area ({n} condos)",
        "zh": "按区域分组 ({n} 个公寓)",
    },
    "smart.condos": {
        "en": "condos",
        "zh": "个公寓",
    },
    "smart.more": {
        "en": "... and {n} more",
        "zh": "... 还有 {n} 个",
    },
    "smart.show_more": {
        "en": "Show {n} more condos",
        "zh": "查看其余 {n} 个公寓",
    },
    "smart.full_table": {
        "en": "Full Data Table",
        "zh": "完整数据表",
    },
    "smart.analysis": {
        "en": "Analysis Summary",
        "zh": "分析摘要",
    },
    "smart.col_project": {
        "en": "Project",
        "zh": "项目",
    },
    "smart.col_area": {
        "en": "Area",
        "zh": "区域",
    },
    "smart.col_est_rent": {
        "en": "Est {n}BR Rent",
        "zh": "预估{n}房租金",
    },
    "smart.col_median_psf": {
        "en": "Median PSF",
        "zh": "中位尺价",
    },
    "smart.col_contracts": {
        "en": "Contracts",
        "zh": "成交量",
    },

    # -- Regular search --
    "result.condo_projects": {
        "en": "Condo Projects",
        "zh": "公寓项目",
    },
    "result.avg_br": {
        "en": "Avg {n}BR",
        "zh": "{n}房均价",
    },
    "result.range": {
        "en": "Range",
        "zh": "范围",
    },
    "result.condo_heading": {
        "en": "Condo Projects ({n})",
        "zh": "公寓项目 ({n})",
    },
    "result.no_condo": {
        "en": "No condos match. Try adjusting filters.",
        "zh": "没有匹配的公寓，请调整筛选条件。",
    },
    "result.contracts": {
        "en": "{n} contracts",
        "zh": "{n} 份合同",
    },
    "result.condo_table": {
        "en": "Condo Data Table",
        "zh": "公寓数据表",
    },

    # -- Trend chart --
    "trend.title": {
        "en": "Rent Trend: {name}",
        "zh": "租金走势: {name}",
    },
    "trend.expand": {
        "en": "Rent Trend",
        "zh": "租金走势",
    },
    "trend.quarter": {
        "en": "Quarter",
        "zh": "季度",
    },
    "trend.median_psf": {
        "en": "Median $/psf",
        "zh": "中位尺价 $/psf",
    },
    "trend.est_rent": {
        "en": "Est. Monthly Rent ($)",
        "zh": "预估月租 ($)",
    },
    "trend.p25_p75": {
        "en": "P25-P75 Range",
        "zh": "P25-P75 区间",
    },
    "trend.no_data": {
        "en": "No historical data available",
        "zh": "暂无历史数据",
    },
    "trend.single_qtr_info": {
        "en": "Only 1 quarter of data available ({qtr}). Historical trends will accumulate automatically as URA releases new quarterly data (every ~3 months).",
        "zh": "目前仅有 1 个季度的数据 ({qtr})。URA 每季度更新（约3个月一次），历史趋势会自动累积。",
    },
    "trend.price_dist": {
        "en": "Price Distribution ({qtr})",
        "zh": "租金分布 ({qtr})",
    },
    "trend.p25": {
        "en": "P25 (Low)",
        "zh": "P25 (低)",
    },
    "trend.median": {
        "en": "Median",
        "zh": "中位",
    },
    "trend.p75": {
        "en": "P75 (High)",
        "zh": "P75 (高)",
    },
    "trend.contracts_qtr": {
        "en": "{n} rental contracts in this quarter",
        "zh": "本季度 {n} 份租赁合同",
    },
    "trend.current": {
        "en": "Current",
        "zh": "当前",
    },
    "trend.low": {
        "en": "Historical Low",
        "zh": "历史最低",
    },
    "trend.high": {
        "en": "Historical High",
        "zh": "历史最高",
    },
    "trend.change": {
        "en": "vs Last Qtr",
        "zh": "环比上季",
    },
    "trend.bargain_room": {
        "en": "Bargain room: **${delta:,}/mo** below P75",
        "zh": "砍价空间: 比P75低 **${delta:,}/月**",
    },

    # -- HDB --
    "hdb.transactions": {
        "en": "HDB Transactions",
        "zh": "组屋交易数",
    },
    "hdb.median_rent": {
        "en": "Median Rent",
        "zh": "中位租金",
    },
    "hdb.overview": {
        "en": "HDB Rental Overview ({n} town-type combos)",
        "zh": "组屋租金概览 ({n} 个区域-房型组合)",
    },
    "hdb.no_match": {
        "en": "No HDB listings match. Try adjusting filters.",
        "zh": "没有匹配的组屋，请调整筛选条件。",
    },
    "hdb.txn_count": {
        "en": "{n} transactions (last 6 months)",
        "zh": "{n} 笔交易 (近6个月)",
    },
    "hdb.street_table": {
        "en": "HDB Street-Level Data",
        "zh": "组屋街道级数据",
    },

    # -- Map --
    "map.title": {
        "en": "Map",
        "zh": "地图",
    },

    # -- Tips --
    "tips.title": {
        "en": "Tips",
        "zh": "小贴士",
    },
    "tips.condo": {
        "en": """**Condo tips:**
- Google "*condo name* + brochure" for floor plans
- Check URA Rental Transactions for exact unit history
- Aim for P25 price when negotiating
- Use the rent trend chart to spot downward trends""",
        "zh": """**公寓技巧:**
- 谷歌搜索 "公寓名 + brochure" 查看户型图
- 查看 URA 租赁交易记录了解精确历史价格
- 砍价目标瞄准 P25 价格
- 利用租金走势图发现降价趋势""",
    },
    "tips.hdb": {
        "en": """**HDB tips:**
- HDB rental data shows actual approved rents (not asking prices)
- Compare similar flat types on the same street for fair pricing
- Check if the flat is within the minimum occupation period (MOP)""",
        "zh": """**组屋技巧:**
- HDB数据显示的是实际批准租金（非挂牌价）
- 对比同街道同房型的租金来判断合理价格
- 确认房屋是否过了最低居住期限 (MOP)""",
    },

    # -- Rent row details (P25/P75 + district comparison) --
    "row.p25": {
        "en": "P25 (bargaining target)",
        "zh": "P25 (议价目标)",
    },
    "row.p75": {
        "en": "P75",
        "zh": "P75",
    },
    "row.vs_district_below": {
        "en": "{pct}% below area median",
        "zh": "低于区域中位 {pct}%",
    },
    "row.vs_district_above": {
        "en": "{pct}% above area median",
        "zh": "高于区域中位 {pct}%",
    },
    "row.vs_district_at": {
        "en": "at area median",
        "zh": "接近区域中位",
    },
    "row.contracts_short": {
        "en": "{n} contracts",
        "zh": "{n}笔合约",
    },

    # -- Features Showcase --
    "features.heading": {
        "en": "What this tool can do",
        "zh": "这个工具能干啥",
    },
    "features.subheading": {
        "en": "Click any example to try it",
        "zh": "点击示例即可试用",
    },
    "features.smart.title": {
        "en": "Smart Landmark Search",
        "zh": "地标智能搜索",
    },
    "features.smart.desc": {
        "en": "Type a school, office, or district — we auto-expand to all nearby MRT stations and rank by walk distance.",
        "zh": "输入学校/办公楼/区域，自动展开到周边地铁站并按步行距离排序。",
    },
    "features.nl.title": {
        "en": "Natural Language (EN + 中文)",
        "zh": "自然语言 (中英混合)",
    },
    "features.nl.desc": {
        "en": "Mix English and Chinese, rough or precise. Supports price ranges, facing, floor, radius.",
        "zh": "中英混合，模糊或精确都行。支持价格区间、朝向、楼层、距离。",
    },
    "features.data.title": {
        "en": "Condo + HDB Data",
        "zh": "公寓 + 组屋数据",
    },
    "features.data.desc": {
        "en": "551 condo projects from URA + 200K+ HDB transactions from data.gov.sg. Updated quarterly / monthly.",
        "zh": "URA 551 个公寓项目 + 20万+ HDB 租赁记录，季度/月度更新。",
    },
    "features.trend.title": {
        "en": "Rent Trends (P25/P50/P75)",
        "zh": "租金趋势 (P25/P50/P75)",
    },
    "features.trend.desc": {
        "en": "Per-project 8-quarter history with P25 as a realistic negotiation target.",
        "zh": "每个项目 8 个季度历史，P25 可作议价目标。",
    },
    "features.commute.title": {
        "en": "Smart Commute Search",
        "zh": "智能通勤搜索",
    },
    "features.commute.desc": {
        "en": "Enter two locations (e.g. office + school) and find optimal rental areas between them.",
        "zh": "输入两个位置（如办公室+学校），找夹在中间的最佳租房区域。",
    },
    "features.filter.title": {
        "en": "Facing, Floor & Range Filters",
        "zh": "朝向/楼层/价格区间筛选",
    },
    "features.filter.desc": {
        "en": "Narrow by south-facing, high floor, exact price band, or custom radius from an MRT.",
        "zh": "按朝南、高楼层、精确价格区间、自定义距 MRT 范围筛选。",
    },

    # -- Welcome --
    "welcome.how_to": {
        "en": """### How to use

**1. Choose property type** — Condo, HDB, or Both (sidebar)

**2. Search** — Natural language or sidebar filters:
- `Queenstown 1b1b 3300` → 1BR condos ~$3,300/mo
- `Bishan 2 bedroom 4000` → 2BR condos near Bishan
- `Paya Lebar 1 bedroom 3000-3500` → 1BR condos $3,000-$3,500

---

**Data sources:**
- **Condo:** URA official rental statistics (551 projects, quarterly)
- **HDB:** HDB rental transactions (200K+ records, 2021-2026)
- Click through to **PropertyGuru** for live listings""",
        "zh": """### 使用方法

**1. 选择房产类型** — 公寓、组屋或全部（左侧栏）

**2. 搜索** — 支持自然语言或侧栏筛选:
- `Queenstown 1b1b 3300` → Queenstown 1房 约$3,300/月
- `找Bishan附近2房 4000以内` → Bishan附近 2房 $4,000以内
- `Paya Lebar 1 bedroom 3000-3500` → Paya Lebar 1房 $3,000-$3,500

---

**数据来源:**
- **公寓:** URA 官方租赁统计 (551个项目，按季度更新)
- **组屋:** HDB 租赁交易记录 (20万+条, 2021-2026)
- 点击链接跳转 **PropertyGuru** 查看实时房源""",
    },
    "welcome.popular": {
        "en": "Popular Searches",
        "zh": "热门搜索",
    },

    # -- Loading --
    "loading.condo": {
        "en": "Loading condo data...",
        "zh": "加载公寓数据...",
    },
    "loading.hdb": {
        "en": "Loading HDB data...",
        "zh": "加载组屋数据...",
    },
    "loading.failed_condo": {
        "en": "Failed to load condo data",
        "zh": "加载公寓数据失败",
    },
    "loading.failed_hdb": {
        "en": "Failed to load HDB data",
        "zh": "加载组屋数据失败",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_lang() -> str:
    """Return current language code from session state ('en' or 'zh')."""
    return st.session_state.get("lang", "en")


def set_lang(lang: str) -> None:
    """Set language in session state."""
    st.session_state["lang"] = lang


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.

    Supports format placeholders: t("bed.n", n=2, s="s") -> "2 Bedrooms"
    """
    lang = get_lang()
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def bedroom_label(n: int) -> str:
    """Return human-readable bedroom label for selectbox."""
    if n == 0:
        return t("bed.studio")
    s = "s" if n > 1 else ""
    return t("bed.n", n=n, s=s)
