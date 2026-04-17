# ============================================================
#  dashboard/app.py — Trinetra Live Dashboard
#  Plotly Dash — Dark theme trading UI
#
#  Install: pip install dash plotly dash-bootstrap-components
#  Run    : python dashboard/app.py
#  Open   : http://localhost:8050
# ============================================================

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os, sys, json
from datetime import datetime, timedelta
import pytz
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

IST      = pytz.timezone("Asia/Kolkata")
SYMBOLS  = ["NIFTY50", "BANKNIFTY", "SENSEX"]
TICKERS  = {"NIFTY50":"^NSEI", "BANKNIFTY":"^NSEBANK", "SENSEX":"^BSESN"}

# ── Dark theme colors ─────────────────────────────────────────
DARK_BG    = "#0d1117"
CARD_BG    = "#161b22"
BORDER     = "#30363d"
GREEN      = "#00e5a0"
RED        = "#ff3d5a"
YELLOW     = "#ffe600"
BLUE       = "#00aaff"
PURPLE     = "#9d4edd"
TEXT       = "#e6edf3"
MUTED      = "#8b949e"

# ════════════════════════════════════════════════════════════
#  APP INIT
# ════════════════════════════════════════════════════════════

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="Trinetra — AI Market Intelligence",
    update_title=None,
    meta_tags=[{"name":"viewport","content":"width=device-width, initial-scale=1"}]
)
server = app.server   # for deployment

# ════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════

def fetch_candles(symbol, period="2d", interval="5m"):
    try:
        ticker = TICKERS[symbol]
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df = df.reset_index()
        for col in df.columns:
            if col.lower() in ['datetime','date','index']:
                df = df.rename(columns={col:'date'}); break
        df['date'] = pd.to_datetime(df['date'])
        return df.dropna().reset_index(drop=True)
    except:
        return pd.DataFrame()

def get_current_prices():
    prices = {}
    for sym, ticker in TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            prices[sym] = round(t.fast_info.last_price, 2)
        except:
            prices[sym] = 0
    return prices

def load_prediction_log():
    log_path = os.path.join(DATA_DIR, "combined_log.csv")
    if os.path.exists(log_path):
        try:
            return pd.read_csv(log_path).tail(50)
        except:
            pass
    return pd.DataFrame()

def make_candlestick(df, symbol):
    fig = make_subplots(rows=2, cols=1,
        shared_xaxes=True, row_heights=[0.7, 0.3],
        vertical_spacing=0.03)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['date'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        increasing_line_color=GREEN,
        decreasing_line_color=RED,
        name=symbol,
        increasing_fillcolor=GREEN,
        decreasing_fillcolor=RED,
    ), row=1, col=1)

    # EMAs
    if len(df) >= 9:
        df['ema9']  = df['close'].ewm(span=9).mean()
        df['ema21'] = df['close'].ewm(span=21).mean()
        fig.add_trace(go.Scatter(x=df['date'], y=df['ema9'],
            line=dict(color=YELLOW, width=1), name='9 EMA', opacity=0.8), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['ema21'],
            line=dict(color=PURPLE, width=1), name='21 EMA', opacity=0.8), row=1, col=1)

    # Volume
    colors = [GREEN if df['close'].iloc[i] >= df['open'].iloc[i] else RED
              for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df['date'], y=df['volume'],
        marker_color=colors, opacity=0.6, name='Volume'
    ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor=DARK_BG, plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="monospace"),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor=CARD_BG, bordercolor=BORDER),
        margin=dict(l=10, r=10, t=10, b=10),
        height=450,
    )
    fig.update_xaxes(gridcolor=BORDER, showgrid=True)
    fig.update_yaxes(gridcolor=BORDER, showgrid=True)
    return fig

def make_gauge(value, title, min_val=0, max_val=100, color=GREEN):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(color=TEXT, size=12)),
        number=dict(font=dict(color=TEXT, size=20)),
        gauge=dict(
            axis=dict(range=[min_val, max_val],
                      tickcolor=MUTED, tickfont=dict(color=MUTED)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=CARD_BG,
            bordercolor=BORDER,
            steps=[
                dict(range=[min_val, max_val*0.33], color="#1a1f2a"),
                dict(range=[max_val*0.33, max_val*0.66], color="#1f2937"),
                dict(range=[max_val*0.66, max_val], color="#1a2a1f"),
            ],
        )
    ))
    fig.update_layout(
        paper_bgcolor=DARK_BG, font=dict(color=TEXT),
        height=180, margin=dict(l=15, r=15, t=30, b=10)
    )
    return fig

