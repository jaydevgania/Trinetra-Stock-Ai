# ============================================================
#  bse_nse_connect.py — NSE + BSE Live Data
#  Uses yfinance only — no bsedata/nsetools (both outdated)
# ============================================================

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

os.makedirs("data", exist_ok=True)

# ── Index Tickers ─────────────────────────────────────────────
INDICES = {
    "NIFTY 50":   "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX":     "^BSESN",
    "INDIA VIX":  "^INDIAVIX",
    "NIFTY IT":   "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
}

# ════════════════════════════════════════════════════════════
#  LIVE INDEX QUOTES
# ════════════════════════════════════════════════════════════

def get_index_quote(name, ticker):
    try:
        t     = yf.Ticker(ticker)
        price = round(t.fast_info.last_price, 2)
        prev  = round(t.fast_info.previous_close, 2)
        chng  = round(price - prev, 2)
        pchng = round((chng / prev) * 100, 2)
        arrow = "🟢" if pchng >= 0 else "🔴"
        print(f"  {arrow} {name:15} : ₹{price:>10,.2f}  ({pchng:+.2f}%)")
        return {"name": name, "price": price, "change": chng, "pChange": pchng}
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return None

def get_nifty_live():
    return get_index_quote("NIFTY 50", "^NSEI")

def get_banknifty_live():
    return get_index_quote("BANK NIFTY", "^NSEBANK")

def get_sensex_live():
    return get_index_quote("SENSEX", "^BSESN")

def get_india_vix():
    try:
        t     = yf.Ticker("^INDIAVIX")
        vix   = round(t.fast_info.last_price, 2)
        prev  = round(t.fast_info.previous_close, 2)
        chng  = round(((vix - prev) / prev) * 100, 2)

        if vix > 20:   level = "⚠️  HIGH FEAR"
        elif vix > 15: level = "🟡 MODERATE"
        else:          level = "✅ LOW / CALM"

        print(f"  ⚡ {'INDIA VIX':15} : {vix:>10.2f}  ({chng:+.2f}%)  {level}")
        return {"vix": vix, "change": chng, "level": level}
    except Exception as e:
        print(f"  ❌ India VIX error: {e}")
        return None

def get_all_live():
    print("\n" + "="*50)
    print("📊 LIVE MARKET SNAPSHOT — Trinetra")
    print("="*50)
    nifty     = get_nifty_live()
    banknifty = get_banknifty_live()
    sensex    = get_sensex_live()
    vix       = get_india_vix()
    print("="*50)
    return {"nifty": nifty, "banknifty": banknifty,
            "sensex": sensex, "vix": vix}

# ════════════════════════════════════════════════════════════
#  TOP GAINERS & LOSERS — NSE (scrape from NSE website)
# ════════════════════════════════════════════════════════════

def get_nse_gainers_losers():
    """Fetch top gainers and losers from NSE via yfinance screener"""
    try:
        # Nifty 50 stocks list
        nifty50_symbols = [
            "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
            "HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
            "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","HCLTECH.NS",
            "SUNPHARMA.NS","TITAN.NS","BAJFINANCE.NS","WIPRO.NS","ONGC.NS",
            "NTPC.NS","POWERGRID.NS","ULTRACEMCO.NS","TECHM.NS","INDUSINDBK.NS",
            "TATAMOTORS.NS" if False else "M&M.NS","NESTLEIND.NS","JSWSTEEL.NS","COALINDIA.NS","ADANIENT.NS",
        ]

        rows = []
        print("📊 Fetching Nifty 50 stocks data...")

        for sym in nifty50_symbols:
            try:
                t     = yf.Ticker(sym)
                price = t.fast_info.last_price
                prev  = t.fast_info.previous_close
                if price and prev:
                    pchng = round(((price - prev) / prev) * 100, 2)
                    rows.append({
                        "symbol":     sym.replace(".NS",""),
                        "lastPrice":  round(price, 2),
                        "pChange":    pchng,
                        "change":     round(price - prev, 2),
                    })
            except:
                continue

        if not rows:
            print("⚠️  No stock data fetched")
            return None, None

        df = pd.DataFrame(rows)
        df = df.sort_values("pChange", ascending=False)

        # Top 5 gainers (only truly positive)
        gainers = df[df['pChange'] > 0].head(5)
        print(f"\n🟢 TOP GAINERS:")
        if len(gainers) == 0:
            print("  No gainers today — fully bearish market")
        for _, row in gainers.iterrows():
            print(f"  🟢 {row['symbol']:15} ₹{row['lastPrice']:>8.2f}  (+{row['pChange']}%)")

        # Top 5 losers (only truly negative)
        losers = df[df['pChange'] < 0].tail(5).iloc[::-1]
        print(f"\n🔴 TOP LOSERS:")
        for _, row in losers.iterrows():
            print(f"  🔴 {row['symbol']:15} ₹{row['lastPrice']:>8.2f}  ({row['pChange']}%)")

        df.to_csv("data/nifty50_stocks.csv", index=False)
        return gainers, losers

    except Exception as e:
        print(f"❌ Gainers/Losers error: {e}")
        return None, None

