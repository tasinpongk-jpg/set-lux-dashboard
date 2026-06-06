"""
Lux Algo equivalent indicators implemented in Python.

Replicates the core logic of:
- Lux Algo Signals & Overlays (SuperTrend-based Buy/Sell)
- Lux Algo Smart Trail (ATR trailing stop)
- Lux Algo AI Cluster (K-Means classification)
- Lux Algo Oscillator Matrix (composite oscillator)
- Lux Algo Trend Forecaster (EMA channels)
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


# ──────────────────────────────────────────────
# CORE: SuperTrend (foundation of Lux Algo Signals)
# ──────────────────────────────────────────────

def supertrend(df: pd.DataFrame, atr_period: int = 10, factor: float = 3.0) -> pd.DataFrame:
    """
    SuperTrend indicator — the core engine behind Lux Algo Signals & Overlays.
    Returns: upper_band, lower_band, supertrend, direction (1=bull, -1=bear),
             buy_signal, sell_signal
    """
    high, low, close = df["High"], df["Low"], df["Close"]
    hl2 = (high + low) / 2

    # ATR
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=atr_period, adjust=False).mean()

    upper_band = hl2 + factor * atr
    lower_band = hl2 - factor * atr

    supertrend_vals = pd.Series(np.nan, index=df.index)
    direction = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        # Upper band
        if upper_band.iloc[i] < supertrend_vals.iloc[i - 1] or close.iloc[i - 1] > supertrend_vals.iloc[i - 1]:
            upper_band.iloc[i] = upper_band.iloc[i]
        else:
            upper_band.iloc[i] = supertrend_vals.iloc[i - 1]

        # Lower band
        if lower_band.iloc[i] > supertrend_vals.iloc[i - 1] or close.iloc[i - 1] < supertrend_vals.iloc[i - 1]:
            lower_band.iloc[i] = lower_band.iloc[i]
        else:
            lower_band.iloc[i] = supertrend_vals.iloc[i - 1]

        # Direction
        if close.iloc[i] > upper_band.iloc[i]:
            direction.iloc[i] = 1
            supertrend_vals.iloc[i] = lower_band.iloc[i]
        elif close.iloc[i] < lower_band.iloc[i]:
            direction.iloc[i] = -1
            supertrend_vals.iloc[i] = upper_band.iloc[i]
        else:
            direction.iloc[i] = direction.iloc[i - 1]
            supertrend_vals.iloc[i] = supertrend_vals.iloc[i - 1]

    buy_signal = (direction == 1) & (direction.shift(1) == -1)
    sell_signal = (direction == -1) & (direction.shift(1) == 1)

    return pd.DataFrame({
        "st_upper": upper_band,
        "st_lower": lower_band,
        "supertrend": supertrend_vals,
        "st_direction": direction,
        "st_buy": buy_signal,
        "st_sell": sell_signal,
    }, index=df.index)


# ──────────────────────────────────────────────
# Lux Algo Smart Trail (ATR-based adaptive trail)
# ──────────────────────────────────────────────

def smart_trail(df: pd.DataFrame, atr_period: int = 14, factor: float = 2.0) -> pd.DataFrame:
    """
    Lux Algo Smart Trail — adaptive ATR trailing stop.
    Returns trail value and direction.
    """
    close = df["Close"]
    high, low = df["High"], df["Low"]

    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()

    trail = pd.Series(np.nan, index=df.index)
    direction = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        if pd.isna(trail.iloc[i - 1]):
            trail.iloc[i] = close.iloc[i]
            continue

        prev_trail = trail.iloc[i - 1]
        prev_close = close.iloc[i - 1]
        curr_close = close.iloc[i]
        curr_atr = atr.iloc[i]

        if pd.isna(curr_atr):
            trail.iloc[i] = prev_trail
            continue

        stop_dist = factor * curr_atr

        if curr_close > prev_trail:
            trail.iloc[i] = max(prev_trail, curr_close - stop_dist)
            direction.iloc[i] = 1
        elif curr_close < prev_trail:
            trail.iloc[i] = min(prev_trail, curr_close + stop_dist)
            direction.iloc[i] = -1
        else:
            trail.iloc[i] = prev_trail
            direction.iloc[i] = direction.iloc[i - 1]

    buy_cross = (close > trail) & (close.shift(1) <= trail.shift(1))
    sell_cross = (close < trail) & (close.shift(1) >= trail.shift(1))

    return pd.DataFrame({
        "trail": trail,
        "trail_dir": direction,
        "trail_buy": buy_cross,
        "trail_sell": sell_cross,
    }, index=df.index)


# ──────────────────────────────────────────────
# Lux Algo AI Cluster (K-Means classification)
# ──────────────────────────────────────────────

def ai_cluster(df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
    """
    Replicates Lux Algo AI Cluster logic using KMeans on OHLCV features.
    Returns cluster label: 1=bullish, -1=bearish, 0=neutral
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    close = df["Close"]
    high, low = df["High"], df["Low"]
    volume = df.get("Volume", pd.Series(1, index=df.index))

    # Feature engineering (same as Lux Algo's feature set)
    rsi = _rsi(close, 14)
    ema_fast = close.ewm(span=9, adjust=False).mean()
    ema_slow = close.ewm(span=21, adjust=False).mean()
    ema_ratio = (ema_fast / ema_slow - 1) * 100

    atr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1).rolling(14).mean()
    atr_pct = atr / close * 100

    vol_ma = volume.rolling(20).mean()
    vol_ratio = volume / vol_ma.replace(0, np.nan)

    features_df = pd.DataFrame({
        "rsi": rsi,
        "ema_ratio": ema_ratio,
        "atr_pct": atr_pct,
        "vol_ratio": vol_ratio,
    }).dropna()

    cluster_labels = pd.Series(0, index=df.index)

    if len(features_df) < lookback:
        return pd.DataFrame({"cluster": cluster_labels}, index=df.index)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features_df)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled)

    # Identify which cluster is bullish (highest RSI + EMA ratio)
    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    bullish_cluster = int(np.argmax(centers[:, 0] + centers[:, 1]))  # RSI + EMA ratio
    bearish_cluster = int(np.argmin(centers[:, 0] + centers[:, 1]))

    mapped = np.where(labels == bullish_cluster, 1,
              np.where(labels == bearish_cluster, -1, 0))

    cluster_labels.loc[features_df.index] = mapped

    return pd.DataFrame({"cluster": cluster_labels}, index=df.index)


