# SG Condo Rental Search 🏠

An interactive tool for searching and comparing Singapore condo rentals, powered by URA official data.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Natural Language Search** — Type queries in English or Chinese, e.g. `Queenstown 1b1b 3300` or `找Bishan附近2房4000以内`
- **URA Official Data** — 551 condo projects with median rent per square foot, P25-P75 ranges, and contract volumes (Q4 2025)
- **Interactive Map** — Folium map with MRT stations, condo markers color-coded by price
- **Smart Filtering** — Filter by MRT proximity, bedrooms, price range, and sort by rent/popularity
- **Direct Links** — Click through to 99.co / PropertyGuru for live listings on each condo
- **Bargaining Reference** — P25-P75 price range helps you negotiate better deals

## Quick Start

```bash
# Clone
git clone https://github.com/demoleiwang/SGCondoRentalSearch.git
cd SGCondoRentalSearch

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

### Option 1: Natural Language

Type your query in the search box:

| Query | What it does |
|---|---|
| `Queenstown 1b1b 3300` | 1BR near Queenstown MRT, ~$3,300/mo |
| `找Bishan附近2房4000以内` | 2BR near Bishan, max $4,000 |
| `Paya Lebar 1 bedroom 3000-3500` | 1BR near Paya Lebar, $3,000-$3,500 |
| `Holland Village studio 2500以下 high floor` | Studio near Holland Village, max $2,500, high floor |

### Option 2: Sidebar Filters

Use the sidebar to select MRT station, bedroom count, and price range, then click **Search**.

### Claude Code Integration

If you use [Claude Code](https://claude.ai/claude-code), there's a built-in skill:

```
/search-condo Queenstown 1b1b 3300
```

## How It Works

1. **Data Source** — Fetches URA rental statistics from [data.gov.sg](https://data.gov.sg) (updated quarterly)
2. **Rent Estimation** — Multiplies median $/psf by typical unit sizes (e.g. 530 sqft for 1BR)
3. **MRT Mapping** — Maps MRT stations to postal districts to find nearby condos
4. **Geocoding** — Uses [OneMap API](https://www.onemap.gov.sg/) to plot condos on the map
5. **Live Listings** — Generates 99.co and PropertyGuru search URLs for each project

## Data Sources

| Source | Type | Access |
|---|---|---|
| [URA via data.gov.sg](https://data.gov.sg) | Official rental statistics | Free API |
| [OneMap](https://www.onemap.gov.sg/) | Geocoding | Free API |
| [99.co](https://www.99.co) | Live rental listings | Via browser link |
| [PropertyGuru](https://www.propertyguru.com.sg) | Live rental listings | Via browser link |
| [URA Rental Transactions](https://www.ura.gov.sg/property-market-information/pmiResidentialRentalSearch) | Historical transactions | Web portal |

## Project Structure

```
├── app.py                    # Streamlit dashboard
├── config.py                 # Constants and configuration
├── engine.py                 # NL query parser + filter engine
├── geo.py                    # Haversine distance, MRT lookup, geocoding
├── requirements.txt          # Python dependencies
├── data/
│   └── mrt_stations.json     # 140 MRT stations with coordinates
└── scraper/
    ├── data_gov.py           # data.gov.sg URA data fetcher
    └── ninety_nine.py        # 99.co scraper (backup, Cloudflare-blocked)
```

## Rental Tips

From the [rental guide](rednote_experience.txt):

1. **Find the unit number** — Google `"condo name" + brochure` for floor plans
2. **Check URA history** — Look up past rental transactions for the exact unit type
3. **Cross-reference platforms** — Compare prices across 99.co, PropertyGuru, and SRX
4. **Use P25 as your target** — The 25th percentile is a realistic bargaining target
5. **Know your leverage** — Historical data gives you concrete numbers to negotiate with

## Contributing

Issues and PRs welcome. This is a community tool — if you find better data sources or have feature ideas, please share!

## License

MIT
