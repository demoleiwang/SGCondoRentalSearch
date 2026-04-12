"""
100+ example queries for SG Rental Search.
Run this file to verify all examples parse correctly.

Usage: python examples.py
"""

import sys
sys.path.insert(0, ".")

from engine import parse_query, criteria_to_display

# (query, expected_fields_description)
EXAMPLES = [
    # ===== BASIC CONDO SEARCHES =====
    # 1-10: Simple station + bedroom + price
    ("Queenstown 1b1b 3300", "Queenstown, 1BR, ~$3300"),
    ("Bishan 2 bedroom 4000", "Bishan, 2BR, ~$4000"),
    ("Novena 1br 3500", "Novena, 1BR, ~$3500"),
    ("Toa Payoh 3br 5000", "Toa Payoh, 3BR, ~$5000"),
    ("Orchard 1 bedroom 4500", "Orchard, 1BR, ~$4500"),
    ("Holland Village 2b2b 4800", "Holland Village, 2BR, ~$4800"),
    ("Paya Lebar 1b1b 3200", "Paya Lebar, 1BR, ~$3200"),
    ("Tiong Bahru 1br 3000", "Tiong Bahru, 1BR, ~$3000"),
    ("Buona Vista 2 bedrooms 4200", "Buona Vista, 2BR, ~$4200"),
    ("Clementi 1b1b 2800", "Clementi, 1BR, ~$2800"),

    # 11-20: Price range patterns
    ("Queenstown 1br 3000-3500", "Queenstown, 1BR, $3000-$3500"),
    ("Bishan 2br 3500-4500", "Bishan, 2BR, $3500-$4500"),
    ("Novena 1 bedroom 3000 to 4000", "Novena, 1BR, $3000-$4000"),
    ("Toa Payoh 2br 2500~3500", "Toa Payoh, 2BR, $2500-$3500"),
    ("Orchard studio 2000-3000", "Orchard, studio, $2000-$3000"),
    ("Paya Lebar 3br 5000-7000", "Paya Lebar, 3BR, $5000-$7000"),
    ("Bishan 1br budget 3000 to 3500", "Bishan, 1BR, $3000-$3500"),
    ("Queenstown 2 bedroom 4000 to 5000", "Queenstown, 2BR, $4000-$5000"),
    ("Holland Village 1br 3500到4500", "Holland Village, 1BR, $3500-$4500"),
    ("Novena 2b2b 4000-5500", "Novena, 2BR, $4000-$5500"),

    # 21-30: Under / max price
    ("Orchard 1br under 4000", "Orchard, 1BR, max $4000"),
    ("Queenstown 2 bedroom below 5000", "Queenstown, 2BR, max $5000"),
    ("Bishan 1b1b 3500以内", "Bishan, 1BR, max $3500"),
    ("Novena studio 不超过2500", "Novena, studio, max $2500"),
    ("Clementi 1br max 3000", "Clementi, 1BR, max $3000"),
    ("Toa Payoh 2房 4000以下", "Toa Payoh, 2BR, max $4000"),
    ("Paya Lebar 1br under $3,500", "Paya Lebar, 1BR, max $3500"),
    ("Holland Village 3br below 7000", "Holland Village, 3BR, max $7000"),
    ("Buona Vista 1 bedroom 低于3200", "Buona Vista, 1BR, max $3200"),
    ("Redhill 2br under 4500", "Redhill, 2BR, max $4500"),

    # 31-40: Above / min price
    ("Orchard 2br at least 5000", "Orchard, 2BR, min $5000"),
    ("Clementi 1br above 2500", "Clementi, 1BR, min $2500"),
    ("Newton 3br 6000以上", "Newton, 3BR, min $6000"),
    ("Novena 2br 至少4000", "Novena, 2BR, min $4000"),
    ("Bishan 1b1b minimum 3000", "Bishan, 1BR, min $3000"),
    ("Queenstown 2房 3000起", "Queenstown, 2BR, min $3000"),

    # ===== FACING / ORIENTATION =====
    # 41-55
    ("Queenstown 1b1b 3300 south facing", "south facing"),
    ("Bishan 2br 4000 north facing", "north facing"),
    ("朝南的1房 Novena 3500", "south facing Chinese"),
    ("Paya Lebar 1br 3200 facing south", "facing south"),
    ("east facing 2br Toa Payoh 4000", "east facing"),
    ("Holland Village 1br 3500 west facing", "west facing"),
    ("southeast facing condo Queenstown 3000", "SE facing"),
    ("Bishan 2br 4500 northeast facing", "NE facing"),
    ("Orchard 1br 4000 northwest", "NW facing"),
    ("southwest facing Clementi 2br 4000", "SW facing"),
    ("找朝东南的1房 Novena", "SE facing Chinese"),
    ("Queenstown 1b1b 朝北 3300", "north facing Chinese"),
    ("Bishan 2房 朝西 4500", "west facing Chinese"),
    ("Toa Payoh 东北朝向 2br 3800", "NE facing Chinese"),
    ("south facing high floor Queenstown 1br 3500", "south + high floor"),

    # ===== FLOOR PREFERENCES =====
    # 56-65
    ("high floor 1br Queenstown 3500", "high floor >= 15"),
    ("高楼层 Bishan 2房 4500", "high floor Chinese"),
    ("Novena 1br 3500 min floor 10", "floor >= 10"),
    ("Toa Payoh 2br 4000 floor 20", "floor >= 20"),
    ("Orchard 1 bedroom 4000 minimum floor 15", "floor >= 15"),
    ("帮我找高楼层的1b1b Queenstown 3300", "high floor Chinese"),
    ("Queenstown 1br 3300 floor >= 8", "floor >= 8"),
    ("Paya Lebar 2br 4500 high floor south facing", "high floor + south"),
    ("Holland Village 1br 3500 high floor", "high floor"),
    ("low floor Bishan 2br 4000", "low floor preference"),

    # ===== HDB SEARCHES =====
    # 66-80
    ("Queenstown 3-room 2500", "HDB 3-room"),
    ("Bishan 4-room 3000", "HDB 4-room"),
    ("Toa Payoh 3 room 2200", "HDB 3-room"),
    ("Ang Mo Kio 4-room 2800", "HDB 4-room"),
    ("Tampines 5-room 3500", "HDB 5-room"),
    ("Woodlands 3-room 1800", "HDB 3-room"),
    ("Yishun 4-room 2500", "HDB 4-room"),
    ("Sengkang 3-room 2000-2500", "HDB 3-room range"),
    ("Punggol 4 room under 2800", "HDB 4-room max"),
    ("executive flat Bishan 5000", "HDB executive"),
    ("Hougang 3-room 2000以内", "HDB 3-room Chinese max"),
    ("Clementi 5-room HDB 3200", "HDB 5-room"),
    ("Bedok 4-room 2500-3000", "HDB 4-room range"),
    ("Jurong East 3-room 2000", "HDB 3-room"),
    ("Serangoon 4-room HDB 2800", "HDB 4-room"),

    # ===== CHINESE QUERIES =====
    # 81-100
    ("找Queenstown附近1房3300左右", "Chinese basic"),
    ("在Bishan地铁站附近租2房，预算4000以内", "Chinese with budget limit"),
    ("帮我筛选Novena附近朝南的1b1b月租3500", "Chinese south facing"),
    ("Queenstown附近有没有3000以下的1房", "Chinese under price"),
    ("想在Toa Payoh租2房，4000左右", "Chinese around price"),
    ("Paya Lebar附近1房3200到3800", "Chinese price range"),
    ("找Holland Village的studio，预算2500以内", "Chinese studio"),
    ("Bishan附近的3房condo，预算6000左右", "Chinese 3BR"),
    ("想租Orchard附近高楼层1房，4000以内", "Chinese high floor"),
    ("Clementi地铁站500米内的2房，不超过4500", "Chinese radius + price"),
    ("在Novena附近找朝东南的2b2b，月租5000左右", "Chinese SE facing"),
    ("Queenstown附近的condo，1房1卫，3300", "Chinese 1b1b"),
    ("预算3000，想在Tiong Bahru找1房", "Chinese budget first"),
    ("Buona Vista 1房 3000块左右", "Chinese with 块"),
    ("Redhill附近2房朝南高楼层 4500以内", "Chinese complex"),
    ("找个Bishan附近的2房，4000到5000之间", "Chinese range with 之间"),
    ("帮我看看Ang Mo Kio有什么3房HDB，2500以下的", "Chinese HDB"),
    ("想在Tampines租4-room，3000左右", "Chinese HDB 4-room"),
    ("Woodlands 3房 2000以内 低楼层", "Chinese HDB low floor"),
    ("大概3500，Queenstown附近1房", "Chinese approx price"),

    # ===== ENGLISH COMPLEX QUERIES =====
    # 101-115
    ("looking for 1 bedroom near Queenstown MRT around 3300 per month", "complex EN"),
    ("2 bedroom condo near Bishan MRT budget 4000 to 5000 south facing", "complex EN facing"),
    ("need a studio near Dhoby Ghaut under 2500", "studio under price"),
    ("1br near Clarke Quay around $3,500", "with dollar sign"),
    ("affordable 2br near Novena 3500-4500 high floor", "affordable + high floor"),
    ("3 bedroom near Newton at least 6000", "3BR min price"),
    ("Paya Lebar 1br 500m radius 3200", "with radius"),
    ("2 bedrooms Buona Vista 4000 to 5000 north facing", "range + facing"),
    ("Queenstown 1 bedroom 600 sqft 3300", "with area"),
    ("1br Farrer Park 3000", "less common station"),
    ("Bedok 2 bedroom 3500 east facing", "east area"),
    ("Kembangan 1br 2800", "small station"),
    ("Botanic Gardens 2br 5000", "between lines station"),
    ("Stevens 1 bedroom 4000", "TEL/DTL station"),
    ("Bayfront studio 3000", "CBD area"),

    # ===== EDGE CASES =====
    # 116-125
    ("one-north 1br 3000", "hyphenated station name"),
    ("Queenstown", "station only"),
    ("1 bedroom 3000", "no station"),
    ("south facing 2br 4000", "facing first, no station"),
    ("$3,500 1br Queenstown", "price first"),
    ("Queenstown condo 1b1b rent 3300 monthly", "verbose EN"),
    ("便宜的1房 Queenstown 3000以下", "Chinese cheap + under"),
    ("Bishan or Toa Payoh 2br 4000", "multi station (picks first match)"),
    ("找个安静的Queenstown 1房 3300", "with adjective"),
    ("Queenstown 1b1b 3300 no agent fee", "with irrelevant text"),

    # ===== DOLLAR SIGN & SPECIAL FORMATS =====
    # 122-130
    ("$3,000-$3,500 1br Queenstown", "dollar signs in range"),
    ("$3,500 to $4,500 2br Bishan", "dollar signs with to"),
    ("Queenstown 1br $3,300/month", "dollar sign with /month"),
    ("10楼以上 Bishan 2房 4000", "Chinese floor number first"),
    ("Novena 1br 15楼 3500", "Chinese floor inline"),
    ("rent under $4,000 Orchard 1br", "dollar with under prefix"),
    ("minimum $3,000 2br Queenstown", "dollar with minimum prefix"),
    ("Toa Payoh 2br 3500 2km内", "radius in Chinese"),
    ("1.5km范围 Bishan 1br 3000", "decimal km radius"),
]


def main():
    total = len(EXAMPLES)
    passed = 0
    failed = []

    print(f"Running {total} example queries...\n")
    print(f"{'#':>3} | {'Status':6} | {'Query':<60} | Parsed")
    print("-" * 140)

    for i, (query, desc) in enumerate(EXAMPLES, 1):
        criteria = parse_query(query)
        display = criteria_to_display(criteria)
        has_content = bool(criteria)

        # Basic validation: should parse to something
        status = "OK" if has_content else "EMPTY"
        if status == "OK":
            passed += 1
        else:
            failed.append((i, query, desc))

        print(f"{i:>3} | {status:6} | {query:<60} | {display}")

    print("-" * 140)
    print(f"\nResult: {passed}/{total} passed ({total - passed} empty)")

    if failed:
        print("\nFailed (empty parse):")
        for i, q, d in failed:
            print(f"  #{i}: {q} ({d})")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
