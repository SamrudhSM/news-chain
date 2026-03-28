import requests
import os
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

def search_news(query: str, days_back: int = 7, max_results: int = 5) -> list[dict]:
    """
    Search for news articles using NewsAPI.
    
    Args:
        query: Search query e.g. "Iran oil sanctions"
        days_back: How many days back to search (default 7)
        max_results: Max articles to return (default 5)
    
    Returns:
        List of articles with title, description, url, publishedAt
    """
    from datetime import datetime, timedelta

    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "from": date_from,
        "sortBy": "relevancy",
        "pageSize": max_results,
        "language": "en",
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"NewsAPI error: {data.get('message')}")
            return []

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title":       article.get("title", ""),
                "description": article.get("description", ""),
                "url":         article.get("url", ""),
                "source":      article.get("source", {}).get("name", ""),
                "published_at": article.get("publishedAt", ""),
                "content":     article.get("content", "")
            })

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []


def get_top_geopolitical_news(max_results: int = 10) -> list[dict]:
    """
    Fetch top geopolitical news without a specific query.
    Good for trending topics feed.
    """
    query = "geopolitics OR war OR sanctions OR military OR diplomacy OR conflict"
    return search_news(query, days_back=2, max_results=max_results)


if __name__ == "__main__":
    # Test it
    print("Testing NewsAPI connection...\n")
    
    articles = search_news("Iran oil sanctions", max_results=3)
    
    if articles:
        print(f"Found {len(articles)} articles:\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Published: {article['published_at']}")
            print(f"   URL: {article['url']}")
            print()
    else:
        print("No articles found. Check your NEWS_API_KEY in .env")
