---
inclusion: always
---

# User Preferences

Shared defaults for all tour types (cycling, hiking, roadtrips). Domain-specific steering files reference this document — keep it as the single source of truth for personal preferences.

## Output Language

- All user-facing text (tour descriptions, summaries, chat responses): **German**
- Code, file names, GPX metadata, tool parameters: **English/kebab-case**

## Travel Group

- **Persons**: 2
- **Cycling**: 2 persons + 2 bicycles
- **Car trips**: Compact rental car, pickup/dropoff at airport

## Home Base (Berlin/Brandenburg Tours)

- **Station**: S Blankenfelde (TF) Bhf
- **Default departure**: ~09:00 Uhr

## Interests — Priority Order

When planning any tour, actively search for and surface these interests. Higher priority = more prominent placement in output. Items marked "always" MUST appear in the output whenever found, even if not the main theme of the tour.

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

## Food & Drink Rules

Apply these preferences when selecting restaurants, cafés, and stops:

1. Prioritize **cafés mit selbstgebackenem Kuchen** (homemade cake)
2. Regional/local cuisine over international chains
3. Markets and food halls over tourist restaurants
4. Wine tastings and craft coffee over generic options
5. Never recommend fast food or chain restaurants

## Accommodation Rules

Apply when suggesting overnight stays:

- Small/boutique over large chains
- Central location, walkable to sights
- Price range: ~80–150 €/night for 2 persons
- Sauna/wellness is a plus — mention when available
- Never recommend hostels or budget chains

## Content Rules

These rules govern how the assistant produces output for this project:

- **No fabrication**: Never invent POI names, opening hours, prices, or travel times. Only present verified data (API results or web search).
- **Emoji usage**: Use the emoji from the interest table consistently when listing POIs in tour documents.
- **Deduplication**: When multiple sources return the same POI, keep only one entry. Prefer the version with more detail.
- **Seasonal awareness**: Flag seasonal closures, limited opening hours, or weather-dependent availability.
- **Source attribution**: When information comes from web search, note the check date with `ℹ️ Zuletzt geprüft: {date}`.
