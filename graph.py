# from __future__ import annotations

# import json
# import re
# from typing import Any, Dict, List, Literal, TypedDict

# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, START, END

# from prompts import (
#     PARSE_QUERY_PROMPT,
#     RECOMMENDATION_PROMPT,
#     COMPARE_PROMPT,
# )
# from tools import get_stock_snapshot, get_stock_news, label_news_sentiments


# class AgentState(TypedDict, total=False):
#     query: str
#     intent: Literal["analyze", "recommend", "compare"]
#     tickers: List[str]
#     stock_data: Dict[str, Any]
#     comparison_data: Dict[str, Any]
#     news_data: List[Dict[str, str]]
#     user_profile: Dict[str, Any]
#     final_response: str
#     error: str


# KNOWN_COMPANY_TO_TICKER = {
#     "apple": "AAPL",
#     "tesla": "TSLA",
#     "microsoft": "MSFT",
#     "nvidia": "NVDA",
#     "amd": "AMD",
#     "amazon": "AMZN",
#     "google": "GOOGL",
#     "alphabet": "GOOGL",
#     "meta": "META",
#     "netflix": "NFLX",
# }


# def safe_json_extract(text: str) -> Dict[str, Any]:
#     text = text.strip()
#     text = re.sub(r"```json|```", "", text).strip()

#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         pass

#     match = re.search(r"\{.*\}", text, re.DOTALL)
#     if match:
#         try:
#             return json.loads(match.group(0))
#         except json.JSONDecodeError:
#             pass

#     return {}


# def fallback_parse_query(query: str) -> Dict[str, Any]:
#     lowered = query.lower()

#     if "compare" in lowered:
#         intent = "compare"
#     elif "recommend" in lowered or "should i buy" in lowered or "buy" in lowered:
#         intent = "recommend"
#     else:
#         intent = "analyze"

#     # tickers = re.findall(r"\b[A-Z]{1,5}\b", query)
#     tickers = re.findall(r"\b[A-Z]{2,5}\b", query)
#     tickers = [t for t in tickers if t not in {"BUY", "NOW"}]
#     tickers = [t.upper() for t in tickers]

#     if not tickers:
#         for company, ticker in KNOWN_COMPANY_TO_TICKER.items():
#             if company in lowered:
#                 tickers.append(ticker)

#     seen = set()
#     unique_tickers = []
#     for t in tickers:
#         if t not in seen:
#             unique_tickers.append(t)
#             seen.add(t)

#     if intent == "compare":
#         unique_tickers = unique_tickers[:2]
#     else:
#         unique_tickers = unique_tickers[:1]

#     return {"intent": intent, "tickers": unique_tickers}


# def parse_query_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
#     query = state["query"]

#     try:
#         response = llm.invoke(PARSE_QUERY_PROMPT.format(query=query))
#         parsed = safe_json_extract(response.content)

#         if not parsed or "intent" not in parsed or "tickers" not in parsed:
#             raise ValueError("Invalid response from LLM")

#     except Exception as e:
#         print(f"Error in parse_query_node: {e}")
#         parsed = fallback_parse_query(query)

#     intent = parsed.get("intent", "analyze")
#     tickers = parsed.get("tickers", [])

#     if not tickers:
#         return {"error": "I could not identify a stock ticker from your query."}

#     return {
#         "intent": intent,
#         "tickers": tickers,
#     }


# def route_after_parse(state: AgentState) -> str:
#     if state.get("error"):
#         return "error"
#     if state.get("intent") == "compare":
#         return "fetch_compare"
#     return "fetch_single"


# def fetch_single_stock_node(state: AgentState) -> AgentState:
#     ticker = state["tickers"][0]
#     try:
#         snapshot = get_stock_snapshot(ticker)
#         return {"stock_data": snapshot}
#     except Exception as exc:
#         return {"error": str(exc)}


# def fetch_compare_stock_node(state: AgentState) -> AgentState:
#     tickers = state["tickers"]
#     if len(tickers) < 2:
#         return {"error": "Comparison needs two stock tickers."}