# ──────────────────────────────────────────────
# Lux Algo Oscillator Matrix (composite oscillator)
# ──────────────────────────────────────────────

def oscillator_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replicates Lux Algo Oscillator Matrix — composite of RSI, Stochastic, CCI, MFI.
    Returns a composite score -100 to +100 and signal line.
    """
    close = df["Close"]
    high, low = df["High"], df["Low"]
    volume = df.get("Volume", pd.Series(1, index=df.index))

    # RSI normalized to -100/+100
    rsi = _rsi(close, 14)
    rsi_norm = (rsi - 50) * 2  # -100 to +100

    # Stochastic %K normalized
    low_min = low.rolling(14).min()
    high_max = high.rolling(14).max()
    stoch_k = 100 * (close - low_min) / (high_max - low_min + 1e-10)
    stoch_norm = (stoch_k - 50) * 2

    # CCI
    tp = (high + low + close) / 3
    cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std() + 1e-10)
    cci_norm = cci.clip(-100, 100)

    # MFI
    mfm = ((close - low) - (high - close)) / (high - low + 1e-10)
    mfv = mfm * volume
    mfi_raw = mfv.rolling(14).sum() / volume.rolling(14).sum()
    mfi_norm = mfi_raw * 100

    # Composite (equal weight)
    composite = (rsi_norm + stoch_norm + cci_norm + mfi_norm) / 4

    # Signal line (smoothed)
    signal = composite.ewm(span=9, adjust=False).mean()

    osc_cross_up = (composite > signal) & (composite.shift(1) <= signal.shift(1))
    osc_cross_down = (composite < signal) & (composite.shift(1) >= signal.shift(1))

    return pd.DataFrame({
        "osc_composite": composite,
        "osc_signal": signal,
        "osc_bull": osc_cross_up,
        "osc_bear": osc_cross_down,
        "rsi": rsi,
        "stoch_k": stoch_k,
        "cci": cci,
    }, index=df.index)


# ──────────────────────────────────────────────
# EMA Ribbon (Lux Algo Trend Forecaster base)
# ──────────────────────────────────────────────

def ema_ribbon(df: pd.DataFrame) -> pd.DataFrame:
    """EMA ribbon: 9/21/50/100/200 EMAs for trend strength."""
    close = df["Close"]
    emas = {}
    for p in [9, 21, 50, 100, 200]:
        emas[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()

    result = pd.DataFrame(emas, index=df.index)

    # Ribbon alignment score (how many EMAs are in bull order)
    bull_score = (
        (result["ema_9"] > result["ema_21"]).astype(int) +
        (result["ema_21"] > result["ema_50"]).astype(int) +
        (result["ema_50"] > result["ema_100"]).astype(int) +
        (result["ema_100"] > result["ema_200"]).astype(int)
    )
    result["ribbon_score"] = bull_score  # 0-4, 4=fully bullish

    # Price position vs 200 EMA
    result["above_200"] = (close > result["ema_200"]).astype(int)

    return result


# ──────────────────────────────────────────────
# Volume Analysis
# ──────────────────────────────────────────────

def volume_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Volume surge and OBV trend detection."""
    close = df["Close"]
    volume = df.get("Volume", pd.Series(1, index=df.index))

    vol_ma20 = volume.rolling(20).mean()
    vol_ratio = volume / vol_ma20.replace(0, np.nan)

    # OBV
    direction = np.sign(close.diff())
    obv = (volume * direction).cumsum()
    obv_ema = obv.ewm(span=20, adjust=False).mean()
    obv_trend = (obv > obv_ema).astype(int)

    # Volume surge (>1.5x average = notable, >2x = strong)
    vol_surge = (vol_ratio > 1.5).astype(int)

    return pd.DataFrame({
        "vol_ratio": vol_ratio,
        "vol_surge": vol_surge,
        "obv": obv,
        "obv_trend": obv_trend,
    }, index=df.index)


