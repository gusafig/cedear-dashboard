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
# Fuente: listado oficial BYMA, actualizado al 02/09/2026
# Incluye NYSE, NASDAQ y sus variantes (NYSE Arca, NYSE American, NASDAQ GS/GM/CM).
# Excluidos: B3, Frankfurt, London SE, Xetra, Bovespa, OTC puro (Yahoo Finance
# no los cubre bien) y ADRs deslistados/discontinuados (ver detalle más abajo).

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
    # ──────────────────────────────────────────────────────────────
    # Nuevos CEDEARs incorporados — listado oficial BYMA (actualizado 02/09/2026)
    # Se agregan las acciones/ETFs del listado BYMA que cotizan en NYSE /
    # NASDAQ (incl. NYSE Arca, NYSE American, NASDAQ GS/GM/CM) y que no
    # estaban en el universo. Cuando el código de BYMA difiere del ticker
    # real en Yahoo Finance se usa el ticker real (aclarado en el comentario).
    #
    # Quedan afuera del listado BYMA por estar deslistados/discontinuados:
    # AABA (Altaba), CS (Credit Suisse), SI (Silvergate Bancorp),
    # AUY (Yamana Gold), TWTR (Twitter), WBA (Walgreens, privada desde 2025),
    # MBT (Mobile TeleSystems, sancionada), TTM (Tata Motors, deslistó su ADR
    # en 2023), PTR (PetroChina) y AOCA (Aluminum Corp of China/Chalco).
    # También quedan afuera por ser el mismo ticker ya presente con otro
    # código BYMA: BA.C (=BAC), DISN (=DIS), KEEL (=BITF).
    # ──────────────────────────────────────────────────────────────
    # Tecnología
    "ANET":  {"name": "Arista Networks",                           "sector": "tech"},
    "CRWD":  {"name": "CrowdStrike",                               "sector": "tech"},
    "DELL":  {"name": "Dell Technologies",                         "sector": "tech"},
    "EA":    {"name": "Electronic Arts",                           "sector": "tech"},
    "ERIC":  {"name": "Ericsson",                                  "sector": "tech"},
    "KLAC":  {"name": "KLA Corp",                                  "sector": "tech"},
    "NOK":   {"name": "Nokia",                                     "sector": "tech"},  # BYMA usa 'NOKA'; ticker real Yahoo es 'NOK'
    "CAJ":   {"name": "Canon",                                     "sector": "tech"},
    "SPCX":  {"name": "SpaceX (Space Exploration Technologies)",   "sector": "tech"},  # Debutó en NASDAQ en 2026
    "NBIS":  {"name": "Nebius Group",                              "sector": "tech"},
    "SNDK":  {"name": "SanDisk",                                   "sector": "tech"},  # Spin-off de Western Digital (2025)
    "WDC":   {"name": "Western Digital",                           "sector": "tech"},
    "FI":    {"name": "Fiserv",                                    "sector": "tech"},  # BYMA usa 'FISV'; cambió su ticker a 'FI' en NYSE en 2023
    "JMIA":  {"name": "Jumia Technologies",                        "sector": "tech"},
    "JOYY":  {"name": "JOYY Inc",                                  "sector": "tech"},
    "SDA":   {"name": "SunCar Technology Group",                   "sector": "tech"},
    "UPST":  {"name": "Upstart Holdings",                          "sector": "tech"},
    "YELP":  {"name": "Yelp",                                      "sector": "tech"},
    "TRIP":  {"name": "Tripadvisor",                               "sector": "tech"},
    "SPCE":  {"name": "Virgin Galactic",                           "sector": "tech"},
    "ONDS":  {"name": "Ondas Holdings",                            "sector": "tech"},
    "BB":    {"name": "BlackBerry",                                "sector": "tech"},
    "CLS":   {"name": "Celestica",                                 "sector": "tech"},
    "XYZ":   {"name": "Block (ex-Square)",                         "sector": "tech"},
    # Finanzas
    "IBKR":  {"name": "Interactive Brokers",                       "sector": "finance"},
    "AEG":   {"name": "Aegon",                                     "sector": "finance"},
    "BCS":   {"name": "Barclays",                                  "sector": "finance"},
    "BBVA":  {"name": "BBVA (Banco Bilbao Vizcaya Argentaria)",    "sector": "finance"},  # BYMA usa 'BBV'; ticker real Yahoo es 'BBVA'
    "LYG":   {"name": "Lloyds Banking Group",                      "sector": "finance"},
    "MFG":   {"name": "Mizuho Financial Group",                    "sector": "finance"},
    "MUFG":  {"name": "Mitsubishi UFJ Financial Group",            "sector": "finance"},
    "NMR":   {"name": "Nomura Holdings",                           "sector": "finance"},
    "BRK-B": {"name": "Berkshire Hathaway (Cl. B)",                "sector": "finance"},  # BYMA usa 'BRKB'; en Yahoo se escribe 'BRK-B'
    "O":     {"name": "Realty Income",                             "sector": "finance"},  # REIT
    "PLD":   {"name": "Prologis",                                  "sector": "finance"},  # REIT
    "WELL":  {"name": "Welltower",                                 "sector": "finance"},  # REIT
    # Energía
    "SHEL":  {"name": "Shell",                                     "sector": "energy"},
    "NEE":   {"name": "NextEra Energy",                            "sector": "energy"},
    "NGG":   {"name": "National Grid",                             "sector": "energy"},
    "KEP":   {"name": "Korea Electric Power",                      "sector": "energy"},
    "FSLR":  {"name": "First Solar",                               "sector": "energy"},
    "TLN":   {"name": "Talen Energy",                              "sector": "energy"},
    "GPRK":  {"name": "GeoPark",                                   "sector": "energy"},
    "GLNG":  {"name": "Golar LNG",                                 "sector": "energy"},
    "E":     {"name": "Eni SpA",                                   "sector": "energy"},
    # Consumo
    "DEO":   {"name": "Diageo",                                    "sector": "consumer"},
    "UL":    {"name": "Unilever",                                  "sector": "consumer"},
    "ORLY":  {"name": "O'Reilly Automotive",                       "sector": "consumer"},
    "DECK":  {"name": "Deckers Outdoor (HOKA/UGG)",                "sector": "consumer"},
    "ANF":   {"name": "Abercrombie & Fitch",                       "sector": "consumer"},
    "STLA":  {"name": "Stellantis",                                "sector": "consumer"},
    "SYY":   {"name": "Sysco",                                     "sector": "consumer"},
    "T":     {"name": "AT&T",                                      "sector": "consumer"},
    "VZ":    {"name": "Verizon Communications",                    "sector": "consumer"},
    "TMUS":  {"name": "T-Mobile US",                               "sector": "consumer"},
    "ORAN":  {"name": "Orange S.A.",                               "sector": "consumer"},
    "HIMS":  {"name": "Hims & Hers Health",                        "sector": "consumer"},  # También podría ir en salud
    "URBN":  {"name": "Urban Outfitters",                          "sector": "consumer"},
    "VOD":   {"name": "Vodafone Group",                            "sector": "consumer"},
    "AAP":   {"name": "Advance Auto Parts",                        "sector": "consumer"},
    "CAR":   {"name": "Avis Budget Group",                         "sector": "consumer"},
    # Salud
    "NVO":   {"name": "Novo Nordisk",                              "sector": "health"},
    "PHG":   {"name": "Koninklijke Philips",                       "sector": "health"},
    "NTRA":  {"name": "Natera",                                    "sector": "health"},
    # Industrial / Materiales
    "LIN":   {"name": "Linde",                                     "sector": "industrial"},
    "SHW":   {"name": "Sherwin-Williams",                          "sector": "industrial"},
    "GT":    {"name": "Goodyear Tire & Rubber",                    "sector": "industrial"},
    "HWM":   {"name": "Howmet Aerospace",                          "sector": "industrial"},
    "GEV":   {"name": "GE Vernova",                                "sector": "industrial"},
    "NUE":   {"name": "Nucor",                                     "sector": "industrial"},
    "PKX":   {"name": "POSCO Holdings",                            "sector": "industrial"},  # BYMA usa 'PKS'; ticker real Yahoo es 'PKX'
    "CAAP":  {"name": "Corporación América Airports",              "sector": "industrial"},  # Empresa argentina
    "TRV":   {"name": "The Travelers Companies",                   "sector": "industrial"},  # BYMA usa 'TRVV'; ticker real Yahoo es 'TRV'
    "XRX":   {"name": "Xerox Holding",                             "sector": "industrial"},  # BYMA usa 'XROX'; ticker real Yahoo es 'XRX'
    "PBI":   {"name": "Pitney Bowes",                              "sector": "industrial"},
    "PCAR":  {"name": "Paccar",                                    "sector": "industrial"},
    "SNA":   {"name": "Snap-on",                                   "sector": "industrial"},
    "PSO":   {"name": "Pearson",                                   "sector": "industrial"},
    "SHPW":  {"name": "Shapeways Holdings",                        "sector": "industrial"},
    # Minería / Metales
    "CCJ":   {"name": "Cameco",                                    "sector": "mining"},
    "MOS":   {"name": "The Mosaic Co",                             "sector": "mining"},
    "MP":    {"name": "MP Materials",                              "sector": "mining"},
    "LAAC":  {"name": "Lithium Americas (Argentina) Corp",         "sector": "mining"},  # BYMA usa 'LAR'; ticker real Yahoo es 'LAAC'
    "B":     {"name": "Barrick Mining Corp (ex-Barrick Gold)",     "sector": "mining"},  # Cambió de ticker GOLD→B en mayo 2025
    "NG":    {"name": "Novagold Resources",                        "sector": "mining"},
    # Brasil / LatAm
    "BIOX":  {"name": "Bioceres Crop Solutions",                   "sector": "brasil"},  # Empresa argentina (agtech)
    "TEN":   {"name": "Tenaris",                                   "sector": "brasil"},  # Grupo Techint, Argentina/Luxemburgo
    "AKO.B": {"name": "Embotelladora Andina (Coca-Cola Andina)",   "sector": "brasil"},  # LatAm - Chile
    "LND":   {"name": "Brasilagro",                                "sector": "brasil"},
    "TX":    {"name": "Ternium",                                   "sector": "brasil"},  # BYMA usa 'TXR'; ticker real Yahoo es 'TX' (grupo Techint)
    # México
    "KOF":   {"name": "Coca-Cola FEMSA",                           "sector": "mexico"},  # BYMA usa 'KOFM'; ticker real Yahoo es 'KOF'
    # China
    "WBO":   {"name": "Weibo",                                     "sector": "china"},
    # ETFs
    "CIBR":  {"name": "First Trust NASDAQ Cybersecurity ETF",      "sector": "etf"},
    "ESGU":  {"name": "iShares ESG Aware MSCI USA ETF",            "sector": "etf"},
    "EWY":   {"name": "iShares MSCI South Korea ETF",              "sector": "etf"},
    "ICLN":  {"name": "iShares Global Clean Energy ETF",           "sector": "etf"},
    "IEUR":  {"name": "iShares Core MSCI Europe ETF",              "sector": "etf"},
    "IJH":   {"name": "iShares Core S&P Mid-Cap ETF",              "sector": "etf"},
    "IVE":   {"name": "iShares S&P 500 Value ETF",                 "sector": "etf"},
    "IVW":   {"name": "iShares S&P 500 Growth ETF",                "sector": "etf"},
    "RSP":   {"name": "Invesco S&P 500 Equal Weight ETF",          "sector": "etf"},
    "SPHQ":  {"name": "Invesco S&P 500 Quality ETF",               "sector": "etf"},
    "XME":   {"name": "SPDR S&P Metals & Mining ETF",              "sector": "etf"},
    # Crypto mining
    "BMNR":  {"name": "Bitmine Immersion Technologies",            "sector": "crypto"},
}