# ════════════════════════════════════════════════════════════
#  LAYOUT COMPONENTS
# ════════════════════════════════════════════════════════════

def card(children, style=None):
    base = {"background": CARD_BG, "border": f"1px solid {BORDER}",
            "borderRadius": "8px", "padding": "16px", "marginBottom": "12px"}
    if style: base.update(style)
    return html.Div(children, style=base)

def price_card(symbol, price, change_pct):
    color = GREEN if change_pct >= 0 else RED
    arrow = "▲" if change_pct >= 0 else "▼"
    return card([
        html.Div(symbol, style={"color": MUTED, "fontSize": "12px", "fontWeight": "bold"}),
        html.Div(f"₹{price:,.2f}",
                 style={"color": TEXT, "fontSize": "22px", "fontWeight": "bold", "margin": "4px 0"}),
        html.Div(f"{arrow} {abs(change_pct):.2f}%",
                 style={"color": color, "fontSize": "14px"}),
    ], style={"textAlign": "center", "minWidth": "150px"})

def signal_badge(direction, confidence):
    if "BULLISH" in direction:   bg, text = "#00e5a020", GREEN
    elif "BEARISH" in direction: bg, text = "#ff3d5a20", RED
    else:                         bg, text = "#ffe60020", YELLOW
    return html.Span(
        f"{direction.replace('🟢','').replace('🔴','').replace('🟡','').strip()} {confidence:.0f}%",
        style={"background": bg, "color": text, "borderRadius": "20px",
               "padding": "4px 12px", "fontSize": "13px", "fontWeight": "bold",
               "border": f"1px solid {text}30"}
    )

# ════════════════════════════════════════════════════════════
#  MAIN LAYOUT
# ════════════════════════════════════════════════════════════

