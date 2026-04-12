---
description: Find optimal rental areas based on landmarks (school, office, etc.). Usage: /smart-search <describe your locations and preferences>
---

# Smart Search

The user wants to find the best area to live based on nearby landmarks. Their description: $ARGUMENTS

## What to do

1. **Extract locations and preferences** from the user's description:
   - Landmarks: school, office, gym, etc.
   - Budget, bedrooms, extra preferences (facing, floor, etc.)

2. **Run the smart search** using the project's smart_search module:
   ```bash
   python -c "
   from smart_search import expand_query
   result = expand_query('$ARGUMENTS')
   if result:
       print(result.summary)
   else:
       print('No landmark detected. Try including a place name like SMU, NUS, CBD, etc.')
   "
   ```

3. **For detailed results per area**:
   ```bash
   python -c "
   from smart_search import expand_query
   result = expand_query('$ARGUMENTS')
   if result:
       for s in result.strategies[:5]:
           print(f'{s.station} ({s.distance_m}m): {s.reason}')
       print(f'Total condos found: {len(result.results)}')
       for r in result.results[:10]:
           print(f'  {r.project_name}: \${r.est_rent:,}/mo [{r.strategy_name}]')
           print(f'    PropertyGuru: {r.url_propertyguru}')
   "
   ```

4. **Launch the Streamlit app** for interactive exploration:
   ```bash
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8501 || streamlit run app.py --server.headless true &
   ```
   Tell the user to type their query in the search box — smart expand triggers automatically.

## Supported landmarks
- **Universities**: SMU, NUS, NTU, SUTD, SIM, SIT
- **Business hubs**: CBD, MBFC, OUE Downtown, Mapletree Business City, one-north, Changi Business Park
- **Hospitals**: SGH, NUH, TTSH
- **Areas**: Orchard, Sentosa, Changi Airport

## Example queries
- "SMU附近 1b1b 3300"
- "NUS附近便宜的1房 2500以内"
- "CBD附近 2br 5000 south facing"
- "找NTU附近的2房 3000左右"
