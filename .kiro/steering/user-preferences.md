---
inclusion: always
---

# User Preferences

Single source of truth for personal defaults shared across all tour types (cycling, hiking, roadtrips). Domain-specific steering files (cycling-tour-planning.md, roadtrip-planning.md) reference and extend these rules.

## Output Language

- User-facing text (tour descriptions, summaries, chat responses, section headings): **German**
- Code, file names, GPX metadata (`track_name`), MCP tool parameters, commit messages: **English/kebab-case**

## Travel Group

- **Default group size**: 2 persons
- **Cycling**: 2 persons + 2 bicycles (affects fare calculations and transit constraints)
- **Car trips**: Compact rental car, pickup/dropoff at airport

## Home Base

- **Station**: S Blankenfelde (TF) Bhf
- **Available lines**: S2, RB24, RE5, RE7, RE8
- **Default departure**: ~09:00 Uhr
- **Scope**: All Berlin/Brandenburg tours must be reachable from this station

## Flight Preferences (Roadtrips)

- Prefer **direct flights** from BER. Only suggest connections if no direct option exists.
- **Fallback**: If no direct flight to the destination exists, search for the nearest airport with a direct BER connection. Accept up to ~3 hours driving from that airport to the trip region. Note: cross-border rental car usage (e.g., Portugal → Spain) is acceptable within EU/Schengen — book with "cross-border" option and note the surcharge in the cost estimate.
- Outbound: early morning (07:00–09:00) to maximize the first day
- Return: afternoon/evening (15:00–17:00) to use the last morning
- Preferred days: avoid Friday/Monday (business surcharge). Tuesday–Thursday outbound, Sunday return.

## Interests — Priority Order

When planning any tour, actively search for these interests using available tools (Overpass POI search, web search). Higher priority = more prominent placement in output. Items marked "always" MUST appear whenever found, even if not the tour's main theme.

| Priority | Emoji | Interest                  | Behavior                                                                                   |
| -------- | ----- | ------------------------- | ------------------------------------------------------------------------------------------ |
| 1        | 🎨    | Moderne Kunst             | **Always highlight.** Galleries, sculpture parks, installations, contemporary art museums. |
| 2        | 🥾    | Wandern                   | Day hikes, nature trails, coastal paths. Moderate difficulty, 3–5 hours.                   |
| 3        | 🏊    | Baden                     | Lakes, beaches, thermal baths, natural swimming spots.                                     |
| 4        | 🍷    | Regionale Küche           | Local restaurants, markets, food specialties. Authentic over fancy.                        |
| 5        | 🌿    | Botanische Gärten & Parks | **Always include when available nearby.** Botanical gardens, arboretums, landscape parks.  |
| 6        | ☕    | Kaffeeröstereien          | **Always mention when found.** Specialty roasters with tastings or café.                   |
| 7        | 🍇    | Weingüter                 | **Always include in wine regions.** Wineries with tastings/cellar door.                    |
| 8        | 🪖    | Kalter Krieg              | **Always highlight.** Cold War sites, bunkers, border installations, military history.     |

### Applying Interests

- Use the emoji from this table consistently in all tour documents when listing POIs
- When multiple interests overlap at one location, list the highest-priority one first
- For cycling tours: map to Overpass presets (`kunst`, `sehenswuerdigkeiten`, `einkehr`, `badestellen`)
- For roadtrips: use web search to find relevant POIs matching these interests

## Food & Drink Rules

Apply when selecting restaurants, cafés, and stops:

1. Prioritize **Cafés mit selbstgebackenem Kuchen** (homemade cake)
2. Regional/local cuisine over international chains
3. Markets and food halls over tourist restaurants
4. Wine tastings and craft coffee over generic options
5. **Never** recommend fast food or chain restaurants

## Accommodation Rules

Apply when suggesting overnight stays:

- Small/boutique over large chains
- Central location, walkable to sights
- Price range: ~80–150 €/night for 2 persons
- Sauna/wellness is a plus — mention when available
- **Never** recommend hostels or budget chains

## Content Integrity Rules

These rules govern all output across the project:

- **No fabrication**: Never invent POI names, opening hours, prices, or travel times. Only present data verified via API results or web search. If data is unavailable, state that explicitly.
- **Emoji consistency**: Always use the emoji from the interest table above when listing POIs. Use 🍺 for beer gardens/restaurants/cafés in tour documents (Overpass `einkehr` preset).
- **Deduplication**: When multiple sources return the same POI, keep only one entry — prefer the version with more detail. Remove duplicates within 200 m of each other.
- **Seasonal awareness**: Flag seasonal closures, limited opening hours, or weather-dependent availability. Warn about off-season risks.
- **Source attribution**: When information comes from web search, note the check date: `ℹ️ Zuletzt geprüft: {date}`.
- **Links**: Add hyperlinks to official websites for major POIs (museums, national parks, tourism boards, notable restaurants). Prefer stable URLs (official sites, regional tourism portals like reiseland-brandenburg.de, visitberlin.de). Do **not** link to Google Maps, TripAdvisor reviews, or temporary pages.
- **Unverifiable data**: If an API is unavailable or data cannot be confirmed, add `ℹ️ Nicht verifiziert.` rather than omitting the section or guessing.
