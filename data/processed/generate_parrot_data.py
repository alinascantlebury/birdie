"""
generate_parrot_data_v2.py
Extracts Red-masked Parakeet only from ebd_clean.csv

Run from: ~/Desktop/data/birdie/data/processed/
  python3 generate_parrot_data_v2.py
"""

import pandas as pd
import json
from collections import defaultdict

print("Loading ebd_clean.csv...")
df = pd.read_csv('ebd_clean.csv', low_memory=False)

# Filter to Red-masked Parakeet only (the SF colony species)
target = ['Red-masked Parakeet', 'Mitred/Red-masked Parakeet']
parrots = df[df['COMMON NAME'].isin(target)].copy()
print(f"Red-masked Parakeet rows: {len(parrots)}")

parrots = parrots.dropna(subset=['LATITUDE','LONGITUDE'])

# Export raw coords
coords = []
for _, row in parrots.iterrows():
    coords.append({
        "lat": float(row['LATITUDE']),
        "lng": float(row['LONGITUDE']),
        "year": int(row['year']) if pd.notna(row['year']) else None,
        "locality": str(row['LOCALITY']) if pd.notna(row['LOCALITY']) else ""
    })

with open('parrot_coords.json', 'w') as f:
    json.dump(coords, f, indent=2)
print(f"Exported {len(coords)} coords to parrot_coords.json")

# Aggregate by location + year
LOCATIONS = {
    'Fort Mason':          (37.807, -122.428),
    'Telegraph Hill':      (37.800, -122.408),
    'Corona Heights':      (37.764, -122.439),
    'Buena Vista Park':    (37.770, -122.442),
    'USF / Lone Mountain': (37.777, -122.452),
    'Presidio':            (37.793, -122.456),
    'Golden Gate Park':    (37.771, -122.468),
}

def nearest_location(lat, lng):
    best_name, best_dist = None, float('inf')
    for name, (clat, clng) in LOCATIONS.items():
        dist = ((lat - clat)**2 + (lng - clng)**2) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name if best_dist < 0.014 else 'Other'

by_loc_year = defaultdict(lambda: defaultdict(int))
for c in coords:
    if c['year'] and c['lat'] and c['lng']:
        loc = nearest_location(c['lat'], c['lng'])
        if loc != 'Other':
            by_loc_year[loc][c['year']] += 1

all_years = sorted(set(yr for loc_data in by_loc_year.values() for yr in loc_data))
# filter to 2010 onwards
all_years = [y for y in all_years if y >= 2010]
print(f"Years: {all_years}")

result = {}
for loc_name in LOCATIONS:
    result[loc_name] = {
        "lat": LOCATIONS[loc_name][0],
        "lng": LOCATIONS[loc_name][1],
        "years": {yr: by_loc_year[loc_name].get(yr, 0) for yr in all_years}
    }

print("\nRed-masked Parakeet sightings per location:")
for loc, d in result.items():
    total = sum(d["years"].values())
    if total > 0:
        peak_yr = max(d["years"], key=d["years"].get)
        print(f"  {loc}: total={total}, peak={d['years'][peak_yr]} in {peak_yr}")

with open('parrot_by_location_year.json', 'w') as f:
    json.dump(result, f, indent=2)

# Line chart
th = result['Telegraph Hill']['years']
fm = result['Fort Mason']['years']
line_data = [{"year": yr, "fort_mason": fm.get(yr,0), "telegraph_hill": th.get(yr,0)}
             for yr in all_years]
with open('parrot_line_chart.json', 'w') as f:
    json.dump(line_data, f, indent=2)

print("\nDone. Files written:")
print("  parrot_coords.json")
print("  parrot_by_location_year.json")
print("  parrot_line_chart.json")