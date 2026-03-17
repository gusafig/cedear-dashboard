"""
fetch_data.py  —  CEDEAR Dashboard
Descarga datos diarios (3 años) de Yahoo Finance para todos los CEDEARs
negociables en BYMA que cotizan en NYSE / NASDAQ.
Calcula: RSI(14), MACD(12/26/9), MA20/50/200, Bandas de Bollinger(20,2).
Genera: data/market_data.json
"""

import json
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

# ── Universo CEDEAR — NYSE / NASDAQ únicamente ────────────────────────────────
# Fuente: listado oficial BYMA 03/02/2026
# Excluidos: B3, Frankfurt, London SE, OTC (Yahoo Finance no los cubre bien)

CEDEARS = {
    # Tecnología
    "AAPL":  {"name": "Apple",                     "sector": "tech"},
    "MSFT":  {"name": "Microsoft",                 "sector": "tech"},
    "GOOGL": {"name": "Alphabet",                  "sector": "tech"},
    "AMZN":  {"name": "Amazon",                    "sector": "tech"},
    "TSLA":  {"name": "Tesla",                     "sector": "tech"},
    "META":  {"name": "Meta Platforms",            "sector": "tech"},
    "NVDA":  {"name": "NVIDIA",                    "sector": "tech"},
    "NFLX":  {"name": "Netflix",                   "sector": "tech"},
    "ORCL":  {"name": "Oracle",                    "sector": "tech"},
    "CRM":   {"name": "Salesforce",                "sector": "tech"},
    "INTC":  {"name": "Intel",                     "sector": "tech"},
    "AMD":   {"name": "AMD",                       "sector": "tech"},
    "QCOM":  {"name": "Qualcomm",                  "sector": "tech"},
    "ADBE":  {"name": "Adobe",                     "sector": "tech"},
    "PYPL":  {"name": "PayPal",                    "sector": "tech"},
    "UBER":  {"name": "Uber",                      "sector": "tech"},
    "SPOT":  {"name": "Spotify",                   "sector": "tech"},
    "SHOP":  {"name": "Shopify",                   "sector": "tech"},
    "CSCO":  {"name": "Cisco",                     "sector": "tech"},
    "IBM":   {"name": "IBM",                       "sector": "tech"},
    "AMAT":  {"name": "Applied Materials",         "sector": "tech"},
    "ADI":   {"name": "Analog Devices",            "sector": "tech"},
    "LRCX":  {"name": "Lam Research",              "sector": "tech"},
    "MRVL":  {"name": "Marvell Technology",        "sector": "tech"},
    "MU":    {"name": "Micron Technology",         "sector": "tech"},
    "MSTR":  {"name": "MicroStrategy",             "sector": "tech"},
    "NOW":   {"name": "ServiceNow",                "sector": "tech"},
    "TEAM":  {"name": "Atlassian",                 "sector": "tech"},
    "DOCU":  {"name": "DocuSign",                  "sector": "tech"},
    "SNOW":  {"name": "Snowflake",                 "sector": "tech"},
    "PLTR":  {"name": "Palantir",                  "sector": "tech"},
    "PANW":  {"name": "Palo Alto Networks",        "sector": "tech"},
    "COIN":  {"name": "Coinbase",                  "sector": "tech"},
    "ARM":   {"name": "ARM Holdings",              "sector": "tech"},
    "ASML":  {"name": "ASML Holding",              "sector": "tech"},
    "TSM":   {"name": "Taiwan Semiconductor",      "sector": "tech"},
    "AVGO":  {"name": "Broadcom",                  "sector": "tech"},
    "TXN":   {"name": "Texas Instruments",         "sector": "tech"},
    "SWKS":  {"name": "Skyworks Solutions",        "sector": "tech"},
    "ISRG":  {"name": "Intuitive Surgical",        "sector": "tech"},
    "CRWV":  {"name": "CoreWeave",                 "sector": "tech"},
    "ALAB":  {"name": "Astera Labs",               "sector": "tech"},
    "ASTS":  {"name": "AST SpaceMobile",           "sector": "tech"},
    "RKLB":  {"name": "Rocket Lab",                "sector": "tech"},
    "OKLO":  {"name": "Oklo",                      "sector": "tech"},
    "RGTI":  {"name": "Rigetti Computing",         "sector": "tech"},
    "AI":    {"name": "C3.AI",                     "sector": "tech"},
    "PATH":  {"name": "UiPath",                    "sector": "tech"},
    "TWLO":  {"name": "Twilio",                    "sector": "tech"},
    "ZM":    {"name": "Zoom",                      "sector": "tech"},
    "SNAP":  {"name": "Snap",                      "sector": "tech"},
    "PINS":  {"name": "Pinterest",                 "sector": "tech"},
    "RBLX":  {"name": "Roblox",                    "sector": "tech"},
    "ROKU":  {"name": "Roku",                      "sector": "tech"},
    "ETSY":  {"name": "Etsy",                      "sector": "tech"},
    "EBAY":  {"name": "eBay",                      "sector": "tech"},
    "HOOD":  {"name": "Robinhood",                 "sector": "tech"},
    "INFY":  {"name": "Infosys",                   "sector": "tech"},
    "SAP":   {"name": "SAP SE",                    "sector": "tech"},
    "SONY":  {"name": "Sony",                      "sector": "tech"},
    "NTES":  {"name": "NetEase",                   "sector": "tech"},
    "TCOM":  {"name": "Trip.com",                  "sector": "tech"},
    "TEM":   {"name": "Tempus AI",                 "sector": "tech"},
    "GLOB":  {"name": "Globant",                   "sector": "tech"},
    "SATL":  {"name": "Satellogic",                "sector": "tech"},
    "GRMN":  {"name": "Garmin",                    "sector": "tech"},
    "ABNB":  {"name": "Airbnb",                    "sector": "tech"},
    "HPQ":   {"name": "HP Inc",                    "sector": "tech"},
    "ADP":   {"name": "ADP",                       "sector": "tech"},
    # Finanzas
    "JPM":   {"name": "JPMorgan Chase",            "sector": "finance"},
    "GS":    {"name": "Goldman Sachs",             "sector": "finance"},
    "BAC":   {"name": "Bank of America",           "sector": "finance"},
    "C":     {"name": "Citigroup",                 "sector": "finance"},
    "WFC":   {"name": "Wells Fargo",               "sector": "finance"},
    "MS":    {"name": "Morgan Stanley",            "sector": "finance"},
    "BLK":   {"name": "BlackRock",                 "sector": "finance"},
    "AXP":   {"name": "American Express",          "sector": "finance"},
    "V":     {"name": "Visa",                      "sector": "finance"},
    "MA":    {"name": "Mastercard",                "sector": "finance"},
    "SCHW":  {"name": "Charles Schwab",            "sector": "finance"},
    "BX":    {"name": "Blackstone",                "sector": "finance"},
    "BK":    {"name": "BNY Mellon",                "sector": "finance"},
    "USB":   {"name": "U.S. Bancorp",              "sector": "finance"},
    "AIG":   {"name": "AIG",                       "sector": "finance"},
    "SPGI":  {"name": "S&P Global",                "sector": "finance"},
    "MMC":   {"name": "Marsh & McLennan",          "sector": "finance"},
    "NU":    {"name": "Nu Holdings",               "sector": "finance"},
    "ITUB":  {"name": "Itaú Unibanco",             "sector": "finance"},
    "BBD":   {"name": "Banco Bradesco",            "sector": "finance"},
    "BSBR":  {"name": "Santander Brasil",          "sector": "finance"},
    "SAN":   {"name": "Banco Santander",           "sector": "finance"},
    "ING":   {"name": "ING Groep",                 "sector": "finance"},
    "HSBC":  {"name": "HSBC Holdings",             "sector": "finance"},
    "IBN":   {"name": "ICICI Bank",                "sector": "finance"},
    "HDB":   {"name": "HDFC Bank",                 "sector": "finance"},
    "KB":    {"name": "KB Financial",              "sector": "finance"},
    "PAGS":  {"name": "PagSeguro",                 "sector": "finance"},
    "XP":    {"name": "XP Inc",                    "sector": "finance"},
    # Energía
    "XOM":   {"name": "ExxonMobil",                "sector": "energy"},
    "CVX":   {"name": "Chevron",                   "sector": "energy"},
    "COP":   {"name": "ConocoPhillips",            "sector": "energy"},
    "SLB":   {"name": "Schlumberger",              "sector": "energy"},
    "BP":    {"name": "BP",                        "sector": "energy"},
    "HAL":   {"name": "Halliburton",               "sector": "energy"},
    "BKR":   {"name": "Baker Hughes",              "sector": "energy"},
    "OXY":   {"name": "Occidental Petroleum",      "sector": "energy"},
    "PSX":   {"name": "Phillips 66",               "sector": "energy"},
    "TTE":   {"name": "TotalEnergies",             "sector": "energy"},
    "EQNR":  {"name": "Equinor",                   "sector": "energy"},
    "PBR":   {"name": "Petrobras",                 "sector": "energy"},
    "VIST":  {"name": "Vista Energy",              "sector": "energy"},
    "VST":   {"name": "Vistra",                    "sector": "energy"},
    "CEG":   {"name": "Constellation Energy",      "sector": "energy"},
    "USO":   {"name": "US Oil Fund",               "sector": "energy"},
    # Consumo
    "WMT":   {"name": "Walmart",                   "sector": "consumer"},
    "KO":    {"name": "Coca-Cola",                 "sector": "consumer"},
    "PG":    {"name": "Procter & Gamble",          "sector": "consumer"},
    "MCD":   {"name": "McDonald's",                "sector": "consumer"},
    "NKE":   {"name": "Nike",                      "sector": "consumer"},
    "SBUX":  {"name": "Starbucks",                 "sector": "consumer"},
    "DIS":   {"name": "Disney",                    "sector": "consumer"},
    "COST":  {"name": "Costco",                    "sector": "consumer"},
    "TGT":   {"name": "Target",                    "sector": "consumer"},
    "HD":    {"name": "Home Depot",                "sector": "consumer"},
    "MDLZ":  {"name": "Mondelez",                  "sector": "consumer"},
    "PEP":   {"name": "PepsiCo",                   "sector": "consumer"},
    "PM":    {"name": "Philip Morris",             "sector": "consumer"},
    "MO":    {"name": "Altria",                    "sector": "consumer"},
    "CL":    {"name": "Colgate-Palmolive",         "sector": "consumer"},
    "KMB":   {"name": "Kimberly-Clark",            "sector": "consumer"},
    "HSY":   {"name": "Hershey",                   "sector": "consumer"},
    "LVS":   {"name": "Las Vegas Sands",           "sector": "consumer"},
    "CCL":   {"name": "Carnival",                  "sector": "consumer"},
    "BKNG":  {"name": "Booking Holdings",          "sector": "consumer"},
    "RACE":  {"name": "Ferrari",                   "sector": "consumer"},
    "TM":    {"name": "Toyota",                    "sector": "consumer"},
    "HMC":   {"name": "Honda",                     "sector": "consumer"},
    "GM":    {"name": "General Motors",            "sector": "consumer"},
    "F":     {"name": "Ford",                      "sector": "consumer"},
    "ROST":  {"name": "Ross Stores",               "sector": "consumer"},
    "TJX":   {"name": "TJX Companies",             "sector": "consumer"},
    "ARCO":  {"name": "Arcos Dorados",             "sector": "consumer"},
    "AMX":   {"name": "America Movil",             "sector": "consumer"},
    # Salud
    "JNJ":   {"name": "Johnson & Johnson",         "sector": "health"},
    "PFE":   {"name": "Pfizer",                    "sector": "health"},
    "MRK":   {"name": "Merck",                     "sector": "health"},
    "ABBV":  {"name": "AbbVie",                    "sector": "health"},
    "UNH":   {"name": "UnitedHealth",              "sector": "health"},
    "LLY":   {"name": "Eli Lilly",                 "sector": "health"},
    "AMGN":  {"name": "Amgen",                     "sector": "health"},
    "BIIB":  {"name": "Biogen",                    "sector": "health"},
    "GILD":  {"name": "Gilead Sciences",           "sector": "health"},
    "BMY":   {"name": "Bristol-Myers Squibb",      "sector": "health"},
    "MDT":   {"name": "Medtronic",                 "sector": "health"},
    "DHR":   {"name": "Danaher",                   "sector": "health"},
    "TMO":   {"name": "Thermo Fisher",             "sector": "health"},
    "ABT":   {"name": "Abbott Labs",               "sector": "health"},
    "AZN":   {"name": "AstraZeneca",               "sector": "health"},
    "GSK":   {"name": "GSK",                       "sector": "health"},
    "NVS":   {"name": "Novartis",                  "sector": "health"},
    "MRNA":  {"name": "Moderna",                   "sector": "health"},
    "VRTX":  {"name": "Vertex Pharmaceuticals",    "sector": "health"},
    "CVS":   {"name": "CVS Health",                "sector": "health"},
    "CAH":   {"name": "Cardinal Health",           "sector": "health"},
    # Industrial / Materiales
    "CAT":   {"name": "Caterpillar",               "sector": "industrial"},
    "BA":    {"name": "Boeing",                    "sector": "industrial"},
    "GE":    {"name": "GE Aerospace",              "sector": "industrial"},
    "MMM":   {"name": "3M",                        "sector": "industrial"},
    "HON":   {"name": "Honeywell",                 "sector": "industrial"},
    "RTX":   {"name": "Raytheon Technologies",     "sector": "industrial"},
    "LMT":   {"name": "Lockheed Martin",           "sector": "industrial"},
    "DE":    {"name": "Deere & Co.",               "sector": "industrial"},
    "UNP":   {"name": "Union Pacific",             "sector": "industrial"},
    "FDX":   {"name": "FedEx",                     "sector": "industrial"},
    "MSI":   {"name": "Motorola Solutions",        "sector": "industrial"},
    "JCI":   {"name": "Johnson Controls",          "sector": "industrial"},
    "DOW":   {"name": "Dow Inc",                   "sector": "industrial"},
    "DD":    {"name": "DuPont",                    "sector": "industrial"},
    "IP":    {"name": "International Paper",       "sector": "industrial"},
    "AVY":   {"name": "Avery Dennison",            "sector": "industrial"},
    "ECL":   {"name": "Ecolab",                    "sector": "industrial"},
    "GLW":   {"name": "Corning",                   "sector": "industrial"},
    "ACN":   {"name": "Accenture",                 "sector": "industrial"},
    "EFX":   {"name": "Equifax",                   "sector": "industrial"},
    "IFF":   {"name": "Intl Flavors",              "sector": "industrial"},
    "HOG":   {"name": "Harley-Davidson",           "sector": "industrial"},
    "DAL":   {"name": "Delta Air Lines",           "sector": "industrial"},
    "AAL":   {"name": "American Airlines",         "sector": "industrial"},
    "UAL":   {"name": "United Airlines",           "sector": "industrial"},
    "BNG":   {"name": "Bunge",                     "sector": "industrial"},
    # Minería / Metales
    "NEM":   {"name": "Newmont",                   "sector": "mining"},
    "AEM":   {"name": "Agnico Eagle",              "sector": "mining"},
    "KGC":   {"name": "Kinross Gold",              "sector": "mining"},
    "GFI":   {"name": "Gold Fields",               "sector": "mining"},
    "HMY":   {"name": "Harmony Gold",              "sector": "mining"},
    "PAAS":  {"name": "Pan American Silver",       "sector": "mining"},
    "FCX":   {"name": "Freeport-McMoRan",          "sector": "mining"},
    "BHP":   {"name": "BHP Group",                 "sector": "mining"},
    "RIO":   {"name": "Rio Tinto",                 "sector": "mining"},
    "VALE":  {"name": "Vale",                      "sector": "mining"},
    "SCCO":  {"name": "Southern Copper",           "sector": "mining"},
    "MUX":   {"name": "McEwen Mining",             "sector": "mining"},
    "HL":    {"name": "Hecla Mining",              "sector": "mining"},
    "CDE":   {"name": "Coeur Mining",              "sector": "mining"},
    "LAC":   {"name": "Lithium Americas",          "sector": "mining"},
    "NXE":   {"name": "NexGen Energy",             "sector": "mining"},
    # Brasil ADR
    "ABEV":  {"name": "Ambev",                     "sector": "brasil"},
    "ERJ":   {"name": "Embraer",                   "sector": "brasil"},
    "GGB":   {"name": "Gerdau",                    "sector": "brasil"},
    "SID":   {"name": "CSN",                       "sector": "brasil"},
    "BAK":   {"name": "Braskem",                   "sector": "brasil"},
    "BRFS":  {"name": "BRF SA",                    "sector": "brasil"},
    "SUZ":   {"name": "Suzano",                    "sector": "brasil"},
    "EBR":   {"name": "Eletrobras",                "sector": "brasil"},
    "SBS":   {"name": "Sabesp",                    "sector": "brasil"},
    "ELP":   {"name": "Copel",                     "sector": "brasil"},
    "UGP":   {"name": "Ultrapar",                  "sector": "brasil"},
    "STNE":  {"name": "StoneCo",                   "sector": "brasil"},
    "NTCO":  {"name": "Natura & Co",               "sector": "brasil"},
    "VIV":   {"name": "Telefônica Brasil",         "sector": "brasil"},
    "TIMB":  {"name": "TIM Brasil",                "sector": "brasil"},
    "MELI":  {"name": "MercadoLibre",              "sector": "brasil"},
    "ADGO":  {"name": "Adecoagro",                 "sector": "brasil"},
    # China ADR
    "BABA":  {"name": "Alibaba",                   "sector": "china"},
    "BIDU":  {"name": "Baidu",                     "sector": "china"},
    "JD":    {"name": "JD.com",                    "sector": "china"},
    "NIO":   {"name": "NIO",                       "sector": "china"},
    "PDD":   {"name": "PDD Holdings (Temu)",       "sector": "china"},
    "XPEV":  {"name": "XPeng",                     "sector": "china"},
    "LFC":   {"name": "China Life Insurance",      "sector": "china"},
    "SNP":   {"name": "Sinopec",                   "sector": "china"},
    "SE":    {"name": "Sea Ltd",                   "sector": "china"},
    # México ADR
    "CX":    {"name": "Cemex",                     "sector": "mexico"},
    "FMX":   {"name": "FEMSA",                     "sector": "mexico"},
    "TV":    {"name": "Grupo Televisa",            "sector": "mexico"},
    "PAC":   {"name": "GAP Aeropuertos Pacífico",  "sector": "mexico"},
    "ASR":   {"name": "ASUR Aeropuertos Sureste",  "sector": "mexico"},
    # ETFs
    "SPY":   {"name": "SPDR S&P 500",              "sector": "etf"},
    "QQQ":   {"name": "Invesco QQQ (NASDAQ 100)",  "sector": "etf"},
    "DIA":   {"name": "SPDR Dow Jones",            "sector": "etf"},
    "IVV":   {"name": "iShares S&P 500",           "sector": "etf"},
    "IWM":   {"name": "iShares Russell 2000",      "sector": "etf"},
    "EEM":   {"name": "iShares MSCI EM",           "sector": "etf"},
    "IEMG":  {"name": "iShares Core MSCI EM",      "sector": "etf"},
    "EWZ":   {"name": "iShares MSCI Brazil",       "sector": "etf"},
    "FXI":   {"name": "iShares China Large-Cap",   "sector": "etf"},
    "EFA":   {"name": "iShares MSCI EAFE",         "sector": "etf"},
    "EWJ":   {"name": "iShares MSCI Japan",        "sector": "etf"},
    "ACWI":  {"name": "iShares MSCI ACWI",         "sector": "etf"},
    "ILF":   {"name": "iShares Latin America 40",  "sector": "etf"},
    "GLD":   {"name": "SPDR Gold Trust",           "sector": "etf"},
    "SLV":   {"name": "iShares Silver Trust",      "sector": "etf"},
    "GDX":   {"name": "VanEck Gold Miners",        "sector": "etf"},
    "COPX":  {"name": "Global X Copper Miners",    "sector": "etf"},
    "URA":   {"name": "Global X Uranium",          "sector": "etf"},
    "SMH":   {"name": "VanEck Semiconductor",      "sector": "etf"},
    "ARKK":  {"name": "ARK Innovation",            "sector": "etf"},
    "XLE":   {"name": "Energy Select SPDR",        "sector": "etf"},
    "XLF":   {"name": "Financial Select SPDR",     "sector": "etf"},
    "XLK":   {"name": "Technology Select SPDR",    "sector": "etf"},
    "XLV":   {"name": "Health Care Select SPDR",   "sector": "etf"},
    "XLI":   {"name": "Industrial Select SPDR",    "sector": "etf"},
    "XLB":   {"name": "Materials Select SPDR",     "sector": "etf"},
    "XLC":   {"name": "Comm Services SPDR",        "sector": "etf"},
    "XLY":   {"name": "Consumer Discret. SPDR",    "sector": "etf"},
    "XLP":   {"name": "Consumer Staples SPDR",     "sector": "etf"},
    "XLU":   {"name": "Utilities Select SPDR",     "sector": "etf"},
    "XLRE":  {"name": "Real Estate SPDR",          "sector": "etf"},
    "IBB":   {"name": "iShares NASDAQ Biotech",    "sector": "etf"},
    "VIG":   {"name": "Vanguard Dividend Apprec.", "sector": "etf"},
    "VEA":   {"name": "Vanguard FTSE Dev. Markets","sector": "etf"},
    "IBIT":  {"name": "iShares Bitcoin Trust",     "sector": "etf"},
    "ETHA":  {"name": "iShares Ethereum ETF",      "sector": "etf"},
    "TQQQ":  {"name": "ProShares UltraPro QQQ",    "sector": "etf"},
    "SPXL":  {"name": "Direxion S&P 500 Bull 3x",  "sector": "etf"},
    "SH":    {"name": "ProShares Short S&P500",    "sector": "etf"},
    "PSQ":   {"name": "ProShares Short QQQ",       "sector": "etf"},
    "VXX":   {"name": "iPath S&P 500 VIX",         "sector": "etf"},
    "ITA":   {"name": "iShares Aerospace & Defense","sector": "etf"},
    # Crypto mining
    "RIOT":  {"name": "Riot Platforms",            "sector": "crypto"},
    "BITF":  {"name": "Bitfarms",                  "sector": "crypto"},
    "HUT":   {"name": "Hut 8 Mining",              "sector": "crypto"},
    "IREN":  {"name": "Iren Ltd",                  "sector": "crypto"},
    "MARA":  {"name": "Marathon Digital",          "sector": "crypto"},
}

