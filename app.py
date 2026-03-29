# from __future__ import annotations

# import os
# import streamlit as st
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI

# st.set_page_config(page_title="Stock Agent", page_icon="📈", layout="wide")
# st.title("📈 Stock Research & Recommendation Agent")

# try:
#     load_dotenv()
#     st.write("App started successfully.")
    
#     from graph import build_graph

#     api_key = os.getenv("OPENAI_API_KEY")
#     model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

#     if not api_key:
#         st.error("OPENAI_API_KEY is missing in .env")
#         st.stop()

#     llm = ChatOpenAI(
#         model=model_name,
#         temperature=0.2,
#     )

#     graph = build_graph(llm)

#     query = st.text_input("Enter your query", value="Should I buy TSLA?")

#     if st.button("Analyze"):
#         with st.spinner("Analyzing..."):
#             result = graph.invoke({"query": query})
#         st.text_area("Result", value=result.get("final_response", "No response"), height=500)

# except Exception as e:
#     st.error(f"App crashed: {e}")
#     st.exception(e)



from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from graph import build_graph


@st.cache_resource
def get_graph():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,
    )

    return build_graph(llm)


def main() -> None:
    st.set_page_config(
        page_title="Stock Research & Recommendation Agent",
        page_icon="📈",
        layout="wide",
    )

    st.title("📈 Stock Research & Recommendation Agent")

    with st.sidebar:
        st.header("Investor Profile")

        risk_appetite = st.selectbox(
            "Risk Appetite",
            ["low", "medium", "high"],
            index=0,
        )

        investment_horizon = st.selectbox(
            "Investment Horizon",
            ["short_term", "medium_term", "long_term"],
            index=2,
        )

        preferred_sectors = st.multiselect(
            "Preferred Sectors",
            ["technology", "healthcare", "finance", "energy", "consumer", "industrial"],
            default=["technology", "healthcare"],
        )

        avoid_sectors = st.multiselect(
            "Avoid Sectors",
            ["crypto", "technology", "healthcare", "finance", "energy", "consumer", "industrial"],
            default=["crypto"],
        )

        investing_style = st.selectbox(
            "Investing Style",
            ["conservative", "balanced", "aggressive"],
            index=0,
        )

    query = st.text_input("Enter your query", value="Should I buy TSLA?")

    if st.button("Analyze"):
        if not query.strip():
            st.warning("Please enter a query.")
            return

        user_profile = {
            "risk_appetite": risk_appetite,
            "investment_horizon": investment_horizon,
            "preferred_sectors": preferred_sectors,
            "avoid_sectors": avoid_sectors,
            "investing_style": investing_style,
        }

        try:
            graph = get_graph()

            with st.spinner("Analyzing..."):
                result = graph.invoke({
                    "query": query.strip(),
                    "user_profile": user_profile,
                })

            st.text_area(
                "Result",
                value=result.get("final_response", "No response generated."),
                height=500,
            )

        except Exception as exc:
            st.error(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()