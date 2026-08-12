# StockMind Market Research — Astrology Provider Setup

## Recommended architecture

StockMind now separates the **astrological calculation layer** from the **market-analysis layer**:

`IDX/security master → listing date → ephemeris provider → Natal Chart + Transit → Fibonacci Time/Price → Technical/Fundamental/Bandarmology → AI summary`

For the astronomical/ephemeris layer, the most defensible foundation is **Swiss Ephemeris by Astrodienst**. Astrodienst describes Swiss Ephemeris as a high-accuracy planetary calculation library and states that it is used by most computer astrology programs. It is dual-licensed: AGPL or a commercial Swiss Ephemeris Professional license. A proprietary hosted product should review the commercial-license route before distributing or activating a public service that incorporates the library.

For a hosted REST API, StockMind includes an adapter compatible with **Morphemeris**, whose documentation describes it as a REST API built on Swiss Ephemeris.

## Option A — Hosted REST provider (fastest)

1. Create an API account with your chosen ephemeris provider.
2. Copy the API base URL and API key into `backend/.env`:

```env
ASTRO_PROVIDER=morphemeris
ASTRO_BASE_URL=https://api.morphemeris.com
ASTRO_API_KEY=YOUR_PROVIDER_KEY
ASTRO_TIMEZONE=Asia/Jakarta
ASTRO_DEFAULT_HOUR=9
ASTRO_LATITUDE=-6.2088
ASTRO_LONGITUDE=106.8456
```

3. Restart the backend.
4. In the web app open **Astro Market Deep Dive**, enter the ticker and date, then press **Search & Analisa**.
5. The endpoint `/api/astrology/deep-dive/{symbol}` will request natal and transit positions from the configured ephemeris provider.

The adapter currently expects a Morphemeris-compatible positions endpoint:

`GET /v1/positions?datetime=<ISO>&bodies=sun,moon,mercury,venus,mars,jupiter,saturn,uranus,neptune,pluto`

## Option B — Direct Swiss Ephemeris

For a self-hosted production implementation, use Swiss Ephemeris directly rather than a third-party REST API. Decide the license before deployment:

- AGPL route: the application must satisfy the AGPL obligations described by Astrodienst.
- Commercial route: purchase the Swiss Ephemeris Professional license from Astrodienst for a proprietary service.

The StockMind code keeps the provider interface isolated in `backend/app/astrology_provider.py`, so a direct Swiss-Ephemeris implementation can replace the REST adapter without changing the front-end.

## Important distinction

There is no single “official Astronacci API” that automatically generates the complete trading interpretation shown in the reference image. The **planet positions** can come from Swiss Ephemeris or an API built on it. The five-stage StockMind interpretation — Financial, Fibonacci Time, Technical, Fundamental, and Bandarmology — is an application-level heuristic and should remain clearly labeled as experimental.

## Market-data connection

The Astrology board also uses market prices to calculate Fibonacci price levels and the daily chart. Keep using an **IDX-licensed/authorized market-data provider** for production prices, corporate actions, and broker data. The market provider and astrology provider should be configured independently.

## Production flow

1. Security master supplies the company's listing date.
2. The user selects analysis date and optional IPO time/location.
3. Ephemeris provider returns natal and current transit positions.
4. Licensed market provider returns OHLCV.
5. StockMind computes Fibonacci price/time levels and technical context.
6. Broker/fundamental providers populate Bandarmology and fundamental stages.
7. AI summarizes the five stages and produces the scenario roadmap.

The UI keeps a demo fallback so the Astro Deep Dive page remains visible before the external providers are connected.
