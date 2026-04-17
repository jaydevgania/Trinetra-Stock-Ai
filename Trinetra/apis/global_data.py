# ============================================================
#  global_data.py — Global Market Data
#  Sources: Yahoo Finance (yfinance) + Alpha Vantage
# ============================================================

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# ── YOUR API KEY ──────────────────────────────────────────────
ALPHA_VANTAGE_KEY = "your_alpha_vantage_key"  # from alphavantage.co

# ════════════════════════════════════════════════════════════
#  YAHOO FINANCE — Free Global Market Data
# ════════════════════════════════════════════════════════════

# Key global symbols that affect Indian market
GLOBAL_SYMBOLS = {
    # US Markets
    "Dow Jones":    "^DJI",
    "S&P 500":      "^GSPC",
    "Nasdaq":       "^IXIC",
    "US VIX":       "^VIX",

    # Commodities
    "Crude Oil":    "CL=F",
    "Gold":         "GC=F",
    "Silver":       "SI=F",

    # Currency (affects Indian market)
    "USD/INR":      "USDINR=X",
    "EUR/INR":      "EURINR=X",

    # Asian Markets
    "Nikkei 225":   "^N225",   # Japan
    "Hang Seng":    "^HSI",    # Hong Kong
    "GIFT/SGX Nifty": "^NSEI",      # GIFT Nifty (formerly SGX Nifty) — best proxy available via yfinance
}

def get_global_live():
    """Get live prices of all global markets affecting India"""
    print("\n🌍 GLOBAL MARKET SNAPSHOT")
    print("=" * 50)
    results = {}

    for name, symbol in GLOBAL_SYMBOLS.items():
        try:
            ticker = yf.Ticker(symbol)
            info   = ticker.fast_info
            price  = round(info.last_price, 2)
            prev   = round(info.previous_close, 2)
            change = round(((price - prev) / prev) * 100, 2)
            arrow  = "🟢" if change >= 0 else "🔴"
            print(f"  {arrow} {name:15} : {price:>10} ({change:+.2f}%)")
            results[name] = {"price": price, "change_pct": change, "symbol": symbol}
        except Exception as e:
            print(f"  ⚠️  {name}: unavailable")

    print("=" * 50)
    return results

def get_gift_sgx_nifty():
    """
    GIFT Nifty / SGX Nifty — predicts Indian market opening direction.
    Trades 6:30 AM – 3:40 PM IST and 4:35 PM – 2:45 AM IST.
    Check this at 8:30 AM to know if Nifty will gap up or gap down.

    SGX Nifty = old name (Singapore Exchange)
    GIFT Nifty = new name (GIFT City, India) — same product
    """
    price = None

    # Method 1: Try yfinance with Nifty 50 (best available proxy)
    try:
        ticker = yf.Ticker("^NSEI")
        price  = round(ticker.fast_info.last_price, 2)
    except:
        pass

    # Method 2: Scrape equitypandit SGX Nifty page
    if not price:
        try:
            import requests as req
            headers = {"User-Agent": "Mozilla/5.0"}
            resp    = req.get("https://www.equitypandit.com/sgxnifty/",
                              headers=headers, timeout=10)
            from bs4 import BeautifulSoup
            soup  = BeautifulSoup(resp.text, "html.parser")
            # Find the live price element
            el    = soup.find("span", {"id": "sgxnifty_ltp"})
            if el:
                price = float(el.text.strip().replace(",",""))
        except:
            pass

    if price:
        print(f"🇸🇬 SGX / GIFT Nifty : ₹{price}")
        print(f"   → Indian market likely to open near ₹{price}")
        return price
    else:
        print(f"❌ SGX/GIFT Nifty: Could not fetch price")
        return None

def get_crude_oil():
    """Crude oil price — key driver of Indian inflation & markets"""
    try:
        crude  = yf.Ticker("CL=F")
        price  = crude.fast_info.last_price
        prev   = crude.fast_info.previous_close
        change = round(((price - prev) / prev) * 100, 2)
        arrow  = "🟢" if change >= 0 else "🔴"
        print(f"🛢️  Crude Oil: ${price:.2f} {arrow} ({change:+.2f}%)")
        if change > 2:
            print("   ⚠️  Crude spike — Negative for Indian market (inflation risk)")
        elif change < -2:
            print("   ✅ Crude down — Positive for Indian market")
        return {"price": price, "change_pct": change}
    except Exception as e:
        print(f"❌ Crude Oil error: {e}")
        return None