#     try:
#         first = get_stock_snapshot(tickers[0])
#         second = get_stock_snapshot(tickers[1])
#         return {
#             "comparison_data": {
#                 "first": first,
#                 "second": second,
#             }
#         }
#     except Exception as exc:
#         return {"error": str(exc)}


# def fetch_news_node(state: AgentState) -> AgentState:
#     ticker = state["tickers"][0]
#     try:
#         news = get_stock_news(ticker, limit=5)
#         return {"news_data": news}
#     except Exception as exc:
#         return {"error": str(exc)}


# def load_user_profile_node(state: AgentState) -> AgentState:
#     profile = {
#         "risk_appetite": "low",
#         "investment_horizon": "long_term",
#         "preferred_sectors": ["technology", "healthcare"],
#         "avoid_sectors": ["crypto"],
#         "investing_style": "conservative",
#     }
#     return {"user_profile": profile}


# def format_news_text(news_items: List[Dict[str, str]]) -> str:
#     if not news_items:
#         return "No recent news available."

#     lines = []
#     for idx, item in enumerate(news_items, start=1):
#         title = item.get("title", "").strip() or "No title"
#         summary = item.get("summary", "").strip() or "No summary available"
#         publisher = item.get("publisher", "").strip()

#         if publisher:
#             lines.append(f"{idx}. {title} ({publisher}) - {summary}")
#         else:
#             lines.append(f"{idx}. {title} - {summary}")

#     return "\n".join(lines)


# def analyze_single_stock_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
#     if "stock_data" not in state:
#         return {"final_response": "Error: stock data could not be fetched."}
#     snapshot = state["stock_data"]
#     ticker = snapshot["ticker"]
#     metrics = snapshot["metrics"]
#     news_items = state.get("news_data", [])
#     news_text = format_news_text(news_items)

#     profile = state.get("user_profile", {})
#     risk_appetite = profile.get("risk_appetite", "unknown")
#     investment_horizon = profile.get("investment_horizon", "unknown")
#     preferred_sectors = ", ".join(profile.get("preferred_sectors", [])) or "none"
#     avoid_sectors = ", ".join(profile.get("avoid_sectors", [])) or "none"
#     investing_style = profile.get("investing_style", "unknown")

#     prompt = RECOMMENDATION_PROMPT.format(
#         ticker=ticker,
#         current_price=metrics["current_price"],
#         change_pct_5d=metrics["change_pct_5d"],
#         change_pct_20d=metrics["change_pct_20d"],
#         volatility=metrics["volatility"],
#         trend=metrics["trend"],
#         news_text=news_text,
#         risk_appetite=risk_appetite,
#         investment_horizon=investment_horizon,
#         preferred_sectors=preferred_sectors,
#         avoid_sectors=avoid_sectors,
#         investing_style=investing_style,
#     )

#     response = llm.invoke(prompt)

#     final = (
#         f"Ticker: {ticker}\n"
#         f"Current Price: ${metrics['current_price']}\n"
#         f"5-day Change: {metrics['change_pct_5d']}%\n"
#         f"20-day Change: {metrics['change_pct_20d']}%\n"
#         f"Volatility: {metrics['volatility']}%\n"
#         f"Trend: {metrics['trend']}\n\n"
#         f"User Profile:\n"
#         f"- Risk Appetite: {risk_appetite}\n"
#         f"- Investment Horizon: {investment_horizon}\n"
#         f"- Preferred Sectors: {preferred_sectors}\n"
#         f"- Avoid Sectors: {avoid_sectors}\n"
#         f"- Investing Style: {investing_style}\n\n"
#         f"Recent News:\n{news_text}\n\n"
#         f"{response.content}"
#     )

#     return {"final_response": final}


# def analyze_compare_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
#     first = state["comparison_data"]["first"]
#     second = state["comparison_data"]["second"]

#     m1 = first["metrics"]
#     m2 = second["metrics"]

#     prompt = COMPARE_PROMPT.format(
#         ticker1=first["ticker"],
#         current_price1=m1["current_price"],
#         change_pct_5d_1=m1["change_pct_5d"],
#         change_pct_20d_1=m1["change_pct_20d"],
#         volatility1=m1["volatility"],
#         trend1=m1["trend"],
#         ticker2=second["ticker"],
#         current_price2=m2["current_price"],
#         change_pct_5d_2=m2["change_pct_5d"],
#         change_pct_20d_2=m2["change_pct_20d"],
#         volatility2=m2["volatility"],
#         trend2=m2["trend"],
#     )