app.layout = html.Div(style={
    "background": DARK_BG, "minHeight": "100vh",
    "fontFamily": "'Segoe UI', monospace", "color": TEXT,
    "padding": "0px"
}, children=[

    # ── Auto-refresh every 60 seconds ────────────────────────
    dcc.Interval(id="refresh-60s",  interval=60_000,  n_intervals=0),
    dcc.Interval(id="refresh-300s", interval=300_000, n_intervals=0),
    dcc.Store(id="store-symbol", data="NIFTY50"),

    # ── Header ────────────────────────────────────────────────
    html.Div(style={
        "background": CARD_BG, "borderBottom": f"1px solid {BORDER}",
        "padding": "12px 24px", "display": "flex",
        "justifyContent": "space-between", "alignItems": "center"
    }, children=[
        html.Div([
            html.Span("🤖 ", style={"fontSize": "24px"}),
            html.Span("TRINETRA", style={
                "fontSize": "22px", "fontWeight": "bold",
                "color": GREEN, "letterSpacing": "3px"
            }),
            html.Span(" AI Market Intelligence",
                      style={"color": MUTED, "fontSize": "13px", "marginLeft": "8px"}),
        ]),
        html.Div([
            html.Span(id="market-status", style={"marginRight": "16px", "fontSize": "13px"}),
            html.Span(id="clock", style={"color": MUTED, "fontSize": "13px"}),
        ]),
    ]),

    # ── Body ──────────────────────────────────────────────────
    html.Div(style={"padding": "16px 24px"}, children=[

        # ── Row 1: Price Cards ────────────────────────────────
        html.Div(id="price-cards", style={
            "display": "flex", "gap": "12px",
            "marginBottom": "12px", "flexWrap": "wrap"
        }),

        # ── Row 2: Chart + Signals ────────────────────────────
        html.Div(style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px"}, children=[

            # Chart panel
            card([
                html.Div(style={"display":"flex","justifyContent":"space-between","marginBottom":"12px"}, children=[
                    html.Div([
                        html.Button(sym, id=f"btn-{sym}", n_clicks=0, style={
                            "background": CARD_BG, "color": TEXT,
                            "border": f"1px solid {BORDER}", "borderRadius": "6px",
                            "padding": "6px 14px", "cursor": "pointer",
                            "marginRight": "6px", "fontSize": "13px",
                        }) for sym in SYMBOLS
                    ]),
                    html.Div([
                        html.Button(p, id=f"period-{p}", n_clicks=0, style={
                            "background": CARD_BG, "color": MUTED,
                            "border": f"1px solid {BORDER}", "borderRadius": "6px",
                            "padding": "4px 10px", "cursor": "pointer",
                            "marginLeft": "4px", "fontSize": "12px",
                        }) for p in ["1d","2d","5d"]
                    ]),
                ]),
                dcc.Graph(id="chart-main", config={"displayModeBar": False}),
            ]),

            # Signal panel
            html.Div([
                # Prediction signal
                card([
                    html.Div("🤖 AI PREDICTION", style={"color":MUTED,"fontSize":"11px","marginBottom":"8px","fontWeight":"bold"}),
                    html.Div(id="signal-direction", style={"fontSize":"22px","fontWeight":"bold","marginBottom":"4px"}),
                    html.Div(id="signal-confidence"),
                    html.Hr(style={"borderColor":BORDER,"margin":"10px 0"}),
                    html.Div(id="signal-targets"),
                    html.Hr(style={"borderColor":BORDER,"margin":"10px 0"}),
                    html.Div(id="signal-strategy", style={"color":MUTED,"fontSize":"12px"}),
                ]),

                # Gauge cards
                dcc.Graph(id="gauge-confidence", config={"displayModeBar":False}),
            ]),
        ]),

        # ── Row 3: Indicators + Patterns ──────────────────────
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"12px","marginTop":"0px"}, children=[

            card([
                html.Div("📊 INDICATOR SIGNALS", style={"color":MUTED,"fontSize":"11px","marginBottom":"10px","fontWeight":"bold"}),
                html.Div(id="indicator-list"),
            ]),

            card([
                html.Div("🕯️ CHART PATTERNS", style={"color":MUTED,"fontSize":"11px","marginBottom":"10px","fontWeight":"bold"}),
                html.Div(id="pattern-list"),
            ]),
        ]),

        # ── Row 4: Prediction Log ─────────────────────────────
        card([
            html.Div("📋 PREDICTION LOG", style={"color":MUTED,"fontSize":"11px","marginBottom":"10px","fontWeight":"bold"}),
            html.Div(id="prediction-log"),
        ]),

        # ── Footer ────────────────────────────────────────────
        html.Div("⚠️  Trinetra is an AI tool for educational purposes. Not financial advice. Always do your own research before trading.",
                 style={"color":MUTED,"fontSize":"11px","textAlign":"center","marginTop":"16px","padding":"8px",
                        "border":f"1px solid {BORDER}","borderRadius":"6px"}),
    ]),
])

# ════════════════════════════════════════════════════════════
#  CALLBACKS
# ════════════════════════════════════════════════════════════

# Clock update
@app.callback(Output("clock","children"), Output("market-status","children"),
              Input("refresh-60s","n_intervals"))
def update_clock(_):
    now = datetime.now(IST)
    ts  = now.strftime("%d %b %Y  %H:%M:%S IST")
    wd  = now.weekday()
    h, m = now.hour, now.minute
    is_open = (wd < 5) and (
        (h==9 and m>=15) or (10<=h<=14) or (h==15 and m<=30)
    )
    status = html.Span(
        "● MARKET OPEN" if is_open else "● MARKET CLOSED",
        style={"color": GREEN if is_open else RED, "fontWeight":"bold"}
    )
    return ts, status

# Symbol selector
@app.callback(Output("store-symbol","data"),
              [Input(f"btn-{s}","n_clicks") for s in SYMBOLS],
              prevent_initial_call=True)
def select_symbol(*args):
    ctx = callback_context
    if not ctx.triggered: return "NIFTY50"
    btn_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return btn_id.replace("btn-","")

# Price cards
@app.callback(Output("price-cards","children"),
              Input("refresh-60s","n_intervals"))
def update_prices(_):
    cards = []
    for sym, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="2d", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            price = float(df['close'].iloc[-1])
            prev  = float(df['close'].iloc[-2]) if len(df) > 1 else price
            chg   = (price - prev) / prev * 100
        except:
            price, chg = 0, 0
        cards.append(price_card(sym, price, chg))

    # Add VIX card
    try:
        vix = float(yf.Ticker("^INDIAVIX").fast_info.last_price)
        vix_color = RED if vix > 20 else YELLOW if vix > 15 else GREEN
        cards.append(card([
            html.Div("INDIA VIX", style={"color":MUTED,"fontSize":"12px","fontWeight":"bold"}),
            html.Div(f"{vix:.2f}", style={"color":vix_color,"fontSize":"22px","fontWeight":"bold","margin":"4px 0"}),
            html.Div("FEAR INDEX", style={"color":MUTED,"fontSize":"12px"}),
        ], style={"textAlign":"center","minWidth":"150px"}))
    except: pass

    return cards

