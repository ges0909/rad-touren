---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Preferences

Personal preferences for multi-day car road trips across Europe. Supplements `user-preferences.md` (universal rules) and `road-planner.md` (workflow and tool usage).

## Trip Profile

- Duration: 7–14 days
- Stops: 4–8 stations forming a logical loop
- Stay per stop: 1–3 nights (1 night for transit stops only)
- Max driving per day: 4 hours — if exceeded, insert an intermediate stop
- Group: 2 persons
- Vehicle: compact car, airport pickup/dropoff
- Booking: billiger-mietwagen.de

## Flight Preferences

Priority order for airport selection:

1. Direct flights from BER (always preferred)
2. Nearest airport with BER direct connection (max ~3 h drive acceptable)

Cross-border rental (EU/Schengen) is acceptable — note surcharges.

Timing:

- Outbound: early morning (07:00–09:00)
- Return: afternoon/evening (15:00–17:00)

Buffer rule (same-city start/end):

- First night at arrival city: max 1 night
- Longer stays (2+ nights) at start/end city: place at the end as flight buffer

## Interest Priorities

Apply this priority order when planning stops and activities. When a location has multiple interests, list the highest priority first.

| Priority | Emoji | Interest           | Guidance                                                                                                                             |
| -------- | ----- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1        | 🥾    | Wandern            | Main activity. Plan 1–2 day hikes (3–5 h) per stop. Require rating ≥4.0 with ≥30 reviews (AllTrails/Komoot). Always web-search.      |
| 2        | 🎨    | Moderne Kunst      | Always highlight. Include galleries, sculpture parks, contemporary museums at every stop where available.                            |
| 3        | 🏛️    | Sehenswürdigkeiten | Historic sites, UNESCO heritage, significant museums.                                                                                |
| 4        | 🌿    | Botanische Gärten  | Always mention when available in a city/region. Do not skip even if other interests are strong.                                      |
| 5        | 🍷    | Regionale Küche    | Local restaurants, wineries, food markets. See Food & Drink section below.                                                           |
| 6        | 🏊    | Baden              | Beaches, thermal baths, lakes. Especially relevant for coastal and summer trips. Check driving-day routes for en-route swim options. |

Research approach per stop:

- Hiking: web-search AllTrails, Komoot, Wikiloc — treat as dedicated day activity, not optional add-on
- Art & sights: combine Wikivoyage with web search
- Swimming: search for options along driving routes between stops

## Food & Drink

### Selection Criteria (priority order)

1. Authentic and traditional — family restaurants, local cuisine, taverns. No fine dining unless explicitly requested.
2. Regional/local over international chains
3. Markets and food halls over tourist restaurants
4. Never recommend fast food or chains
5. Rating threshold: ≥4.0 on TripAdvisor (minimum 50 reviews). Always state the rating. Mention Michelin/Bib Gourmand if applicable.
6. Cross-check high-end picks via Google Maps or TheFork/ElTenedor

### Reservations

- Popular restaurants: recommend reservation (mark with 🍷 + "**Reservierung empfohlen**")
- Always provide a no-reservation alternative nearby

### Output Format

```markdown
### 🍷 Abendessen: {Restaurant Name}

- **Lage:** {City/neighborhood}
- **Spezialität:** {Cuisine type, signature dishes}
- **Rating:** ⭐ {X.X}/5 ({N} Bewertungen, TripAdvisor) | {Michelin note if any}
- **Preis:** {€/€€/€€€} (~{range} € p.P.)
- **Reservierung:** {Empfohlen (Platform) | Nicht nötig}
- **Website:** [{domain}]({url})
- ℹ️ Zuletzt geprüft: {YYYY-MM-DD}
```

## Detours & "Unterwegs" Stops

Between main stations, suggest 1–2 optional stops (30–60 min each):

- Scenic viewpoints
- Small historic towns
- Notable cafés or regional food stops
- Photo opportunities

Format as a dedicated `**Unterwegs:**` section with distance and driving time from main route.

## Seasonal Awareness

- Check opening hours/days for museums, gardens, attractions (note weekly closures)
- Fetch weather forecast for entire trip duration via Open-Meteo
- High season (summer/holidays): emphasize advance booking recommendations
- Off-season: explicitly mark closed attractions with ⚠️
- Flag advance booking requirements: `⚠️ vorab buchen`
