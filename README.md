# AI-Powered Stock Research & Recommendation Agent

An intelligent stock analysis system that combines near real-time market data, news sentiment analysis, and user-specific investment preferences to generate structured, explainable investment insights.

Built using LangChain, LangGraph, and LLMs, the system acts as a tool-using AI agent capable of processing natural language queries and producing context-aware recommendations.

## Features

**Natural Language Queries**

  Ask questions like:
  
  “Should I buy TSLA?”
  
  “Analyze AAPL”
  
  “Compare NVDA and AMD”
  
 **Market Data Analysis**

  Fetches near real-time stock data using yfinance
  
  Computes:
  
  - itemPrice changes (5-day, 20-day)
  - item Volatility
  - item Moving average-based trend
    
**News Sentiment Analysis**

  Retrieves recent news articles
  
  Uses LLM to:   
    
- item classify sentiment per article
- derive overall sentiment
- provide reasoning
  
**User Personalization**

  Incorporates
- item risk appetite
- item investment horizon
- item preferred/avoided sectors
- item investing style
    
  Generates recommendations aligned with user profile
  
**AI Agent Workflow (LangGraph)**

Structured multi-step pipeline:

Query → Parse → Fetch Data → Fetch News → Load Profile → Analyze → Output

**Streamlit UI**
Interactive interface for real-time querying and analysis

## Technologies Used

LangChain – LLM interaction and prompt handling

LangGraph – Workflow orchestration and state management

OpenAI (GPT-4o-mini) – Core reasoning engine

yfinance – Market data and news

Streamlit – Frontend UI

Python – Core implementation

