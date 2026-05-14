---
inclusion: always
---

# User Preferences

Single source of truth for personal defaults across all tour types (cycling, hiking, roadtrips). Domain-specific steering files reference and extend these rules.

## Response Language

- Detect the user's input language and respond in the same language for chat, tour `.md` files, POI descriptions, and section headings.
- Code artifacts (file names, GPX metadata, MCP tool parameters, commit messages) are always in English using kebab-case.

## Travel Group

| Tour Type | Group                                  |
| --------- | -------------------------------------- |
| Default   | 2 persons                              |
| Cycling   | 2 persons + 2 bicycles (fare/transit)  |
| Car trips | Compact rental, airport pickup/dropoff |

- Car rental: book via **billiger-mietwagen.de**.

## Flight Preferences (Roadtrips)

- Prefer **direct flights from BER**. Only suggest connections when no direct option exists.
- Fallback: nearest airport with direct BER connection; accept up to ~3 h driving to reach it. Cross-border rental (EU/Schengen) is acceptable — note surcharge.
- Outbound: early morning (07:00–09:00).
- Return: afternoon/evening (15:00–17:00).

## Interests — Priority Order

Actively search for these when planning any tour. Higher priority = more prominent placement. Items marked "Always" MUST appear in output whenever found nearby.

| #   | Emoji | Interest          | Behavior                                                                                                        |
| --- | ----- | ----------------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | 🥾    | Wandern           | Day hikes, 3–5 h, moderate difficulty. Prefer ≥4.0 stars (≥30 reviews) on AllTrails/Komoot. Always show rating. |
| 2   | 🏊    | Baden             | Lakes, beaches, thermal baths, natural swimming spots.                                                          |
| 3   | 🍷    | Regionale Küche   | Local restaurants, markets, food specialties. Authentic over fancy.                                             |
| 4   | 🌿    | Botanische Gärten | **Always include when nearby.** Botanical gardens, arboretums, landscape parks.                                 |
| 5   | 🎨    | Moderne Kunst     | **Always highlight.** Galleries, sculpture parks, contemporary art museums.                                     |

### How to Apply Interests

- Use the emoji from the table above consistently in all tour documents.
- When multiple interests apply to one location, list highest-priority first.
- Cycling tours: map interests to Overpass POI presets — `kunst`, `sehenswuerdigkeiten`, `einkehr`, `badestellen`.
- Roadtrips: use web search to find POIs matching these interests.

## Food & Drink

Rules for restaurant/food recommendations (in priority order):

1. **Bodenständig und authentisch** — Traditionsküche, Familienrestaurants, Gasthäuser. No fine dining unless explicitly requested.
2. Regional/local over international chains.
3. Markets and food halls over tourist restaurants.
4. **Never** recommend fast food or chain restaurants.
5. Rating threshold: ≥4.0 on TripAdvisor (min. 50 reviews). Always include rating when available. Mention Michelin/Bib Gourmand if applicable.
6. Cross-check high-end picks via Google Maps or TheFork/ElTenedor.

## Accommodation

Rules for lodging recommendations:

- Small/familial hotels, B&Bs, pensiones — no large chains.
- Breakfast included preferred.
- Booking platform: **booking.com**.
- Location: central, walkable to sights.
- Budget: ~80–150 €/night for 2 persons.
- Mention sauna/wellness when available.
- Rating threshold: ≥8.5 on booking.com (min. 50 reviews). Always show rating + review count. Discard options rated <7.5 or with <20 reviews unless no alternative exists.
- Cross-check: when <50 reviews or unusual rating, verify via TripAdvisor or Trivago. Note discrepancies.

## Content Integrity

These rules are non-negotiable for all generated content:

| Rule               | Requirement                                                                                  |
| ------------------ | -------------------------------------------------------------------------------------------- |
| No fabrication     | Only present data from API results or web search. If unavailable, state explicitly.          |
| Emoji consistency  | Use interest-table emoji for POIs. Use 🍺 for beer gardens/restaurants (Overpass `einkehr`). |
| Deduplication      | One entry per POI; remove duplicates within 200 m radius.                                    |
| Seasonal awareness | Flag closures, limited hours, off-season risks.                                              |
| Source attribution | Append `ℹ️ Zuletzt geprüft: {date}` for web-sourced data.                                    |
| Links              | Official websites for major POIs only. No Google Maps, TripAdvisor, or temporary URLs.       |
| Unverifiable data  | Mark with `ℹ️ Nicht verifiziert.` — never guess or invent details.                           |

## Route Discovery & Reviews

### Waymarked Trails (official marked routes)

Use these MCP tools in sequence for route research:

1. `search_routes(query, activity)` — find routes by name, region, or keyword.
2. `get_route_details(route_id, activity)` — retrieve length, markings, operator.
3. `get_route_segments(route_id, activity)` — get stages and towns along the route.

### Review Lookup (web search)

**Always look up ratings when suggesting hiking routes.** Apply these thresholds:

- Prefer: ≥4.0 stars with ≥30 reviews.
- Discard: <3.5 stars or <10 reviews (unless no alternative).

Procedure:

1. Search: `"{route name}" AllTrails review`
2. Search: `"{route name}" Komoot Bewertung`
3. Search: `"{route name}" Wikiloc rating` (especially Spain/Portugal)
4. Summarize: rating, praise/complaints, difficulty, surface quality.
5. Mark output: `ℹ️ Bewertungen aus Web-Recherche ({date}), nicht per API verifiziert.`

### Tool Selection Guide

| Intent                 | Tool                                                   |
| ---------------------- | ------------------------------------------------------ |
| Routes in a region     | Waymarked Trails `search_routes`                       |
| Route recommendation   | Waymarked Trails `search_routes` + `get_route_details` |
| Route rating/review    | Web search (AllTrails/Komoot)                          |
| Custom cycling tour    | BRouter `calculate_route`                              |
| Custom car/hiking tour | OpenRouteService `calculate_route`                     |
| Experience reports     | Web search (Komoot/AllTrails/Outdooractive)            |
