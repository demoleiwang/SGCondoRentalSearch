---
description: Search Singapore condo/HDB rentals. Usage: /search-condo <your query in natural language>
---

# SG Rental Search

You are helping the user search for condo and HDB rentals in Singapore. The user's query is: $ARGUMENTS

## What to do

1. **Parse the query** using the project's engine module to extract structured criteria:
   ```bash
   cd /Users/wanglei/Projects/others/rental_conda_sg && python -c "
   from engine import parse_query, criteria_to_display
   c = parse_query('$ARGUMENTS')
   print(criteria_to_display(c))
   print(c)
   "
   ```

2. **Check if the Streamlit app is running**, and start it if not:
   ```bash
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8501 || (cd /Users/wanglei/Projects/others/rental_conda_sg && streamlit run app.py --server.headless true &)
   ```
   Tell the user to open http://localhost:8501 and paste their query in the search box.

3. **Provide direct search links** for live listings:
   ```bash
   cd /Users/wanglei/Projects/others/rental_conda_sg && python -c "
   from scraper.data_gov import build_99co_url, build_propertyguru_url
   from engine import parse_query
   c = parse_query('$ARGUMENTS')
   station = c.get('mrt_station', '')
   beds = c.get('bedrooms')
   pmin = c.get('price_min')
   pmax = c.get('price_max')
   print('99.co:', build_99co_url(location=station, bedrooms=beds, price_min=pmin, price_max=pmax))
   print('PropertyGuru:', build_propertyguru_url(location=station, bedrooms=beds, price_min=pmin, price_max=pmax))
   "
   ```

4. **Show a summary** of parsed criteria and helpful tips.

## Supported query patterns
- **Basic**: `Queenstown 1b1b 3300`, `Bishan 2 bedroom 4000`
- **Price range**: `3000-3500`, `3000 to 4000`, `$3,000-$3,500`
- **Max price**: `under 4000`, `4000以内`, `below $3,500`
- **Min price**: `at least 3000`, `3000以上`, `above 2500`
- **Facing**: `south facing`, `朝南`, `northeast`
- **Floor**: `high floor`, `高楼层`, `min floor 10`, `10楼`
- **HDB**: `3-room`, `4-room`, `executive`
- **Radius**: `500m radius`, `2km内`
- **Chinese**: `找Queenstown附近1房3300左右`, `预算4000以内`

## Tips to share
- Adjust filters in the Streamlit sidebar for fine-tuning
- Google "[condo name] + brochure" for floor plans
- Check URA Rental Transactions for historical prices
- P25 (25th percentile) is a good target for negotiation
- Unit number format: "xx-xx" (floor-unit number)
