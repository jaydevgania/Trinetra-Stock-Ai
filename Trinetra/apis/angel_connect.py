from SmartApi import SmartConnect
import pyotp
import pandas as pd
import os
from datetime import datetime, timedelta

# ── Base directory — all files saved relative to Trinetra root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── YOUR CREDENTIALS (fill these in) ─────────────────────────
API_KEY    = "QSO7H5TP"
CLIENT_ID  = "J57403939"
PASSWORD   = "2006"
TOTP_TOKEN = "WCMSMLUAFVVWILNK5EV7FWGJTM"

# ── Instrument Tokens ─────────────────────────────────────────
TOKENS = {
    "NIFTY50":   {"symbol": "NIFTY 50",   "token": "99926000", "exchange": "NSE"},
    "BANKNIFTY": {"symbol": "NIFTY BANK", "token": "99926009", "exchange": "NSE"},
    "SENSEX":    {"symbol": "SENSEX",     "token": "99919000", "exchange": "BSE"},
}

# ── Connect ───────────────────────────────────────────────────
def connect():
    try:
        obj  = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_TOKEN).now()
        data = obj.generateSession(CLIENT_ID, PASSWORD, totp)

        if data['status']:
            print("✅ Angel One Connected Successfully!")
            print(f"   Welcome: {data['data'].get('name', CLIENT_ID)}")
            return obj
        else:
            print(f"❌ Connection Failed: {data['message']}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ── Get Live Price ────────────────────────────────────────────
def get_live_price(obj, exchange, symbol, token):
    try:
        data  = obj.ltpData(exchange, symbol, token)
        price = data['data']['ltp']
        print(f"📈 {symbol}: ₹{price}")
        return price
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

# ── Get All Live Prices ───────────────────────────────────────
def get_all_live_prices(obj):
    prices = {}
    for name, info in TOKENS.items():
        price = get_live_price(obj, info['exchange'], info['symbol'], info['token'])
        prices[name] = price
    return prices

# ── Get Historical Candles in Chunks ─────────────────────────
# Angel API limit: max ~400 candles per request for 5-min data
# We fetch in 30-day chunks to get full 2 years of data

def get_historical(obj, token, name, interval="FIVE_MINUTE", days=2555):
    import time
    all_candles = []
    to_date     = datetime.now()
    from_date   = to_date - timedelta(days=days)

    # Fetch in 25-day chunks (safe margin below API limit)
    chunk_days  = 25
    chunk_start = from_date

    print(f"⏳ Fetching {days} days (~7 years) of {name} data in chunks...")
    print(f"   This will take 3-5 minutes — please wait...")

    while chunk_start < to_date:
        chunk_end = min(chunk_start + timedelta(days=chunk_days), to_date)
        try:
            params = {
                "exchange":    exchange,
                "symboltoken": token,
                "interval":    interval,
                "fromdate":    chunk_start.strftime("%Y-%m-%d %H:%M"),
                "todate":      chunk_end.strftime("%Y-%m-%d %H:%M"),
            }
            data = obj.getCandleData(params)
            if data and data.get('data'):
                all_candles.extend(data['data'])
                print(f"   ✅ {chunk_start.strftime('%Y-%m-%d')} → {chunk_end.strftime('%Y-%m-%d')} : {len(data['data'])} candles")
            time.sleep(0.5)   # avoid rate limiting
        except Exception as e:
            print(f"   ⚠️  Chunk error ({chunk_start.strftime('%Y-%m-%d')}): {e}")

        chunk_start = chunk_end + timedelta(minutes=5)

    if not all_candles:
        print(f"❌ No data fetched for {name}")
        return None

    df = pd.DataFrame(all_candles,
                      columns=['date','open','high','low','close','volume'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    df.to_csv(os.path.join(DATA_DIR, f"{name}_historical.csv"), index=False)
    print(f"✅ {name}: {len(df)} total candles saved → {os.path.join(DATA_DIR, f'{name}_historical.csv')}")
    return df

# ── Get historical using yfinance as backup for older data ───
def get_historical_full(obj, token, name, yf_symbol, exchange="NSE"):
    """
    Smart fetch strategy:
    1. Try Angel API for 5-min data (limited to ~1-2 years)
    2. Use yfinance for older daily data
    3. Combine both for maximum history
    """
    import time
    import yfinance as yf
    import numpy as np

    print(f"\n{'='*55}")
    print(f"📊 Fetching full history for {name}")
    print(f"{'='*55}")

    all_candles = []

    # ── Part 1: Angel API — recent 5-min data ────────────────
    print(f"\n[1/2] Fetching 5-min candles from Angel One (10 years)...")
    to_date    = datetime.now()
    from_date  = to_date - timedelta(days=3650)  # 10 years of 5-min data
    chunk_days = 25
    chunk_start= from_date

    while chunk_start < to_date:
        chunk_end = min(chunk_start + timedelta(days=chunk_days), to_date)
        try:
            params = {
                "exchange":    exchange,
                "symboltoken": token,
                "interval":    "FIVE_MINUTE",
                "fromdate":    chunk_start.strftime("%Y-%m-%d %H:%M"),
                "todate":      chunk_end.strftime("%Y-%m-%d %H:%M"),
            }
            data = obj.getCandleData(params)
            if data and data.get('data'):
                all_candles.extend(data['data'])
                print(f"   ✅ {chunk_start.strftime('%Y-%m-%d')} → {chunk_end.strftime('%Y-%m-%d')} : {len(data['data'])} candles")
            time.sleep(0.4)
        except Exception as e:
            print(f"   ⚠️  {chunk_start.strftime('%Y-%m-%d')}: {e}")
        chunk_start = chunk_end + timedelta(minutes=5)

    if all_candles:
        df_5min = pd.DataFrame(all_candles,
                               columns=['date','open','high','low','close','volume'])
        df_5min['date'] = pd.to_datetime(df_5min['date'])
        df_5min = df_5min.drop_duplicates(subset=['date']).sort_values('date')
        print(f"   📊 5-min candles fetched: {len(df_5min)}")
    else:
        df_5min = pd.DataFrame()
        print("   ⚠️  No 5-min data fetched")

    # ── Part 2: yfinance — older daily data (7 years) ────────
    print(f"\n[2/2] Fetching daily candles from yfinance (7 years)...")
    try:
        df_daily = yf.download(yf_symbol, period="7y", interval="1d", progress=False)
        df_daily = df_daily.reset_index()
        df_daily.columns = [c.lower() for c in df_daily.columns]

        # Rename 'datetime'/'index' to 'date'
        for col in ['datetime','index','date']:
            if col in df_daily.columns:
                df_daily = df_daily.rename(columns={col: 'date'})
                break

        df_daily['date'] = pd.to_datetime(df_daily['date'])

        # Select only needed columns
        df_daily = df_daily[['date','open','high','low','close','volume']].copy()
        df_daily['volume'] = df_daily['volume'].fillna(0).astype(int)

        print(f"   📊 Daily candles fetched: {len(df_daily)}")
    except Exception as e:
        print(f"   ⚠️  yfinance error: {e}")
        df_daily = pd.DataFrame()

    # ── Combine: Use daily for old data, 5-min for recent ────
    if len(df_5min) > 0 and len(df_daily) > 0:
        # Get cutoff: oldest 5-min date
        cutoff = df_5min['date'].min()
        df_old = df_daily[df_daily['date'] < cutoff].copy()

        # Combine
        df_combined = pd.concat([df_old, df_5min], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['date'])
        df_combined = df_combined.sort_values('date').reset_index(drop=True)
        print(f"\n✅ Combined: {len(df_old)} daily + {len(df_5min)} 5-min = {len(df_combined)} total candles")
    elif len(df_5min) > 0:
        df_combined = df_5min
    elif len(df_daily) > 0:
        df_combined = df_daily
    else:
        print(f"❌ No data at all for {name}")
        return None

    # Save
    save_path = os.path.join(DATA_DIR, f"{name}_historical.csv")
    df_combined.to_csv(save_path, index=False)
    print(f"✅ {name}: {len(df_combined)} total candles saved → {save_path}")
    return df_combined


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    obj = connect()
    if obj:
        get_all_live_prices(obj)
        get_historical_full(obj, "99926000", "NIFTY50",   "^NSEI")
        get_historical_full(obj, "99926009", "BANKNIFTY", "^NSEBANK")
        get_historical_full(obj, "99919000", "SENSEX",    "^BSESN", exchange="BSE")