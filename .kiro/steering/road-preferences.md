---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Preferences — Europa Mehrtagstrips

Persönliche Präferenzen für Auto-Rundreisen. Diese Datei ergänzt `user-preferences.md` (universelle Regeln) und `road-planner.md` (technische Workflow-Regeln).

## Trip Profile

| Eigenschaft       | Wert                                              |
| ----------------- | ------------------------------------------------- |
| Dauer             | 7–14 Tage                                         |
| Stops             | 4–8 Stationen, logische Rundfahrt                 |
| Stay per Stop     | 1–3 Nächte (1 Nacht bei Durchgangsorten)          |
| Driving per Day   | Max. 4 Stunden (bei Überschreitung: Stop einfügen) |
| Gruppe            | 2 Personen                                        |
| Fahrzeug          | Kompaktwagen, Flughafen Pickup/Dropoff            |
| Booking           | billiger-mietwagen.de                             |

## Flight Preferences

- **Priorität 1:** Direktflüge ab BER
- **Priorität 2:** Nächster Flughafen mit BER-Direktverbindung (max. ~3 h Fahrzeit akzeptabel)
- **Grenzüberschreitende Anmietung:** Akzeptabel (EU/Schengen), Zuschlag beachten
- **Abflug:** Früh morgens (07:00–09:00 Uhr)
- **Rückflug:** Nachmittag/Abend (15:00–17:00 Uhr)

**Buffer-Regel (Same-City Start/End):**
- Erste Übernachtung am Ankunftsort: max. 1 Nacht
- Längerer Aufenthalt (2+ Nächte): ans Ende legen (Flug-Buffer)

## Interests — Priorität (Mehrtagstrips)

Diese Prioritätsreihenfolge für Roadtrips verwenden. Bei mehreren Interests pro Location höchste Priorität zuerst nennen.

| #   | Emoji | Interest          | Verhalten                                                                                                        |
| --- | ----- | ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1   | 🥾    | Wandern           | **Highest priority.** Tageswanderungen (3–5 h) als Haupt-Aktivität. Rating ≥4.0 (≥30 Reviews, AllTrails/Komoot) |
| 2   | 🎨    | Moderne Kunst     | **Immer hervorheben.** Galerien, Skulpturenparks, zeitgenössische Museen.                                        |
| 3   | 🏛️    | Sehenswürdigkeiten| Historische Stätten, UNESCO-Welterbe, bedeutende Museen.                                                         |
| 4   | 🌿    | Botanische Gärten | **Immer erwähnen wenn in Stadt/Region verfügbar.**                                                               |
| 5   | 🍷    | Regionale Küche   | Lokale Restaurants, Weingüter, Food-Märkte.                                                                      |
| 6   | 🏊    | Baden             | Strände, Thermen, Seen. Besonders relevant bei Küsten-/Sommer-Trips.                                             |

**Anwendung:**
- Pro Stop: 1–2 Wanderungen recherchieren (Web-Suche: AllTrails, Komoot, Wikiloc)
- Kunst & Sehenswürdigkeiten: Wikivoyage + Web-Suche kombinieren
- Wanderungen als eigene Tages-Aktivität einplanen (nicht nur „optional")

## Food & Drink (Mehrtagstrips)

Regeln für Restaurant-Empfehlungen (Prioritätsreihenfolge):

1. **Bodenständig und authentisch** — Traditionsküche, Familienrestaurants, Gasthäuser. Kein Fine Dining außer explizit gewünscht.
2. Regional/lokal vor internationalen Ketten
3. Märkte und Food Halls vor Touristen-Restaurants
4. **Niemals** Fast Food oder Ketten empfehlen
5. **Rating-Schwelle:** ≥4.0 auf TripAdvisor (mind. 50 Bewertungen). Immer Rating angeben. Michelin/Bib Gourmand erwähnen falls vorhanden.
6. **Cross-Check:** High-End-Picks via Google Maps oder TheFork/ElTenedor gegenchecken

**Reservierung:**
- Bei beliebten Restaurants: Reservierung empfehlen (mit 🍷 + „**Reservierung empfohlen**")
- Alternative ohne Reservierung angeben

**Format:**
```
### 🍷 Abendessen: Casa Marcelo

- **Lage:** Santiago de Compostela Altstadt
- **Spezialität:** Galicische Küche, Tasting Menu
- **Rating:** ⭐ 4.6/5 (327 Bewertungen, TripAdvisor) | Michelin Bib Gourmand
- **Preis:** €€€ (~45–60 € p.P.)
- **Reservierung:** Empfohlen (TheFork)
- **Website:** [casamarcelo.net](https://...)
- ℹ️ Zuletzt geprüft: 2026-08-02
```

## Accommodation

Regeln für Unterkunfts-Empfehlungen:

- **Typ:** Kleine/familiäre Hotels, B&Bs, Pensiones — keine großen Ketten
- **Frühstück:** Inklusive bevorzugt
- **Booking-Plattform:** booking.com
- **Lage:** Zentral, fußläufig zu Sehenswürdigkeiten
- **Budget:** ~80–150 €/Nacht für 2 Personen
- **Wellness:** Sauna/Wellness-Bereich erwähnen falls vorhanden
- **Rating-Schwelle:** ≥8.5 auf booking.com (mind. 50 Bewertungen). Immer Rating + Review-Count angeben.
- **Verwerfen:** <7.5 oder <20 Reviews (außer keine Alternative)
- **Cross-Check:** Bei <50 Reviews oder ungewöhnlichem Rating via TripAdvisor oder Trivago verifizieren. Diskrepanzen notieren.

**Format:**
```
### 🏨 Übernachtung: Hotel Casa Antiga

- **Lage:** 5 Gehminuten zur Altstadt
- **Zimmer:** 12 Zimmer, familiengeführt seit 1987
- **Rating:** ⭐ 9.2/10 (184 Bewertungen, booking.com)
- **Preis:** ~95 €/Nacht (Frühstück inklusive)
- **Extras:** Innenhof, kostenlose Weinprobe
- **Booking:** [booking.com/hotel/casa-antiga](https://...)
- ℹ️ Zuletzt geprüft: 2026-08-02
```

## Detours & "Unterwegs"-Stops

Empfehle 30–60 min optionale Stops zwischen Hauptstationen:

- Aussichtspunkte
- Kleine historische Orte
- Besondere Cafés/Restaurants
- Fotospots

Format: Als eigener Abschnitt `**Unterwegs:**` mit Entfernung/Fahrzeit vom Hauptroute.

## Seasonal Awareness

- **Saison-Check:** Öffnungszeiten von Museen, Gärten, Attraktionen prüfen
- **Wetter:** Prognose für gesamte Trip-Dauer abrufen (Open-Meteo)
- **Hochsaison:** Bei Sommer/Ferienzeiten Buchungs-Empfehlung verstärken
- **Off-Season:** Geschlossene Attraktionen explizit kennzeichnen
