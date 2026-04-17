# ============================================================
#  alerts/telegram_alerts.py — Trinetra
#  Telegram Bot Alert System
#
#  Setup (one time only):
#  1. Open Telegram → search @BotFather
#  2. Send /newbot → give name: TrinetraBot
#  3. Copy the BOT_TOKEN it gives you
#  4. Search @userinfobot → send /start → copy your CHAT_ID
#  5. Paste both below and run this file to test
#
#  Run: python alerts/telegram_alerts.py
# ============================================================

import requests
import json
import os
from datetime import datetime
import pytz

# ── YOUR TELEGRAM CREDENTIALS ────────────────────────────────
BOT_TOKEN = "8788431961:AAGH2rhujLksrwy--7oBuRG_9EZBVncevaQ"   # from @BotFather
CHAT_ID   = "5018868220"     # from @userinfobot

IST = pytz.timezone("Asia/Kolkata")

# ════════════════════════════════════════════════════════════
#  SEND MESSAGE
# ════════════════════════════════════════════════════════════

def send_message(text, parse_mode="HTML"):
    """Send a Telegram message"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Add your BOT_TOKEN and CHAT_ID first!")
        print(f"   Message would have been:\n{text}")
        return False

    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id":    CHAT_ID,
        "text":       text,
        "parse_mode": parse_mode,
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            print(f"✅ Telegram alert sent!")
            return True
        else:
            print(f"❌ Telegram error: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
        return False

def send_photo(image_path, caption=""):
    """Send a chart image to Telegram"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(f"⚠️  Would have sent image: {image_path}")
        return False
    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, 'rb') as img:
            r = requests.post(url, data={
                "chat_id": CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }, files={"photo": img}, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Photo send failed: {e}")
        return False

# ════════════════════════════════════════════════════════════
#  ALERT TEMPLATES
# ════════════════════════════════════════════════════════════

def alert_prediction(prediction):
    """
    Send a prediction alert.
    prediction = dict from combined_prediction.py
    """
    sym   = prediction['symbol']
    price = prediction['current_price']
    direc = prediction['direction']
    conf  = prediction['confidence']
    t20   = prediction['target_20min']
    t30   = prediction['target_30min']
    sl    = prediction['stoploss']
    trade = prediction['trade']
    strat = prediction.get('strategy', '')
    ts    = prediction.get('timestamp', datetime.now(IST).strftime("%d %b %Y %H:%M IST"))

    # Direction emoji
    if "BULLISH" in direc:  emoji = "🟢"; action = "BUY / CE"
    elif "BEARISH" in direc: emoji = "🔴"; action = "SELL / PE"
    else:                    emoji = "🟡"; action = "AVOID"

    # Confidence bar
    filled = int(conf / 10)
    bar    = "█" * filled + "░" * (10 - filled)

    # Only alert on strong signals
    if conf < 60:
        conf_label = "⚠️ MODERATE — Use caution"
    elif conf >= 70:
        conf_label = "🔥 VERY STRONG"
    else:
        conf_label = "✅ STRONG"

    msg = f"""
<b>🤖 TRINETRA SIGNAL</b>
<b>━━━━━━━━━━━━━━━━━━━━━━</b>

{emoji} <b>{sym}</b> | {ts}

<b>Direction  :</b> {direc}
<b>Confidence :</b> {conf:.1f}% {conf_label}
<code>[{bar}]</code>

<b>Current ₹  :</b> {price:,.2f}
<b>Target+20m :</b> ₹{t20:,.1f}
<b>Target+30m :</b> ₹{t30:,.1f}
<b>Stop Loss  :</b> ₹{sl:,.1f}

<b>Action     :</b> {action}
<b>Strategy   :</b> {strat}

<i>⚠️ Not financial advice. DYOR.</i>
<b>━━━━━━━━━━━━━━━━━━━━━━</b>
    """.strip()

    return send_message(msg)

def alert_market_open():
    """Send market open alert at 9:15 AM"""
    msg = """
🔔 <b>TRINETRA — MARKET OPEN</b>
━━━━━━━━━━━━━━━━━━━━━━
📅 NSE/BSE opens now — 9:15 AM IST
🤖 Trinetra is active and scanning...
━━━━━━━━━━━━━━━━━━━━━━
    """.strip()
    return send_message(msg)

def alert_market_close(summary=None):
    """Send market close summary at 3:30 PM"""
    if summary:
        msg = f"""
🔔 <b>TRINETRA — MARKET CLOSED</b>
━━━━━━━━━━━━━━━━━━━━━━
📅 NSE/BSE closed — 3:30 PM IST

<b>Today's Summary:</b>
{summary}

🤖 Trinetra going to sleep. See you tomorrow 9:15 AM!
━━━━━━━━━━━━━━━━━━━━━━
        """.strip()
    else:
        msg = """
🔔 <b>TRINETRA — MARKET CLOSED</b>
━━━━━━━━━━━━━━━━━━━━━━
📅 NSE/BSE closed — 3:30 PM IST
🤖 Trinetra going to sleep. See you tomorrow 9:15 AM!
━━━━━━━━━━━━━━━━━━━━━━
        """.strip()
    return send_message(msg)

def alert_high_vix(vix):
    """Alert when VIX is very high — dangerous market"""
    msg = f"""
⚠️ <b>HIGH VIX ALERT — TRINETRA</b>
━━━━━━━━━━━━━━━━━━━━━━
India VIX: <b>{vix:.2f}</b> — EXTREME FEAR

⚠️ Market is highly volatile today!
📉 Confidence in all predictions reduced
🛑 Consider smaller position sizes
━━━━━━━━━━━━━━━━━━━━━━
    """.strip()
    return send_message(msg)

def alert_error(error_msg):
    """Alert when Trinetra encounters an error"""
    msg = f"""
🔴 <b>TRINETRA ERROR</b>
━━━━━━━━━━━━━━━━━━━━━━
<code>{error_msg[:200]}</code>
━━━━━━━━━━━━━━━━━━━━━━
    """.strip()
    return send_message(msg)

def alert_daily_summary(predictions_today, correct_today):
    """Send end of day accuracy summary"""
    acc = correct_today / predictions_today * 100 if predictions_today > 0 else 0
    msg = f"""
📊 <b>TRINETRA DAILY REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━
📅 {datetime.now(IST).strftime('%d %b %Y')}

Total Signals  : {predictions_today}
Correct        : {correct_today}
Accuracy Today : {acc:.1f}%

{'🏆 Great day!' if acc >= 70 else '✅ Good day!' if acc >= 58 else '⚠️ Tough market today'}
━━━━━━━━━━━━━━━━━━━━━━
    """.strip()
    return send_message(msg)

# ════════════════════════════════════════════════════════════
#  TEST
# ════════════════════════════════════════════════════════════

def test_bot():
    """Test that your bot is working"""
    msg = """
✅ <b>TRINETRA BOT CONNECTED!</b>
━━━━━━━━━━━━━━━━━━━━━━
🤖 Trinetra alert system is ready!
📊 You will receive trading signals here.
⏰ Active: Mon-Fri 9:15 AM — 3:30 PM IST
━━━━━━━━━━━━━━━━━━━━━━
    """.strip()
    return send_message(msg)

# ── Main test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Testing Trinetra Telegram Bot...")
    print("\nStep 1: Get BOT_TOKEN from @BotFather on Telegram")
    print("Step 2: Get CHAT_ID from @userinfobot on Telegram")
    print("Step 3: Paste them at top of this file")
    print("Step 4: Run again to test\n")

    # Test with a dummy prediction
    test_prediction = {
        "symbol":       "NIFTY50",
        "current_price": 22379.20,
        "direction":    "🔴 BEARISH",
        "confidence":   78.3,
        "target_20min": 22289.0,
        "target_30min": 22234.0,
        "stoploss":     22454.0,
        "trade":        "SELL / PE Options",
        "strategy":     "Buy ATM Put",
        "timestamp":    datetime.now(IST).strftime("%d %b %Y %H:%M IST"),
    }

    test_bot()
    alert_prediction(test_prediction)