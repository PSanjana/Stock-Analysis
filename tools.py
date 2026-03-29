from __future__ import annotations

from typing import Any, Dict, List
import statistics

import yfinance as yf


def get_stock_history(ticker: str, period: str = "1mo", interval: str = "1d") -> List[float]:
    """
    Fetch recent close prices for a stock ticker.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)

    if hist.empty or "Close" not in hist.columns:
        raise ValueError(f"No price history found for ticker '{ticker}'.")

    closes = [float(x) for x in hist["Close"].dropna().tolist()]
    if len(closes) < 5:
        raise ValueError(f"Not enough data found for ticker '{ticker}'.")

    return closes


def compute_stock_metrics(prices: List[float]) -> Dict[str, Any]:
    """
    Compute simple stock metrics from close prices.
    """
    if len(prices) < 5:
        raise ValueError("Need at least 5 price points to compute metrics.")

    current_price = prices[-1]
    first_price = prices[0]
    price_5d_ago = prices[-5] if len(prices) >= 5 else prices[0]
    price_20d_ago = prices[-20] if len(prices) >= 20 else prices[0]

    change_pct_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100 if price_5d_ago else 0.0
    change_pct_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100 if price_20d_ago else 0.0

    mean_price = statistics.mean(prices)
    stdev_price = statistics.pstdev(prices) if len(prices) > 1 else 0.0
    volatility = (stdev_price / mean_price) * 100 if mean_price else 0.0

    short_ma = statistics.mean(prices[-5:])
    long_ma = statistics.mean(prices[-20:]) if len(prices) >= 20 else statistics.mean(prices)

    if short_ma > long_ma * 1.01:
        trend = "Upward"
    elif short_ma < long_ma * 0.99:
        trend = "Downward"
    else:
        trend = "Sideways"

    return {
        "current_price": round(current_price, 2),
        "change_pct_5d": round(change_pct_5d, 2),
        "change_pct_20d": round(change_pct_20d, 2),
        "volatility": round(volatility, 2),
        "trend": trend,
    }

def get_stock_news(ticker: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Fetch recent news for a stock ticker using yfinance.
    """
    stock = yf.Ticker(ticker)
    news_items = stock.news or []

    results: List[Dict[str, str]] = []

    for item in news_items[:limit]:
        content = item.get("content", {})

        title = content.get("title", "") or item.get("title", "")
        summary = content.get("summary", "") or item.get("summary", "")

        provider_data = content.get("provider", {})
        if isinstance(provider_data, dict):
            publisher = provider_data.get("displayName", "")
        else:
            publisher = item.get("publisher", "")

        canonical_url = content.get("canonicalUrl", {})
        if isinstance(canonical_url, dict):
            url = canonical_url.get("url", "")
        else:
            url = item.get("link", "")

        results.append(
            {
                "title": title,
                "summary": summary,
                "publisher": publisher,
                "url": url,
            }
        )

    return results



def get_stock_snapshot(ticker: str) -> Dict[str, Any]:
    """
    Convenience wrapper to fetch history and compute metrics.
    """
    prices = get_stock_history(ticker)
    metrics = compute_stock_metrics(prices)
    return {
        "ticker": ticker.upper(),
        "prices": prices,
        "metrics": metrics,
    }