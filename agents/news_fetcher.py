import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
import json
from dotenv import load_dotenv
from tools.search_news import search_news, get_top_geopolitical_news

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def fetch_news_for_query(user_query: str) -> dict:
    print(f"[NewsFetcherAgent] Processing: '{user_query}'")

    # Step 1 - Ask Groq what to search for
    planning_response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a news intelligence agent.
Given a geopolitical query, generate 3 specific search queries to find relevant news.
Respond ONLY with a JSON array of 3 strings. No extra text.
Example: ["Iran oil sanctions 2026", "Iran war oil prices", "Middle East energy crisis"]"""
            },
            {
                "role": "user",
                "content": f"Generate 3 search queries for: {user_query}"
            }
        ]
    )

    raw = planning_response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        search_queries = json.loads(raw)
    except json.JSONDecodeError:
        search_queries = [user_query]

    print(f"[NewsFetcherAgent] Search queries: {search_queries}")

    # Step 2 - Execute searches
    all_articles = []
    for query in search_queries:
        print(f"[NewsFetcherAgent] Searching: '{query}'")
        results = search_news(query, days_back=7, max_results=5)
        all_articles.extend(results)
        print(f"[NewsFetcherAgent] Got {len(results)} articles")

    # Step 3 - Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article["url"] not in seen_urls:
            seen_urls.add(article["url"])
            unique_articles.append(article)

    print(f"[NewsFetcherAgent] Done. {len(unique_articles)} unique articles.")

    return {
        "query": user_query,
        "articles": unique_articles,
        "search_queries_used": search_queries,
        "total_articles": len(unique_articles)
    }


if __name__ == "__main__":
    test_query = "How is the Iran war affecting oil prices and the global economy?"

    print("=" * 60)
    print(f"Query: {test_query}")
    print("=" * 60)

    result = fetch_news_for_query(test_query)

    print(f"\nSearch queries used: {result['search_queries_used']}")
    print(f"Total articles: {result['total_articles']}")
    print("\nArticles:")
    for i, article in enumerate(result["articles"], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Published: {article['published_at']}")