# ════════════════════════════════════════════════════════════
#  SECTOR PERFORMANCE
# ════════════════════════════════════════════════════════════

def get_sector_performance():
    """Check which sectors are up/down today"""
    sectors = {
        "IT":          "^CNXIT",
        "Auto":        "^CNXAUTO",
        "Pharma":      "^CNXPHARMA",
        "Bank":        "^NSEBANK",
        "FMCG":        "^CNXFMCG",
        "Metal":       "^CNXMETAL",
        "Realty":      "^CNXREALTY",
        "Energy":      "^CNXENERGY",
    }

    print(f"\n📊 SECTOR PERFORMANCE:")
    print("-" * 40)
    results = {}

    for sector, ticker in sectors.items():
        try:
            t     = yf.Ticker(ticker)
            price = t.fast_info.last_price
            prev  = t.fast_info.previous_close
            pchng = round(((price - prev) / prev) * 100, 2)
            arrow = "🟢" if pchng >= 0 else "🔴"
            bar   = "█" * int(abs(pchng) * 2)
            print(f"  {arrow} {sector:10} {pchng:+.2f}%  {bar}")
            results[sector] = pchng
        except:
            continue

    return results

# ════════════════════════════════════════════════════════════
#  MARKET BREADTH — How many stocks up vs down
# ════════════════════════════════════════════════════════════

def get_market_breadth():
    """Count advancing vs declining stocks in Nifty 50"""
    try:
        nifty50_symbols = [
            "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
            "HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
            "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","HCLTECH.NS",
            "SUNPHARMA.NS","TITAN.NS","BAJFINANCE.NS","WIPRO.NS","ONGC.NS",
            "NTPC.NS","POWERGRID.NS","ULTRACEMCO.NS","TECHM.NS","INDUSINDBK.NS",
            "TATAMOTORS.NS" if False else "M&M.NS","NESTLEIND.NS","JSWSTEEL.NS","COALINDIA.NS","ADANIENT.NS",
        ]

        advances = declines = unchanged = 0
        for sym in nifty50_symbols:
            try:
                t     = yf.Ticker(sym)
                price = t.fast_info.last_price
                prev  = t.fast_info.previous_close
                chng  = ((price - prev) / prev) * 100
                if chng > 0.1:    advances  += 1
                elif chng < -0.1: declines  += 1
                else:             unchanged += 1
            except:
                continue

        total = advances + declines + unchanged
        ratio = round(advances / declines, 2) if declines > 0 else 999

        mood  = "🟢 BULLISH" if advances > declines else "🔴 BEARISH"
        print(f"\n📊 MARKET BREADTH (Nifty 50):")
        print(f"  🟢 Advancing : {advances}")
        print(f"  🔴 Declining : {declines}")
        print(f"  🟡 Unchanged : {unchanged}")
        print(f"  A/D Ratio   : {ratio}  →  {mood}")

        return {"advances": advances, "declines": declines,
                "unchanged": unchanged, "ratio": ratio, "mood": mood}

    except Exception as e:
        print(f"❌ Market Breadth error: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  FULL SNAPSHOT
# ════════════════════════════════════════════════════════════

def get_full_market_snapshot():
    quotes  = get_all_live()
    gainers, losers = get_nse_gainers_losers()
    sectors = get_sector_performance()
    breadth = get_market_breadth()
    return {
        "quotes":   quotes,
        "gainers":  gainers,
        "losers":   losers,
        "sectors":  sectors,
        "breadth":  breadth,
    }

# ── Main Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    get_full_market_snapshot()