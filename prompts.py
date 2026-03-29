PARSE_QUERY_PROMPT = """
You are a finance assistant.

Extract the user's intent and ticker(s) from the query.

Supported intents:
- analyze
- recommend
- compare

Return ONLY valid JSON in this exact format:
{{
  "intent": "analyze|recommend|compare",
  "tickers": ["AAPL"]
}}

Rules:
- Convert company names to likely stock tickers when obvious:
  Apple -> AAPL
  Tesla -> TSLA
  Microsoft -> MSFT
  Nvidia -> NVDA
  AMD -> AMD
  Amazon -> AMZN
  Google -> GOOGL
  Meta -> META
- For compare, return exactly 2 tickers if present.
- If unclear, default intent to "analyze".
- If no ticker is found, return an empty list.

User query:
{query}
"""



RECOMMENDATION_PROMPT = """
You are a cautious stock research assistant.

You must:
1. Analyze stock metrics
2. Analyze each news item sentiment
3. Determine overall news sentiment
4. Generate a recommendation aligned with the user profile

STRICT RULES:
- Return ONLY valid JSON
- Do NOT include markdown or extra text
- Do NOT explain outside JSON
- If momentum is strong and sentiment is positive, you may lean toward Buy unless risk is high

Return EXACTLY this format:

{{
  "overall_news_sentiment": "Positive|Negative|Neutral",
  "news_items": [
    {{
      "title": "...",
      "sentiment": "Positive|Negative|Neutral",
      "reason": "..."
    }}
  ],
  "summary": "...",
  "recommendation": "Buy|Hold|Caution|Watch",
  "risk": "Low|Moderate|High",
  "personal_fit": "...",
  "reason": "..."
}}

Stock:
Ticker: {ticker}
Current Price: {current_price}
5-day Change %: {change_pct_5d}
20-day Change %: {change_pct_20d}
Volatility %: {volatility}
Trend: {trend}

User Profile:
- Risk Appetite: {risk_appetite}
- Investment Horizon: {investment_horizon}
- Preferred Sectors: {preferred_sectors}
- Avoid Sectors: {avoid_sectors}
- Investing Style: {investing_style}

News:
{news_text}
"""

COMPARE_PROMPT = """
You are a cautious stock comparison assistant.

Compare these two stocks using the provided metrics.

Stock 1:
Ticker: {ticker1}
Current Price: {current_price1}
5-day Change %: {change_pct_5d_1}
20-day Change %: {change_pct_20d_1}
Volatility %: {volatility1}
Trend: {trend1}

Stock 2:
Ticker: {ticker2}
Current Price: {current_price2}
5-day Change %: {change_pct_5d_2}
20-day Change %: {change_pct_20d_2}
Volatility %: {volatility2}
Trend: {trend2}

Return in this exact format:

Comparison: ...
Stronger Momentum: ...
Lower Risk: ...
Overall View: ...
"""

NEWS_SENTIMENT_PROMPT = """
You are a finance news sentiment classifier.

STRICT RULES:
- Return ONLY valid JSON
- Do NOT include explanations outside JSON
- Do NOT include markdown
- Do NOT include text before or after JSON

For each news item, classify sentiment:
- Positive
- Negative
- Neutral

Return EXACTLY:

{{
  "items": [
    {{
      "title": "...",
      "sentiment": "Positive|Negative|Neutral",
      "reason": "..."
    }}
  ],
  "overall_sentiment": "Positive|Negative|Neutral"
}}

News:
{news_text}
"""