#     response = llm.invoke(prompt)

#     final = (
#         f"Stock 1: {first['ticker']}\n"
#         f"- Current Price: ${m1['current_price']}\n"
#         f"- 5-day Change: {m1['change_pct_5d']}%\n"
#         f"- 20-day Change: {m1['change_pct_20d']}%\n"
#         f"- Volatility: {m1['volatility']}%\n"
#         f"- Trend: {m1['trend']}\n\n"
#         f"Stock 2: {second['ticker']}\n"
#         f"- Current Price: ${m2['current_price']}\n"
#         f"- 5-day Change: {m2['change_pct_5d']}%\n"
#         f"- 20-day Change: {m2['change_pct_20d']}%\n"
#         f"- Volatility: {m2['volatility']}%\n"
#         f"- Trend: {m2['trend']}\n\n"
#         f"{response.content}"
#     )

#     return {"final_response": final}


# def error_node(state: AgentState) -> AgentState:
#     return {"final_response": f"Error: {state.get('error', 'Unknown error')}"}


# def build_graph(llm: ChatOpenAI):
#     builder = StateGraph(AgentState)

#     builder.add_node("parse_query", lambda state: parse_query_node(state, llm))
#     builder.add_node("fetch_single", fetch_single_stock_node)
#     builder.add_node("fetch_compare", fetch_compare_stock_node)
#     builder.add_node("fetch_news", fetch_news_node)
#     builder.add_node("load_profile", load_user_profile_node)
#     builder.add_node("analyze_single", lambda state: analyze_single_stock_node(state, llm))
#     builder.add_node("analyze_compare", lambda state: analyze_compare_node(state, llm))
#     builder.add_node("error", error_node)

#     builder.add_edge(START, "parse_query")
#     builder.add_conditional_edges(
#         "parse_query",
#         route_after_parse,
#         {
#             "fetch_single": "fetch_single",
#             "fetch_compare": "fetch_compare",
#             "error": "error",
#         },
#     )

#     builder.add_conditional_edges(
#         "fetch_single",
#         route_after_data_fetch,
#         {
#             "next": "fetch_news",
#             "error": "error",
#         },
#     )

#     builder.add_conditional_edges(
#         "fetch_news",
#         route_after_data_fetch,
#         {
#             "next": "load_profile",
#             "error": "error",
#         },
#     )

#     builder.add_edge("load_profile", "analyze_single")

#     builder.add_edge("fetch_compare", "analyze_compare")
#     builder.add_edge("analyze_single", END)
#     builder.add_edge("analyze_compare", END)
#     builder.add_edge("error", END)

#     return builder.compile()

# def route_after_data_fetch(state: AgentState) -> str:
#     if state.get("error"):
#         return "error"
#     return "next"

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from prompts import (
    PARSE_QUERY_PROMPT,
    RECOMMENDATION_PROMPT,
    COMPARE_PROMPT,
    NEWS_SENTIMENT_PROMPT,
)
from tools import get_stock_snapshot, get_stock_news


class AgentState(TypedDict, total=False):
    query: str
    intent: Literal["analyze", "recommend", "compare"]
    tickers: List[str]
    stock_data: Dict[str, Any]
    comparison_data: Dict[str, Any]
    news_data: List[Dict[str, str]]
    user_profile: Dict[str, Any]
    final_response: str
    error: str


KNOWN_COMPANY_TO_TICKER = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "amd": "AMD",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "netflix": "NFLX",
    "salesforce": "CRM",
}


