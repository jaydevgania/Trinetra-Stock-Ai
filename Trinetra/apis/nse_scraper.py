# ============================================================
#  nse_scraper.py — NSE Data using yfinance + Jugaad Trader
#
#  Install these first:
#  pip install yfinance jugaad-data pandas
# ============================================================

import yfinance as yf
import pandas as pd
import os
from datetime import datetime

os.makedirs("data", exist_ok=True)

# ════════════════════════════════════════════════════════════
#  LIVE QUOTES using yfinance (100% reliable, no blocking)
# ════════════════════════════════════════════════════════════

# NSE symbols in yfinance format
SYMBOLS = {
    "NIFTY 50":   "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX":  "^INDIAVIX",
}

def get_nifty_live():
    try:
        ticker = yf.Ticker("^NSEI")
        price  = ticker.fast_info.last_price
        prev   = ticker.fast_info.previous_close
        chng   = round(((price - prev) / prev) * 100, 2)
        arrow  = "🟢" if chng >= 0 else "🔴"
        print(f"{arrow} NIFTY 50   : ₹{round(price,2)} ({chng:+}%)")
        return round(price, 2)
    except Exception as e:
        print(f"❌ Nifty error: {e}")
        return None

def get_banknifty_live():
    try:
        ticker = yf.Ticker("^NSEBANK")
        price  = ticker.fast_info.last_price
        prev   = ticker.fast_info.previous_close
        chng   = round(((price - prev) / prev) * 100, 2)
        arrow  = "🟢" if chng >= 0 else "🔴"
        print(f"{arrow} BANK NIFTY : ₹{round(price,2)} ({chng:+}%)")
        return round(price, 2)
    except Exception as e:
        print(f"❌ Bank Nifty error: {e}")
        return None

def get_india_vix():
    try:
        ticker = yf.Ticker("^INDIAVIX")
        vix    = ticker.fast_info.last_price
        vix    = round(vix, 2)

        if vix > 20:   level = "⚠️  HIGH FEAR — Big move expected"
        elif vix > 15: level = "🟡 MODERATE — Some uncertainty"
        else:          level = "✅ LOW — Market is calm"

        print(f"⚡ India VIX : {vix} → {level}")
        return {"vix": vix, "level": level}
    except Exception as e:
        print(f"❌ India VIX error: {e}")
        return None

def get_all_live_quotes():
    print("\n📊 LIVE MARKET QUOTES")
    print("-" * 40)
    nifty     = get_nifty_live()
    banknifty = get_banknifty_live()
    vix       = get_india_vix()
    return {"nifty": nifty, "banknifty": banknifty, "vix": vix}

# ════════════════════════════════════════════════════════════
#  OPTIONS CHAIN using jugaad-data
#  jugaad-data uses NSE's mobile API which is less restricted
# ════════════════════════════════════════════════════════════

def get_options_chain(symbol="NIFTY"):
    try:
        from jugaad_data.nse import NSELive
        n       = NSELive()
        data    = n.equities_option_chain(symbol)

        records     = data['records']['data']
        expiry_date = data['records']['expiryDates'][0]
        spot_price  = data['records']['underlyingValue']

        rows = []
        for record in records:
            if record.get('expiryDate') != expiry_date:
                continue
            row = {"strikePrice": record['strikePrice']}
            if 'CE' in record:
                ce = record['CE']
                row.update({
                    'CE_OI':     ce.get('openInterest', 0),
                    'CE_chngOI': ce.get('changeinOpenInterest', 0),
                    'CE_LTP':    ce.get('lastPrice', 0),
                    'CE_IV':     ce.get('impliedVolatility', 0),
                    'CE_volume': ce.get('totalTradedVolume', 0),
                })
            if 'PE' in record:
                pe = record['PE']
                row.update({
                    'PE_OI':     pe.get('openInterest', 0),
                    'PE_chngOI': pe.get('changeinOpenInterest', 0),
                    'PE_LTP':    pe.get('lastPrice', 0),
                    'PE_IV':     pe.get('impliedVolatility', 0),
                    'PE_volume': pe.get('totalTradedVolume', 0),
                })
            rows.append(row)

        df = pd.DataFrame(rows).fillna(0)
        df.to_csv(f"data/{symbol}_options_chain.csv", index=False)
        print(f"✅ {symbol} Options Chain | Spot: ₹{spot_price} | Expiry: {expiry_date} | {len(df)} strikes")
        return df, spot_price, expiry_date

    except ImportError:
        print("⚠️  jugaad-data not installed. Run: pip install jugaad-data")
        return None, None, None
    except Exception as e:
        print(f"❌ Options Chain error ({symbol}): {e}")
        return None, None, None

# ════════════════════════════════════════════════════════════
#  PCR — Put Call Ratio
# ════════════════════════════════════════════════════════════

def calculate_pcr(symbol="NIFTY"):
    try:
        df, spot, expiry = get_options_chain(symbol)
        if df is None:
            return None

        pcr = round(df['PE_OI'].sum() / df['CE_OI'].sum(), 2)

        if pcr > 1.2:   sentiment = "🟢 BULLISH"
        elif pcr < 0.8: sentiment = "🔴 BEARISH"
        else:           sentiment = "🟡 NEUTRAL"

        print(f"📊 {symbol} PCR: {pcr} → {sentiment}")
        return {"symbol": symbol, "pcr": pcr, "sentiment": sentiment, "spot": spot}

    except Exception as e:
        print(f"❌ PCR error ({symbol}): {e}")
        return None

# ════════════════════════════════════════════════════════════
#  MAX PAIN
# ════════════════════════════════════════════════════════════

def calculate_max_pain(symbol="NIFTY"):
    try:
        df, spot, _ = get_options_chain(symbol)
        if df is None:
            return None

        pain_values = {}
        for strike in df['strikePrice'].unique():
            above     = df[df['strikePrice'] > strike]
            below     = df[df['strikePrice'] < strike]
            call_pain = ((above['strikePrice'] - strike) * above['CE_OI']).sum()
            put_pain  = ((strike - below['strikePrice']) * below['PE_OI']).sum()
            pain_values[strike] = call_pain + put_pain

        max_pain = min(pain_values, key=pain_values.get)
        print(f"🎯 {symbol} Max Pain: ₹{max_pain} | Spot: ₹{spot}")
        return {"symbol": symbol, "max_pain": max_pain, "spot": spot}

    except Exception as e:
        print(f"❌ Max Pain error: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  MASTER SNAPSHOT
# ════════════════════════════════════════════════════════════

def get_full_options_snapshot():
    print("\n⚙️  OPTIONS MARKET SNAPSHOT — Trinetra")
    print("=" * 50)

    quotes        = get_all_live_quotes()
    nifty_pcr     = calculate_pcr("NIFTY")
    banknifty_pcr = calculate_pcr("BANKNIFTY")
    nifty_maxpain = calculate_max_pain("NIFTY")

    print("=" * 50)
    return {
        "quotes":        quotes,
        "nifty_pcr":     nifty_pcr,
        "banknifty_pcr": banknifty_pcr,
        "max_pain":      nifty_maxpain,
    }

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    get_full_options_snapshot()