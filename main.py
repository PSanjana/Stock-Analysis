from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from graph import build_graph


def main() -> None:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,
    )

    graph = build_graph(llm)

    print("Stock Research & Recommendation Agent")
    print("Examples:")
    print("- Analyze AAPL")
    print("- Should I buy TSLA?")
    print("- Compare NVDA and AMD")
    print("- Type 'exit' to quit\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        result = graph.invoke({"query": query})
        print("\nAssistant:")
        print(result.get("final_response", "No response generated."))
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()