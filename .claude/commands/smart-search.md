---
description: Find optimal rental areas based on commute to multiple destinations (school, office, etc.). Usage: /smart-search <describe your locations and preferences>
---

# Smart Commute Search

The user wants to find the best area to live based on their daily commute destinations. Their description: $ARGUMENTS

## What to do

1. **Extract locations and preferences** from the user's description:
   - Destinations: school, office, gym, partner's workplace, etc.
   - Each needs a label + address (you may need to infer the full address)
   - Budget, bedrooms, extra preferences (facing, floor, etc.)

2. **Run the commute analysis** using the project's commute module:
   ```bash
   cd /Users/wanglei/Projects/others/rental_conda_sg && python -c "
   from commute import Location, analyze_commute, generate_queries, format_analysis_report
   
   locations = [
       Location(name='LABEL1', address='ADDRESS1'),
       Location(name='LABEL2', address='ADDRESS2'),
   ]
   scored = analyze_commute(locations)
   queries = generate_queries(scored, bedrooms=BEDS, price_min=MIN, price_max=MAX, extra_criteria='EXTRA')
   print(format_analysis_report(locations, queries))
   "
   ```

3. **For each recommended area**, run a search to get specific condos:
   ```bash
   cd /Users/wanglei/Projects/others/rental_conda_sg && python -c "
   from scraper.data_gov import fetch_rental_data, get_districts_for_mrt
   df = fetch_rental_data()
   districts = get_districts_for_mrt('STATION_NAME')
   area = df[(df['postal_district'].isin(districts)) & (df['est_rent_1br'] >= MIN) & (df['est_rent_1br'] <= MAX)]
   for _, r in area.head(5).iterrows():
       print(f\"{r['project_name']}: \${int(r['est_rent_1br']):,}/mo (median \${r['median_psf']:.2f} psf)\")
   "
   ```

4. **Present results** as a ranked list:
   - Why each area is recommended (commute to each destination, direct MRT lines)
   - Specific condos available with estimated rents
   - Links to 99.co/PropertyGuru for live listings

5. **Also launch the Streamlit app** in Smart Commute mode:
   ```bash
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8501 || (cd /Users/wanglei/Projects/others/rental_conda_sg && streamlit run app.py --server.headless true &)
   ```
   Tell the user to switch to "Smart Commute" mode in the sidebar.

## Example descriptions:
- "I study at SMU and work at OUE Downtown One, looking for 1br around 3300"
- "I work at Changi Business Park, my partner works at Raffles Place, budget 4000 for 2br"
- "NUS student, part-time at Orchard, want studio under 2500"

## Common Singapore landmarks:
- **Universities**: SMU (Bras Basah), NUS (Kent Ridge), NTU (Pioneer), SUTD (Upper Changi)
- **Business hubs**: CBD/Raffles Place, Changi Business Park, one-north, Mapletree Business City
- **Malls**: Orchard Road, Bugis Junction, VivoCity (HarbourFront)