def get_usd_inr():
    """USD/INR exchange rate — affects FII flows into India"""
    try:
        fx     = yf.Ticker("USDINR=X")
        rate   = fx.fast_info.last_price
        prev   = fx.fast_info.previous_close
        change = round(rate - prev, 4)
        print(f"💱 USD/INR: ₹{rate:.2f} ({change:+.4f})")
        if rate > 84:
            print("   ⚠️  Rupee weak — FIIs may sell Indian assets")
        else:
            print("   ✅ Rupee stable")
        return {"rate": rate, "change": change}
    except Exception as e:
        print(f"❌ USD/INR error: {e}")
        return None

def get_historical_global(symbol="^GSPC", days=365, name="SP500"):
    """Get historical data for any global symbol"""
    try:
        end   = datetime.now()
        start = end - timedelta(days=days)
        df    = yf.download(symbol, start=start, end=end, interval="1d")
        df.to_csv(f"data/{name}_historical.csv")
        print(f"✅ {name} historical data: {len(df)} days saved")
        return df
    except Exception as e:
        print(f"❌ Historical error for {symbol}: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  ALPHA VANTAGE — Economic Indicators & Forex
# ════════════════════════════════════════════════════════════

def get_alpha_forex(from_currency="USD", to_currency="INR"):
    """Get real-time forex rate from Alpha Vantage"""
    try:
        url    = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_KEY}"
        resp   = requests.get(url, timeout=10).json()
        data   = resp['Realtime Currency Exchange Rate']
        rate   = float(data['5. Exchange Rate'])
        print(f"💱 {from_currency}/{to_currency} (Alpha Vantage): {rate:.4f}")
        return rate
    except Exception as e:
        print(f"❌ Alpha Vantage Forex error: {e}")
        return None

def get_alpha_commodity(symbol="BRENT"):
    """
    Get commodity prices from Alpha Vantage
    symbol options: 'BRENT', 'WTI', 'NATURAL_GAS', 'COPPER', 'ALUMINUM'
    """
    try:
        url  = f"https://www.alphavantage.co/query?function={symbol}&interval=monthly&apikey={ALPHA_VANTAGE_KEY}"
        resp = requests.get(url, timeout=10).json()
        data = resp.get('data', [])
        if data:
            latest = data[0]
            print(f"🛢️  {symbol}: ${latest['value']} (as of {latest['date']})")
            return latest
        return None
    except Exception as e:
        print(f"❌ Alpha Vantage Commodity error: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  MARKET IMPACT ANALYSIS — How Global Affects India
# ════════════════════════════════════════════════════════════

def analyze_global_impact():
    """
    Analyzes global signals and predicts
    their likely impact on Indian market opening
    """
    print("\n🔍 GLOBAL IMPACT ON INDIAN MARKET")
    print("=" * 50)

    signals = []

    # Check US markets (most important for India)
    sp500  = yf.Ticker("^GSPC").fast_info
    sp_chg = ((sp500.last_price - sp500.previous_close) / sp500.previous_close) * 100
    if sp_chg > 1:
        signals.append(("🟢", f"S&P 500 up {sp_chg:.1f}% — Positive for Indian opening"))
    elif sp_chg < -1:
        signals.append(("🔴", f"S&P 500 down {sp_chg:.1f}% — Negative for Indian opening"))

    # Check Crude Oil
    crude  = yf.Ticker("CL=F").fast_info
    cr_chg = ((crude.last_price - crude.previous_close) / crude.previous_close) * 100
    if cr_chg > 2:
        signals.append(("🔴", f"Crude up {cr_chg:.1f}% — Inflation risk, negative for India"))
    elif cr_chg < -2:
        signals.append(("🟢", f"Crude down {cr_chg:.1f}% — Positive for India"))

    # Check USD/INR
    fx     = yf.Ticker("USDINR=X").fast_info
    fx_chg = fx.last_price - fx.previous_close
    if fx_chg > 0.5:
        signals.append(("🔴", f"Rupee weakened ₹{fx_chg:.2f} — FII outflow risk"))
    elif fx_chg < -0.5:
        signals.append(("🟢", f"Rupee strengthened ₹{abs(fx_chg):.2f} — FII inflow likely"))

    # Print summary
    for arrow, msg in signals:
        print(f"  {arrow} {msg}")

    if not signals:
        print("  🟡 No major global triggers — Indian market likely range-bound")

    print("=" * 50)
    return signals

# ── Main Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    get_global_live()
    print()
    get_crude_oil()
    get_usd_inr()
    get_gift_sgx_nifty()
    print()
    analyze_global_impact()