# ──────────────────────────────────────────────
# MACD
# ──────────────────────────────────────────────

def macd_signal(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    bull_cross = (macd > signal) & (macd.shift(1) <= signal.shift(1))
    bear_cross = (macd < signal) & (macd.shift(1) >= signal.shift(1))

    return pd.DataFrame({
        "macd": macd,
        "macd_signal": signal,
        "macd_hist": hist,
        "macd_bull": bull_cross,
        "macd_bear": bear_cross,
    }, index=df.index)


# ──────────────────────────────────────────────
# MASTER SIGNAL SCORER (combines all Lux Algo signals)
# ──────────────────────────────────────────────

def compute_lux_score(df: pd.DataFrame) -> dict:
    """
    Runs all Lux Algo-equivalent indicators and returns a composite score 0-100
    plus individual signal breakdown for the LATEST bar.
    """
    if len(df) < 50:
        return None

    try:
        st = supertrend(df, atr_period=10, factor=3.0)
        trail = smart_trail(df, atr_period=14, factor=2.0)
        cluster = ai_cluster(df)
        osc = oscillator_matrix(df)
        ribbon = ema_ribbon(df)
        vol = volume_analysis(df)
        macd = macd_signal(df)

        # Get last row of each
        idx = df.index[-1]

        # ── Signal components (each contributes to score) ──

        # 1. SuperTrend direction (35 pts max)
        st_dir = st["st_direction"].iloc[-1]
        st_score = 35 if st_dir == 1 else 0

        # Bonus: recent buy signal (within last 3 bars)
        recent_buy = st["st_buy"].iloc[-3:].any()
        if recent_buy:
            st_score = min(st_score + 15, 50)

        # 2. Smart Trail direction (20 pts max)
        trail_dir = trail["trail_dir"].iloc[-1]
        trail_score = 20 if trail_dir == 1 else 0

        # 3. AI Cluster (15 pts max)
        cluster_val = cluster["cluster"].iloc[-1]
        cluster_score = 15 if cluster_val == 1 else (0 if cluster_val == 0 else -5)

        # 4. Oscillator composite (15 pts max)
        osc_val = osc["osc_composite"].iloc[-1]
        if pd.isna(osc_val):
            osc_score = 7
        elif osc_val > 20:
            osc_score = 15
        elif osc_val > 0:
            osc_score = 10
        elif osc_val > -20:
            osc_score = 5
        else:
            osc_score = 0

        # 5. EMA ribbon (10 pts max)
        ribbon_val = ribbon["ribbon_score"].iloc[-1]
        above_200 = ribbon["above_200"].iloc[-1]
        ribbon_score = int(ribbon_val) * 2 + (2 if above_200 else 0)  # max 10

        # 6. MACD (5 pts max)
        macd_val = macd["macd"].iloc[-1]
        macd_sig_val = macd["macd_signal"].iloc[-1]
        macd_score = 5 if (not pd.isna(macd_val) and macd_val > macd_sig_val) else 0

        # 7. Volume confirmation (5 pts bonus)
        vol_surge = vol["vol_surge"].iloc[-1]
        obv_trend = vol["obv_trend"].iloc[-1]
        vol_score = int(vol_surge) * 3 + int(obv_trend) * 2

        # ── Total score (cap at 100) ──
        total = min(100, max(0, st_score + trail_score + cluster_score + osc_score + ribbon_score + macd_score + vol_score))

        # ── Price metrics ──
        close_last = df["Close"].iloc[-1]
        close_prev = df["Close"].iloc[-2] if len(df) > 1 else close_last
        pct_change = (close_last / close_prev - 1) * 100

        # ── RSI ──
        rsi_val = osc["rsi"].iloc[-1]

        # ── Signal summary ──
        signal_list = []
        if recent_buy:
            signal_list.append("LUX_BUY")
        if trail["trail_buy"].iloc[-3:].any():
            signal_list.append("TRAIL_BUY")
        if cluster_val == 1:
            signal_list.append("AI_BULL_CLUSTER")
        if osc["osc_bull"].iloc[-3:].any():
            signal_list.append("OSC_CROSS_UP")
        if ribbon_val >= 3:
            signal_list.append("EMA_RIBBON_BULL")
        if macd["macd_bull"].iloc[-3:].any():
            signal_list.append("MACD_CROSS")
        if vol_surge:
            signal_list.append("VOL_SURGE")

        # ── Trend label ──
        if total >= 75:
            trend = "STRONG BUY"
        elif total >= 55:
            trend = "BUY"
        elif total >= 40:
            trend = "NEUTRAL"
        elif total >= 25:
            trend = "SELL"
        else:
            trend = "STRONG SELL"

        # ── Support/Resistance ──
        support = df["Low"].rolling(20).min().iloc[-1]
        resistance = df["High"].rolling(20).max().iloc[-1]

        return {
            "score": round(total, 1),
            "trend": trend,
            "close": round(close_last, 2),
            "pct_change_1d": round(pct_change, 2),
            "rsi": round(rsi_val, 1) if not pd.isna(rsi_val) else None,
            "supertrend_dir": "BULL" if st_dir == 1 else "BEAR",
            "trail_dir": "BULL" if trail_dir == 1 else "BEAR",
            "ai_cluster": {1: "BULL", -1: "BEAR", 0: "NEUTRAL"}.get(cluster_val, "NEUTRAL"),
            "osc_composite": round(osc_val, 1) if not pd.isna(osc_val) else None,
            "ema_ribbon": f"{int(ribbon_val)}/4",
            "macd_bull": bool(macd_val > macd_sig_val) if not (pd.isna(macd_val) or pd.isna(macd_sig_val)) else False,
            "vol_surge": bool(vol_surge),
            "signals": signal_list,
            "support": round(support, 2) if not pd.isna(support) else None,
            "resistance": round(resistance, 2) if not pd.isna(resistance) else None,
            "score_breakdown": {
                "supertrend": st_score,
                "smart_trail": trail_score,
                "ai_cluster": cluster_score,
                "oscillator": osc_score,
                "ema_ribbon": ribbon_score,
                "macd": macd_score,
                "volume": vol_score,
            }
        }

    except Exception as e:
        return None


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
