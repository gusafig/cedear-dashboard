"""
fetch_data.py
Descarga precios de Yahoo Finance para acciones con CEDEAR en BYMA.
Genera data/market_data.json que consume el dashboard.
Soporta datos diarios y semanales.
"""

import json
import os
from datetime import datetime, timedelta
import yfinance as yf

# ── Universo CEDEAR ─────────────────────────────────────────────────────────
CEDEARS = {
    # Tecnología
    "AAPL":  {"name": "Apple",           "sector": "tech"},
    "MSFT":  {"name": "Microsoft",       "sector": "tech"},
    "GOOGL": {"name": "Alphabet",        "sector": "tech"},
    "AMZN":  {"name": "Amazon",          "sector": "tech"},
    "TSLA":  {"name": "Tesla",           "sector": "tech"},
    "META":  {"name": "Meta",            "sector": "tech"},
    "NVDA":  {"name": "NVIDIA",          "sector": "tech"},
    "NFLX":  {"name": "Netflix",         "sector": "tech"},
    "ORCL":  {"name": "Oracle",          "sector": "tech"},
    "CRM":   {"name": "Salesforce",      "sector": "tech"},
    "INTC":  {"name": "Intel",           "sector": "tech"},
    "AMD":   {"name": "AMD",             "sector": "tech"},
    "QCOM":  {"name": "Qualcomm",        "sector": "tech"},
    "ADBE":  {"name": "Adobe",           "sector": "tech"},
    "PYPL":  {"name": "PayPal",          "sector": "tech"},
    "UBER":  {"name": "Uber",            "sector": "tech"},
    "SPOT":  {"name": "Spotify",         "sector": "tech"},
    "SHOP":  {"name": "Shopify",         "sector": "tech"},
    # Finanzas
    "JPM":   {"name": "JPMorgan",        "sector": "finance"},
    "GS":    {"name": "Goldman Sachs",   "sector": "finance"},
    "BAC":   {"name": "Bank of America", "sector": "finance"},
    "C":     {"name": "Citigroup",       "sector": "finance"},
    "WFC":   {"name": "Wells Fargo",     "sector": "finance"},
    "MS":    {"name": "Morgan Stanley",  "sector": "finance"},
    "BLK":   {"name": "BlackRock",       "sector": "finance"},
    "AXP":   {"name": "American Express","sector": "finance"},
    "V":     {"name": "Visa",            "sector": "finance"},
    "MA":    {"name": "Mastercard",      "sector": "finance"},
    # Energía
    "XOM":   {"name": "ExxonMobil",      "sector": "energy"},
    "CVX":   {"name": "Chevron",         "sector": "energy"},
    "COP":   {"name": "ConocoPhillips",  "sector": "energy"},
    "SLB":   {"name": "Schlumberger",    "sector": "energy"},
    "BP":    {"name": "BP",              "sector": "energy"},
    # Consumo
    "WMT":   {"name": "Walmart",         "sector": "consumer"},
    "KO":    {"name": "Coca-Cola",       "sector": "consumer"},
    "PG":    {"name": "Procter & Gamble","sector": "consumer"},
    "MCD":   {"name": "McDonald's",      "sector": "consumer"},
    "NKE":   {"name": "Nike",            "sector": "consumer"},
    "SBUX":  {"name": "Starbucks",       "sector": "consumer"},
    "DIS":   {"name": "Disney",          "sector": "consumer"},
    "AMGN":  {"name": "Amgen",           "sector": "consumer"},
    # Salud
    "JNJ":   {"name": "Johnson & Johnson","sector": "health"},
    "PFE":   {"name": "Pfizer",          "sector": "health"},
    "MRK":   {"name": "Merck",           "sector": "health"},
    "ABBV":  {"name": "AbbVie",          "sector": "health"},
    "UNH":   {"name": "UnitedHealth",    "sector": "health"},
    "LLY":   {"name": "Eli Lilly",       "sector": "health"},
    # Materiales / Industrial
    "CAT":   {"name": "Caterpillar",     "sector": "industrial"},
    "BA":    {"name": "Boeing",          "sector": "industrial"},
    "GE":    {"name": "GE Aerospace",    "sector": "industrial"},
    "MMM":   {"name": "3M",              "sector": "industrial"},
    "HON":   {"name": "Honeywell",       "sector": "industrial"},
}