def safe_json_extract(text: str) -> Dict[str, Any]:
    text = text.strip()
    text = re.sub(r"```json|```", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def fallback_parse_query(query: str) -> Dict[str, Any]:
    lowered = query.lower()

    if "compare" in lowered:
        intent = "compare"
    elif "recommend" in lowered or "should i buy" in lowered or "buy" in lowered:
        intent = "recommend"
    else:
        intent = "analyze"

    tickers = re.findall(r"\b[A-Z]{2,5}\b", query)
    tickers = [t.upper() for t in tickers if t not in {"BUY", "NOW"}]

    if not tickers:
        for company, ticker in KNOWN_COMPANY_TO_TICKER.items():
            if company in lowered:
                tickers.append(ticker)

    seen = set()
    unique_tickers = []
    for t in tickers:
        if t not in seen:
            unique_tickers.append(t)
            seen.add(t)

    if intent == "compare":
        unique_tickers = unique_tickers[:2]
    else:
        unique_tickers = unique_tickers[:1]

    return {"intent": intent, "tickers": unique_tickers}


def parse_query_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    query = state["query"]

    try:
        response = llm.invoke(PARSE_QUERY_PROMPT.format(query=query))
        parsed = safe_json_extract(response.content)

        if not parsed or "intent" not in parsed or "tickers" not in parsed:
            raise ValueError("Invalid response from LLM")

    except Exception as e:
        print(f"Error in parse_query_node: {e}")
        parsed = fallback_parse_query(query)

    intent = parsed.get("intent", "analyze")
    tickers = parsed.get("tickers", [])

    if not tickers:
        return {"error": "I could not identify a stock ticker from your query."}

    return {
        "intent": intent,
        "tickers": tickers,
    }


def route_after_parse(state: AgentState) -> str:
    if state.get("error"):
        return "error"
    if state.get("intent") == "compare":
        return "fetch_compare"
    return "fetch_single"


def route_if_error_else_next(state: AgentState) -> str:
    if state.get("error"):
        return "error"
    return "next"


def fetch_single_stock_node(state: AgentState) -> AgentState:
    ticker = state["tickers"][0]
    try:
        snapshot = get_stock_snapshot(ticker)
        return {"stock_data": snapshot}
    except Exception as exc:
        return {"error": str(exc)}


def fetch_compare_stock_node(state: AgentState) -> AgentState:
    tickers = state["tickers"]
    if len(tickers) < 2:
        return {"error": "Comparison needs two stock tickers."}

    try:
        first = get_stock_snapshot(tickers[0])
        second = get_stock_snapshot(tickers[1])
        return {
            "comparison_data": {
                "first": first,
                "second": second,
            }
        }
    except Exception as exc:
        return {"error": str(exc)}


def fetch_news_node(state: AgentState) -> AgentState:
    ticker = state["tickers"][0]
    try:
        news = get_stock_news(ticker, limit=5)
        return {"news_data": news}
    except Exception as exc:
        return {"error": str(exc)}


def load_user_profile_node(state: AgentState) -> AgentState:
    if state.get("user_profile"):
        return {"user_profile": state["user_profile"]}

    profile = {
        "risk_appetite": "low",
        "investment_horizon": "long_term",
        "preferred_sectors": ["technology", "healthcare"],
        "avoid_sectors": ["crypto"],
        "investing_style": "conservative",
    }
    return {"user_profile": profile}


def format_news_for_llm(news_items: List[Dict[str, str]]) -> str:
    if not news_items:
        return "No recent news available."

    blocks = []
    for idx, item in enumerate(news_items, start=1):
        title = item.get("title", "").strip() or "No title"
        summary = item.get("summary", "").strip() or "No summary available"
        publisher = item.get("publisher", "").strip()

        block = f"{idx}. Title: {title}\nSummary: {summary}"
        if publisher:
            block += f"\nPublisher: {publisher}"

        blocks.append(block)

    return "\n\n".join(blocks)

# def label_news_sentiment_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
#     news_items = state.get("news_data", [])

#     if not news_items:
#         return {
#             "labeled_news": [],
#             "overall_news_sentiment": "Neutral",
#         }

#     news_text = format_news_for_llm(news_items)

#     try:
#         prom = NEWS_SENTIMENT_PROMPT.format(news_text=news_text)
#         response = llm.invoke(prom)
#         # print("\n===== RAW NEWS SENTIMENT RESPONSE =====")
#         # print(response.content)
#         # print("=======================================\n")
#         parsed = safe_json_extract(response.content)

#         items = parsed.get("items", [])
#         overall_sentiment = parsed.get("overall_sentiment", "Neutral")

#         labeled_news = []
#         for original_item, labeled_item in zip(news_items, items):
#             labeled_news.append(
#                 {
#                     **original_item,
#                     "sentiment": labeled_item.get("sentiment", "Neutral"),
#                     "reason": labeled_item.get("reason", "No reason provided."),
#                 }
#             )

#         if not labeled_news:
#             labeled_news = [
#                 {
#                     **item,
#                     "sentiment": "Neutral",
#                     "reason": "Sentiment classification unavailable.",
#                 }
#                 for item in news_items
#             ]
#             overall_sentiment = "Neutral"

#         return {
#             "labeled_news": labeled_news,
#             "overall_news_sentiment": overall_sentiment,
#         }

#     except Exception as exc:
#         print(f"Error in label_news_sentiment_node: {exc}")
#         return {
#             "labeled_news": [
#                 {
#                     **item,
#                     "sentiment": "Neutral",
#                     "reason": "Sentiment classification failed.",
#                 }
#                 for item in news_items
#             ],
#             "overall_news_sentiment": "Neutral",
#         }


def format_news_text(news_items: List[Dict[str, str]]) -> str:
    if not news_items:
        return "No recent news available."

    lines = []
    for idx, item in enumerate(news_items, start=1):
        title = item.get("title", "").strip() or "No title"
        summary = item.get("summary", "").strip() or "No summary available"
        publisher = item.get("publisher", "").strip()
        sentiment = item.get("sentiment", "Unknown").strip()
        reason = item.get("reason", "").strip()

        if publisher:
            line = f"{idx}. {title} ({publisher}) [{sentiment}] - {summary}"
        else:
            line = f"{idx}. {title} [{sentiment}] - {summary}"

        if reason:
            line += f" | Reason: {reason}"

        lines.append(line)

    return "\n".join(lines)


def analyze_single_stock_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    if "stock_data" not in state:
        return {"final_response": "Error: stock data could not be fetched."}

    snapshot = state["stock_data"]
    ticker = snapshot["ticker"]
    metrics = snapshot["metrics"]

    news_items = state.get("news_data", [])
    news_text = format_news_for_llm(news_items)

    profile = state.get("user_profile", {})
    risk_appetite = profile.get("risk_appetite", "unknown")
    investment_horizon = profile.get("investment_horizon", "unknown")
    preferred_sectors = ", ".join(profile.get("preferred_sectors", [])) or "none"
    avoid_sectors = ", ".join(profile.get("avoid_sectors", [])) or "none"
    investing_style = profile.get("investing_style", "unknown")

    prompt = RECOMMENDATION_PROMPT.format(
        ticker=ticker,
        current_price=metrics["current_price"],
        change_pct_5d=metrics["change_pct_5d"],
        change_pct_20d=metrics["change_pct_20d"],
        volatility=metrics["volatility"],
        trend=metrics["trend"],
        news_text=news_text,
        risk_appetite=risk_appetite,
        investment_horizon=investment_horizon,
        preferred_sectors=preferred_sectors,
        avoid_sectors=avoid_sectors,
        investing_style=investing_style,
    )

    response = llm.invoke(prompt)

    # Debug (optional)
    # print("\n===== FINAL LLM RESPONSE =====")
    # print(response.content)
    # print("=============================\n")

    parsed = safe_json_extract(response.content)

    if not parsed:
        return {"final_response": "Error: Could not parse LLM response."}

    # Extract fields
    overall_sentiment = parsed.get("overall_news_sentiment", "Unknown")
    news_items_labeled = parsed.get("news_items", [])
    summary = parsed.get("summary", "")
    recommendation = parsed.get("recommendation", "")
    risk = parsed.get("risk", "")
    personal_fit = parsed.get("personal_fit", "")
    reason = parsed.get("reason", "")

    # Format news output
    news_lines = []
    for item in news_items_labeled:
        title = item.get("title", "")
        sentiment = item.get("sentiment", "")
        r = item.get("reason", "")
        news_lines.append(f"- {title} [{sentiment}] | {r}")

    news_output = "\n".join(news_lines)

    final = (
        f"Ticker: {ticker}\n"
        f"Current Price: ${metrics['current_price']}\n"
        f"5-day Change: {metrics['change_pct_5d']}%\n"
        f"20-day Change: {metrics['change_pct_20d']}%\n"
        f"Volatility: {metrics['volatility']}%\n"
        f"Trend: {metrics['trend']}\n\n"
        f"Overall News Sentiment: {overall_sentiment}\n\n"
        f"News Analysis:\n{news_output}\n\n"
        f"Summary: {summary}\n"
        f"Recommendation: {recommendation}\n"
        f"Risk: {risk}\n"
        f"Personal Fit: {personal_fit}\n"
        f"Reason: {reason}"
    )

    return {"final_response": final}

def analyze_compare_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    first = state["comparison_data"]["first"]
    second = state["comparison_data"]["second"]

    m1 = first["metrics"]
    m2 = second["metrics"]

    prompt = COMPARE_PROMPT.format(
        ticker1=first["ticker"],
        current_price1=m1["current_price"],
        change_pct_5d_1=m1["change_pct_5d"],
        change_pct_20d_1=m1["change_pct_20d"],
        volatility1=m1["volatility"],
        trend1=m1["trend"],
        ticker2=second["ticker"],
        current_price2=m2["current_price"],
        change_pct_5d_2=m2["change_pct_5d"],
        change_pct_20d_2=m2["change_pct_20d"],
        volatility2=m2["volatility"],
        trend2=m2["trend"],
    )

    response = llm.invoke(prompt)

    final = (
        f"Stock 1: {first['ticker']}\n"
        f"- Current Price: ${m1['current_price']}\n"
        f"- 5-day Change: {m1['change_pct_5d']}%\n"
        f"- 20-day Change: {m1['change_pct_20d']}%\n"
        f"- Volatility: {m1['volatility']}%\n"
        f"- Trend: {m1['trend']}\n\n"
        f"Stock 2: {second['ticker']}\n"
        f"- Current Price: ${m2['current_price']}\n"
        f"- 5-day Change: {m2['change_pct_5d']}%\n"
        f"- 20-day Change: {m2['change_pct_20d']}%\n"
        f"- Volatility: {m2['volatility']}%\n"
        f"- Trend: {m2['trend']}\n\n"
        f"{response.content}"
    )

    return {"final_response": final}


def error_node(state: AgentState) -> AgentState:
    return {"final_response": f"Error: {state.get('error', 'Unknown error')}"}


def build_graph(llm: ChatOpenAI):
    builder = StateGraph(AgentState)

    builder.add_node("parse_query", lambda state: parse_query_node(state, llm))
    builder.add_node("fetch_single", fetch_single_stock_node)
    builder.add_node("fetch_compare", fetch_compare_stock_node)
    builder.add_node("fetch_news", fetch_news_node)
    # builder.add_node("label_news_sentiment", lambda state: label_news_sentiment_node(state, llm))
    builder.add_node("load_profile", load_user_profile_node)
    builder.add_node("analyze_single", lambda state: analyze_single_stock_node(state, llm))
    builder.add_node("analyze_compare", lambda state: analyze_compare_node(state, llm))
    builder.add_node("error", error_node)

    builder.add_edge(START, "parse_query")
    builder.add_conditional_edges(
        "parse_query",
        route_after_parse,
        {
            "fetch_single": "fetch_single",
            "fetch_compare": "fetch_compare",
            "error": "error",
        },
    )

    builder.add_conditional_edges(
        "fetch_single",
        route_if_error_else_next,
        {
            "next": "fetch_news",
            "error": "error",
        },
    )

    builder.add_conditional_edges(
        "fetch_news",
        route_if_error_else_next,
        {
            "next": "load_profile",
            "error": "error",
        },
    )

    # builder.add_edge("label_news_sentiment", "load_profile")
    builder.add_edge("load_profile", "analyze_single")

    builder.add_edge("fetch_compare", "analyze_compare")
    builder.add_edge("analyze_single", END)
    builder.add_edge("analyze_compare", END)
    builder.add_edge("error", END)

    return builder.compile()