TICKERS = sorted(CEDEARS.keys())


# ── Indicadores técnicos ──────────────────────────────────────────────────────

def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0.0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0.0 for d in deltas[-period:]]
    ag = sum(gains) / period
    al = sum(losses) / period
    if al == 0:
        return 100.0
    return round(100 - (100 / (1 + ag / al)), 2)


def compute_ema(closes, period):
    if len(closes) < period:
        return None
    k   = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for p in closes[period:]:
        ema = p * k + ema * (1 - k)
    return round(ema, 4)


def compute_macd(closes):
    if len(closes) < 26:
        return None, None, None
    k12, k26 = 2/13, 2/27
    e12 = sum(closes[:12]) / 12
    e26 = sum(closes[:26]) / 26
    macd_series = []
    for p in closes[12:]:
        e12 = p * k12 + e12 * (1 - k12)
    for p in closes[26:]:
        e26 = p * k26 + e26 * (1 - k26)
    # Recalcular correctamente
    e12 = sum(closes[:12]) / 12
    e26 = sum(closes[:26]) / 26
    for p in closes[26:]:
        e12 = p * k12 + e12 * (1 - k12)
        e26 = p * k26 + e26 * (1 - k26)
        macd_series.append(e12 - e26)
    if len(macd_series) < 9:
        return round(macd_series[-1], 4), None, None
    signal = compute_ema(macd_series, 9)
    macd_val = round(macd_series[-1], 4)
    hist = round(macd_val - signal, 4) if signal else None
    return macd_val, signal, hist