CEDEARS = dict(sorted(CEDEARS.items()))
TICKERS = list(CEDEARS.keys())


def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute_ema(closes, period):
    if len(closes) < period:
        return None
    k   = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return round(ema, 2)


def compute_macd(closes):
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    if ema12 is None or ema26 is None:
        return None, None, None
    macd_line = round(ema12 - ema26, 4)
    if len(closes) >= 35:
        macd_series = []
        k12 = 2 / 13
        k26 = 2 / 27
        e12 = sum(closes[:12]) / 12
        e26 = sum(closes[:26]) / 26
        for p in closes[26:]:
            e12 = p * k12 + e12 * (1 - k12)
            e26 = p * k26 + e26 * (1 - k26)
            macd_series.append(e12 - e26)
        signal = compute_ema(macd_series, 9)
    else:
        signal = None
    hist = round(macd_line - signal, 4) if signal else None
    return macd_line, signal, hist


def compute_sma(closes, period):
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)


def fetch_all(interval="1d"):
    end_date   = datetime.today()
    days       = 365 * 3
    start_date = end_date - timedelta(days=days)

    print(f"[{datetime.now().isoformat()}] Descargando {len(TICKERS)} tickers (interval={interval})...")

    raw = yf.download(
        TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    results = {}

    for sym in TICKERS:
        try:
            if len(TICKERS) == 1:
                df = raw
            else:
                df = raw[sym] if sym in raw.columns.get_level_values(0) else None

            if df is None or df.empty:
                print(f"  [SKIP] {sym}: sin datos")
                continue

            df     = df.dropna(subset=["Close"])
            closes  = df["Close"].tolist()
            volumes = df["Volume"].tolist()

            if len(closes) < 2:
                continue

            price      = round(float(closes[-1]), 2)
            prev_close = round(float(closes[-2]), 2)
            change_pct = round((price - prev_close) / prev_close * 100, 2)

            high_52   = round(float(max(closes)), 2)
            low_52    = round(float(min(closes)), 2)
            vol_today = int(volumes[-1]) if volumes else 0

            hist_prices = [round(float(c), 2) for c in closes[-90:]]
            hist_dates  = [d.strftime("%Y-%m-%d") for d in df.index[-90:]]

            rsi                          = compute_rsi(closes)
            ma20                         = compute_sma(closes, 20)
            ma50                         = compute_sma(closes, 50)
            ma200                        = compute_sma(closes, 200)
            macd_line, signal_line, macd_hist = compute_macd(closes)

            results[sym] = {
                "symbol":      sym,
                "name":        CEDEARS[sym]["name"],
                "sector":      CEDEARS[sym]["sector"],
                "price_usd":   price,
                "prev_close":  prev_close,
                "change_pct":  change_pct,
                "high_52w":    high_52,
                "low_52w":     low_52,
                "volume":      vol_today,
                "rsi":         rsi,
                "ma20":        ma20,
                "ma50":        ma50,
                "ma200":       ma200,
                "macd":        macd_line,
                "macd_signal": signal_line,
                "macd_hist":   macd_hist,
                "hist_prices": hist_prices,
                "hist_dates":  hist_dates,
            }
            print(f"  [OK] {sym}: USD {price:>8.2f}  ({change_pct:+.2f}%)")

        except Exception as e:
            print(f"  [ERR] {sym}: {e}")

    return results


def main():
    daily  = fetch_all(interval="1d")
    weekly = fetch_all(interval="1wk")

    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at_baires": (datetime.utcnow() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M"),
        "tickers":        daily,
        "tickers_weekly": weekly,
    }

    os.makedirs("data", exist_ok=True)
    out_path = "data/market_data.json"
    with open(out_path, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    print(f"\n✓ {len(daily)} tickers diarios y {len(weekly)} semanales guardados en {out_path}")
    print(f"  Actualizado: {output['updated_at_baires']} (hora Buenos Aires)")


if __name__ == "__main__":
    main()