# Main chart
@app.callback(Output("chart-main","figure"),
              Input("store-symbol","data"),
              Input("refresh-300s","n_intervals"))
def update_chart(symbol, _):
    df = fetch_candles(symbol, period="2d", interval="5m")
    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=DARK_BG, plot_bgcolor=CARD_BG,
                          font=dict(color=TEXT), height=450)
        return fig
    return make_candlestick(df, symbol)

# Signal panel
@app.callback(
    Output("signal-direction","children"),
    Output("signal-confidence","children"),
    Output("signal-targets","children"),
    Output("signal-strategy","children"),
    Output("gauge-confidence","figure"),
    Input("store-symbol","data"),
    Input("refresh-300s","n_intervals"))
def update_signal(symbol, _):
    log = load_prediction_log()
    if not log.empty:
        sym_log = log[log['symbol']==symbol].tail(1)
        if not sym_log.empty:
            row   = sym_log.iloc[0]
            direc = str(row.get('direction','NEUTRAL'))
            conf  = float(row.get('confidence', 50))
            t20   = row.get('target_20min', 0)
            t30   = row.get('target_30min', 0)
            sl    = row.get('stoploss', 0)
            trade = str(row.get('trade','—'))

            color = GREEN if "BULL" in direc else RED if "BEAR" in direc else YELLOW

            direction_el = html.Span(direc, style={"color": color})
            conf_el = html.Div([
                html.Div(style={
                    "background": f"linear-gradient(90deg, {color} {conf}%, {BORDER} {conf}%)",
                    "height":"8px","borderRadius":"4px","marginTop":"6px",
                }),
                html.Div(f"{conf:.1f}% confidence",
                         style={"color":MUTED,"fontSize":"12px","marginTop":"4px"}),
            ])
            targets_el = html.Div([
                html.Div([html.Span("Target 20m: ",style={"color":MUTED,"fontSize":"12px"}),
                          html.Span(f"₹{t20:,.1f}",style={"color":color,"fontWeight":"bold"})]),
                html.Div([html.Span("Target 30m: ",style={"color":MUTED,"fontSize":"12px"}),
                          html.Span(f"₹{t30:,.1f}",style={"color":color,"fontWeight":"bold"})]),
                html.Div([html.Span("Stop Loss: ",style={"color":MUTED,"fontSize":"12px"}),
                          html.Span(f"₹{sl:,.1f}",style={"color":RED,"fontWeight":"bold"})]),
            ])
            strategy_el = html.Div(f"Strategy: {trade}")
            gauge = make_gauge(conf, "Confidence %", color=color)
            return direction_el, conf_el, targets_el, strategy_el, gauge

    # Default empty state
    return (
        html.Span("No prediction yet", style={"color":MUTED}),
        html.Div(),
        html.Div("Run combined_prediction.py first",
                 style={"color":MUTED,"fontSize":"12px"}),
        html.Div(),
        make_gauge(0, "Confidence %")
    )

# Indicator signals
@app.callback(Output("indicator-list","children"),
              Input("store-symbol","data"),
              Input("refresh-300s","n_intervals"))
def update_indicators(symbol, _):
    try:
        from models.indicator_signals import fetch_with_indicators, get_combined_signal
        df  = fetch_with_indicators(symbol)
        res = get_combined_signal(df, symbol)
        sigs = res.get('signals', [])
        items = []
        for name, bias, strength, note in sigs[:12]:
            color = GREEN if bias=="BULLISH" else RED if bias=="BEARISH" else YELLOW
            items.append(html.Div(style={
                "display":"flex","justifyContent":"space-between",
                "padding":"4px 0","borderBottom":f"1px solid {BORDER}20"
            }, children=[
                html.Span(name, style={"color":TEXT,"fontSize":"12px"}),
                html.Span(bias, style={"color":color,"fontSize":"12px","fontWeight":"bold"}),
                html.Span("⭐"*min(strength,5), style={"fontSize":"10px"}),
            ]))
        score_color = GREEN if res['bull_score'] > res['bear_score'] else RED
        items.append(html.Div(style={"marginTop":"8px","textAlign":"right"}, children=[
            html.Span(f"Bull: {res['bull_score']}  ",style={"color":GREEN,"fontSize":"12px"}),
            html.Span(f"Bear: {res['bear_score']}",style={"color":RED,"fontSize":"12px"}),
        ]))
        return items
    except Exception as e:
        return html.Div(f"Run indicator_signals.py first ({e})", style={"color":MUTED,"fontSize":"12px"})