def compute_sma(closes, period):
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 2)


def compute_bollinger(closes, period=20, num_std=2):
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    mid    = sum(window) / period
    std    = (sum((x - mid)**2 for x in window) / period) ** 0.5
    return round(mid, 2), round(mid + num_std * std, 2), round(mid - num_std * std, 2)


# ── Descarga robusta ticker a ticker ─────────────────────────────────────────

def download_ticker(sym, start_str, end_str, retries=3):
    for attempt in range(retries):
        try:
            df = yf.download(
                sym,
                start=start_str,
                end=end_str,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df is not None and not df.empty:
                # Aplanar MultiIndex si existe
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.dropna(subset=["Close"])
                if len(df) > 10:
                    return df
            print(f"    [RETRY {attempt+1}] {sym}: datos vacíos")
        except Exception as e:
            print(f"    [RETRY {attempt+1}] {sym}: {e}")
        if attempt < retries - 1:
            time.sleep(10)
    return None


# ── Proceso principal ─────────────────────────────────────────────────────────

def fetch_all():
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=365 * 3)
    start_str  = start_date.strftime("%Y-%m-%d")
    end_str    = end_date.strftime("%Y-%m-%d")

    print(f"[{datetime.now().isoformat()}]")
    print(f"Descargando {len(TICKERS)} tickers | {start_str} → {end_str}")
    print("-" * 60)

    results = {}
    ok = 0
    skip = 0

    for sym in TICKERS:
        df = download_ticker(sym, start_str, end_str)

        if df is None:
            print(f"  [SKIP] {sym}")
            skip += 1
            continue

        try:
            closes  = [float(x) for x in df["Close"].tolist()]
            volumes = [float(x) for x in df["Volume"].tolist()]
            highs   = [float(x) for x in df["High"].tolist()]
            lows    = [float(x) for x in df["Low"].tolist()]

            price      = round(closes[-1], 2)
            prev_close = round(closes[-2], 2)
            change_pct = round((price - prev_close) / prev_close * 100, 2)
            high_day   = round(highs[-1], 2)
            low_day    = round(lows[-1], 2)
            vol_today  = int(volumes[-1]) if volumes else 0

            recent_252 = closes[-252:] if len(closes) >= 252 else closes
            high_52w   = round(max(recent_252), 2)
            low_52w    = round(min(recent_252), 2)

            # Gráfico: últimos 90 días
            hist_prices = [round(c, 2) for c in closes[-90:]]
            hist_dates  = [d.strftime("%Y-%m-%d") for d in df.index[-90:]]

            # Indicadores
            rsi                       = compute_rsi(closes)
            ma20                      = compute_sma(closes, 20)
            ma50                      = compute_sma(closes, 50)
            ma200                     = compute_sma(closes, 200)
            macd_val, macd_sig, macd_hist = compute_macd(closes)
            bb_mid, bb_upper, bb_lower    = compute_bollinger(closes)

            results[sym] = {
                "symbol":      sym,
                "name":        CEDEARS[sym]["name"],
                "sector":      CEDEARS[sym]["sector"],
                "price_usd":   price,
                "prev_close":  prev_close,
                "change_pct":  change_pct,
                "high_day":    high_day,
                "low_day":     low_day,
                "high_52w":    high_52w,
                "low_52w":     low_52w,
                "volume":      vol_today,
                "rsi":         rsi,
                "ma20":        ma20,
                "ma50":        ma50,
                "ma200":       ma200,
                "macd":        macd_val,
                "macd_signal": macd_sig,
                "macd_hist":   macd_hist,
                "bb_mid":      bb_mid,
                "bb_upper":    bb_upper,
                "bb_lower":    bb_lower,
                "hist_prices": hist_prices,
                "hist_dates":  hist_dates,
            }
            ok += 1
            print(f"  [OK] {sym:6s}  USD {price:>9.2f}  ({change_pct:+.2f}%)  RSI {rsi}")

        except Exception as e:
            print(f"  [ERR] {sym}: {e}")
            skip += 1

        time.sleep(0.5)   # pausa entre tickers para no saturar la API

    print("-" * 60)
    print(f"OK: {ok}  |  Skip/Error: {skip}  |  Total: {len(TICKERS)}")
    return results


def main():
    data = fetch_all()

    output = {
        "updated_at":         datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at_baires":  (datetime.utcnow() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M"),
        "total":              len(data),
        "tickers":            data,
    }

    os.makedirs("data", exist_ok=True)
    path = "data/market_data.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    print(f"\n✓ {len(data)} tickers → {path}")
    print(f"  Actualizado: {output['updated_at_baires']} (hora Buenos Aires)")


if __name__ == "__main__":
    main()