TICKERS = sorted(CEDEARS.keys())


# ── Indicadores técnicos ──────────────────────────────────────────────────────

def compute_rsi(closes, period=14):
    """RSI con suavizado de Wilder (SMMA), estándar de TradingView y plataformas financieras."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    # Seed: promedio simple de los primeros 'period' valores
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Suavizado de Wilder sobre el resto del historial
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


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


def compute_stochastic(highs, lows, closes, k_period=14, d_period=3):
    """Oscilador estocástico lento. %K = posición del cierre dentro del rango
    de las últimas k_period velas; %D = SMA(%K, d_period)."""
    if len(closes) < k_period + d_period - 1:
        return None, None
    k_values = []
    for i in range(len(closes) - d_period, len(closes)):
        window_high = max(highs[i - k_period + 1: i + 1])
        window_low  = min(lows[i - k_period + 1: i + 1])
        if window_high == window_low:
            k_values.append(50.0)
        else:
            k_values.append(100 * (closes[i] - window_low) / (window_high - window_low))
    k_now = round(k_values[-1], 2)
    d_now = round(sum(k_values) / len(k_values), 2)
    return k_now, d_now


def compute_roc(closes, period=12):
    """Rate of Change: variación % del precio respecto a 'period' velas atrás."""
    if len(closes) < period + 1:
        return None
    prev = closes[-period - 1]
    if prev == 0:
        return None
    return round((closes[-1] - prev) / prev * 100, 2)


def compute_vol_rel(volumes, period=20):
    """Volumen de hoy / promedio de volumen de los 'period' días previos (sin incluir hoy)."""
    if len(volumes) < period + 1:
        return None
    avg = sum(volumes[-period - 1: -1]) / period
    if avg == 0:
        return None
    return round(volumes[-1] / avg, 2)


def compute_adx(highs, lows, closes, period=14):
    """ADX/DMI con suavizado de Wilder. Retorna (adx, pdi, ndi)."""
    if len(closes) < period * 2 + 1:
        return None, None, None

    tr_list, pdm_list, ndm_list = [], [], []
    for i in range(1, len(closes)):
        high, low         = highs[i], lows[i]
        prev_high, prev_low, prev_close = highs[i-1], lows[i-1], closes[i-1]
        tr  = max(high - low, abs(high - prev_close), abs(low - prev_close))
        pdm = (high - prev_high) if (high - prev_high) > (prev_low - low) and (high - prev_high) > 0 else 0
        ndm = (prev_low - low)   if (prev_low - low) > (high - prev_high) and (prev_low - low) > 0 else 0
        tr_list.append(tr)
        pdm_list.append(pdm)
        ndm_list.append(ndm)

    def wilder_smooth(data, p):
        s = sum(data[:p])
        result = [s]
        for v in data[p:]:
            s = s - (s / p) + v
            result.append(s)
        return result

    atr_s = wilder_smooth(tr_list,  period)
    pdm_s = wilder_smooth(pdm_list, period)
    ndm_s = wilder_smooth(ndm_list, period)

    pdi_list, ndi_list, dx_list = [], [], []
    for i in range(len(atr_s)):
        pdi = 100 * pdm_s[i] / atr_s[i] if atr_s[i] != 0 else 0
        ndi = 100 * ndm_s[i] / atr_s[i] if atr_s[i] != 0 else 0
        dx  = 100 * abs(pdi - ndi) / (pdi + ndi) if (pdi + ndi) != 0 else 0
        pdi_list.append(pdi)
        ndi_list.append(ndi)
        dx_list.append(dx)

    if len(dx_list) < period:
        return None, round(pdi_list[-1], 2), round(ndi_list[-1], 2)

    # ADX: a diferencia de TR/PDM/NDM (que se acumulan como suma cruda porque
    # su cociente cancela el factor de escala), el DX ya está expresado en
    # porcentaje (0-100). Acumularlo con wilder_smooth() lo trataría como una
    # suma y lo infla muy por encima de 100 — acá se promedia correctamente.
    adx = sum(dx_list[:period]) / period
    for dx in dx_list[period:]:
        adx = (adx * (period - 1) + dx) / period

    return round(adx, 2), round(pdi_list[-1], 2), round(ndi_list[-1], 2)


def compute_obv(closes, volumes, lookback=20):
    """
    On-Balance Volume + señal de confirmación/divergencia contra el precio.
    Retorna (obv, obv_signal) donde obv_signal es uno de:
    'confirma_suba', 'confirma_baja', 'divergencia_alcista', 'divergencia_bajista', 'neutral'.
    """
    if len(closes) < 2 or len(volumes) != len(closes):
        return None, None

    obv_series = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv_series.append(obv_series[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            obv_series.append(obv_series[-1] - volumes[i])
        else:
            obv_series.append(obv_series[-1])

    obv = obv_series[-1]
    if len(obv_series) <= lookback:
        return round(obv, 0), None

    obv_trend   = obv_series[-1] - obv_series[-1 - lookback]
    price_trend = closes[-1] - closes[-1 - lookback]

    if obv_trend > 0 and price_trend > 0:
        signal = "confirma_suba"
    elif obv_trend < 0 and price_trend < 0:
        signal = "confirma_baja"
    elif obv_trend <= 0 and price_trend > 0:
        signal = "divergencia_bajista"
    elif obv_trend >= 0 and price_trend < 0:
        signal = "divergencia_alcista"
    else:
        signal = "neutral"

    return round(obv, 0), signal


def _sma_series(closes, period):
    """Serie completa de SMA (rolling sum, O(n))."""
    if len(closes) < period:
        return []
    series = []
    window_sum = sum(closes[:period])
    series.append(window_sum / period)
    for i in range(period, len(closes)):
        window_sum += closes[i] - closes[i - period]
        series.append(window_sum / period)
    return series


def compute_ma_cross(closes, lookback=5):
    """
    Estado de tendencia (MA50 vs MA200) y detección de cruce reciente
    (Golden Cross / Death Cross) dentro de los últimos `lookback` días.
    Retorna (status, cross_event) — cross_event es None si no hubo cruce reciente.
    """
    if len(closes) < 200 + lookback + 1:
        return None, None

    ma50_s  = _sma_series(closes, 50)
    ma200_s = _sma_series(closes, 200)
    offset  = len(ma50_s) - len(ma200_s)
    ma50_s  = ma50_s[offset:]

    diffs  = [ma50_s[i] - ma200_s[i] for i in range(len(ma200_s))]
    status = "alcista" if diffs[-1] > 0 else "bajista"

    cross = None
    recent_signs = [1 if v > 0 else -1 for v in diffs[-(lookback + 1):]]
    if recent_signs[0] != recent_signs[-1]:
        cross = "golden_cross" if recent_signs[-1] > 0 else "death_cross"

    return status, cross


def _rsi_series(closes, period=14):
    """Serie completa de RSI (suavizado de Wilder), alineada al final de `closes`."""
    if len(closes) < period + 1:
        return []
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def _rsi(ag, al):
        if al == 0:
            return 100.0
        return 100 - (100 / (1 + ag / al))

    series = [_rsi(avg_gain, avg_loss)]
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        series.append(_rsi(avg_gain, avg_loss))
    return series


def _find_local_extrema(series, order=3):
    """Índices de mínimos y máximos locales (comparados contra `order` vecinos a cada lado)."""
    mins, maxs = [], []
    n = len(series)
    for i in range(order, n - order):
        window = series[i - order:i + order + 1]
        if series[i] == min(window):
            mins.append(i)
        if series[i] == max(window):
            maxs.append(i)
    return mins, maxs


def compute_divergence(closes, rsi_series, lookback=40, order=3):
    """
    Divergencia RSI vs. precio sobre los últimos `lookback` días.
    'alcista': precio hace un mínimo más bajo mientras el RSI hace un mínimo más alto.
    'bajista': precio hace un máximo más alto mientras el RSI hace un máximo más bajo.
    """
    if not rsi_series or len(rsi_series) < lookback:
        return None

    price_window = closes[-len(rsi_series):][-lookback:]
    rsi_window   = rsi_series[-lookback:]

    price_mins, price_maxs = _find_local_extrema(price_window, order)
    rsi_mins,   rsi_maxs   = _find_local_extrema(rsi_window, order)

    if len(price_mins) >= 2 and len(rsi_mins) >= 2:
        p1, p2 = price_mins[-2], price_mins[-1]
        if price_window[p2] < price_window[p1]:
            r1 = min(rsi_mins, key=lambda i: abs(i - p1))
            r2 = min(rsi_mins, key=lambda i: abs(i - p2))
            if r2 > r1 and rsi_window[r2] > rsi_window[r1]:
                return "alcista"

    if len(price_maxs) >= 2 and len(rsi_maxs) >= 2:
        p1, p2 = price_maxs[-2], price_maxs[-1]
        if price_window[p2] > price_window[p1]:
            r1 = min(rsi_maxs, key=lambda i: abs(i - p1))
            r2 = min(rsi_maxs, key=lambda i: abs(i - p2))
            if r2 > r1 and rsi_window[r2] < rsi_window[r1]:
                return "bajista"

    return None


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
            pct_from_52w_high = round((price - high_52w) / high_52w * 100, 2) if high_52w else None
            pct_from_52w_low  = round((price - low_52w) / low_52w * 100, 2) if low_52w else None

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
            adx, pdi, ndi                 = compute_adx(highs, lows, closes)
            stoch_k, stoch_d              = compute_stochastic(highs, lows, closes)
            roc                           = compute_roc(closes)
            vol_rel                       = compute_vol_rel(volumes)
            obv, obv_signal               = compute_obv(closes, volumes)
            ma_cross_status, ma_cross_event = compute_ma_cross(closes)
            rsi_series                    = _rsi_series(closes)
            divergence                    = compute_divergence(closes, rsi_series)

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
                "pct_from_52w_high": pct_from_52w_high,
                "pct_from_52w_low":  pct_from_52w_low,
                "volume":      vol_today,
                "vol_rel":     vol_rel,
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
                "adx":         adx,
                "pdi":         pdi,
                "ndi":         ndi,
                "stoch_k":     stoch_k,
                "stoch_d":     stoch_d,
                "roc":         roc,
                "obv":         obv,
                "obv_signal":  obv_signal,
                "ma_cross_status": ma_cross_status,
                "ma_cross_event":  ma_cross_event,
                "divergence":  divergence,
                "hist_prices": hist_prices,
                "hist_dates":  hist_dates,
            }
            ok += 1
            extra = []
            if ma_cross_event: extra.append(ma_cross_event)
            if divergence:     extra.append(f"div_{divergence}")
            extra_str = ("  " + " ".join(extra)) if extra else ""
            print(f"  [OK] {sym:6s}  USD {price:>9.2f}  ({change_pct:+.2f}%)  RSI {rsi}  ADX {adx}{extra_str}")

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