# Chart patterns
@app.callback(Output("pattern-list","children"),
              Input("store-symbol","data"),
              Input("refresh-300s","n_intervals"))
def update_patterns(symbol, _):
    try:
        from models.pattern_recognition import fetch_candles, get_pattern_signal
        df  = fetch_candles(symbol)
        res = get_pattern_signal(df, symbol)
        pats = res.get('patterns', [])
        if not pats:
            return html.Div("No patterns detected in recent candles",
                           style={"color":MUTED,"fontSize":"12px"})
        items = []
        for p in pats[:10]:
            color = GREEN if p['bias']=="BULLISH" else RED if p['bias']=="BEARISH" else YELLOW
            items.append(html.Div(style={
                "display":"flex","justifyContent":"space-between",
                "padding":"4px 0","borderBottom":f"1px solid {BORDER}20"
            }, children=[
                html.Span(p['pattern'], style={"color":TEXT,"fontSize":"12px"}),
                html.Span(p['bias'], style={"color":color,"fontSize":"12px","fontWeight":"bold"}),
                html.Span("⭐"*p['strength'], style={"fontSize":"10px"}),
            ]))
        return items
    except Exception as e:
        return html.Div(f"Loading patterns... ({e})", style={"color":MUTED,"fontSize":"12px"})

# Prediction log
@app.callback(Output("prediction-log","children"),
              Input("refresh-60s","n_intervals"))
def update_log(_):
    log = load_prediction_log()
    if log.empty:
        return html.Div("No predictions logged yet. Run combined_prediction.py first.",
                       style={"color":MUTED,"fontSize":"12px"})
    rows = []
    for _, row in log.tail(10).iloc[::-1].iterrows():
        direc = str(row.get('direction',''))
        color = GREEN if "BULL" in direc else RED if "BEAR" in direc else YELLOW
        rows.append(html.Div(style={
            "display":"grid",
            "gridTemplateColumns":"120px 100px 100px 80px 100px 100px",
            "padding":"6px 0","borderBottom":f"1px solid {BORDER}20",
            "fontSize":"12px"
        }, children=[
            html.Span(str(row.get('timestamp',''))[-14:-4] if 'timestamp' in row else '—',style={"color":MUTED}),
            html.Span(str(row.get('symbol','—')),style={"color":TEXT,"fontWeight":"bold"}),
            html.Span(direc.replace("🟢","").replace("🔴","").replace("🟡","").strip(),style={"color":color}),
            html.Span(f"{row.get('confidence',0):.1f}%",style={"color":color}),
            html.Span(f"₹{row.get('target_30min',0):,.1f}",style={"color":color}),
            html.Span(f"₹{row.get('stoploss',0):,.1f}",style={"color":RED}),
        ]))
    header = html.Div(style={
        "display":"grid",
        "gridTemplateColumns":"120px 100px 100px 80px 100px 100px",
        "padding":"4px 0","marginBottom":"4px","borderBottom":f"1px solid {BORDER}"
    }, children=[
        html.Span("Time",style={"color":MUTED,"fontSize":"11px"}),
        html.Span("Symbol",style={"color":MUTED,"fontSize":"11px"}),
        html.Span("Direction",style={"color":MUTED,"fontSize":"11px"}),
        html.Span("Conf",style={"color":MUTED,"fontSize":"11px"}),
        html.Span("Target 30m",style={"color":MUTED,"fontSize":"11px"}),
        html.Span("SL",style={"color":MUTED,"fontSize":"11px"}),
    ])
    return [header] + rows

# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🤖 TRINETRA Dashboard starting...")
    print("   Open: http://localhost:8050\n")
    app.run(debug=False, host="0.0.0.0", port=8050)