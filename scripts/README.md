# Scripts

Standalone-Skripte für die offline-Generierung von Tourkarten (PNG).

## render_roadtrip_map.py

Rendert eine Roadtrip-Route als PNG-Karte mit OpenStreetMap-Hintergrund, Stationsmarkern und POI-Icons.

**Verwendung:**

```bash
python scripts/render_roadtrip_map.py <gpx_file> <output_png> \
    [--stations 'Name:lon,lat' ...] \
    [--pois 'category:name:lon,lat' ...] \
    [--width 900] [--height 600]
```

**Beispiel:**

```bash
python scripts/render_roadtrip_map.py \
    trips/road/gpx/nordspanien-kueste.gpx \
    trips/road/img/nordspanien-kueste.png \
    --stations 'T1 Bilbao:-2.9253,43.2627' 'T2-3 San Sebastián:-1.9812,43.3183' \
    --pois 'art:Guggenheim:-2.9340,43.2687' 'wine:Bodegas Ysios:-2.5950,42.5680'
```

**POI-Kategorien:**

| Kategorie | Farbe   | Icon               |
| --------- | ------- | ------------------ |
| art       | #9B59B6 | Kunst & Museen     |
| hike      | #27AE60 | Wandern            |
| swim      | #3498DB | Baden              |
| food      | #E67E22 | Essen & Trinken    |
| wine      | #8E44AD | Weingüter          |
| sight     | #2C3E50 | Sehenswürdigkeiten |
| nature    | #1ABC9C | Natur & Parks      |
| coffee    | #795548 | Kaffee             |

**Dependencies:**

```bash
pip install staticmap pillow
```

**Hinweis:** Dieses Script wird für die statischen Tour-Dokumente in `trips/` verwendet. Die Web-App rendert Routen live via Leaflet im Browser.

## icons/

18×18px PNG-Icons für die POI-Kategorien auf der Karte.
