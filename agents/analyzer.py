import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
import json
from dotenv import load_dotenv
from backend.db import (
    create_event, create_entity, create_topic,
    link_event_impacts_topic, link_event_involves_entity,
    link_event_causes_event
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

ANALYSIS_SCHEMA = """
Return ONLY this JSON structure, no extra text:
{
    "event": {
        "id": "unique_snake_case_id",
        "title": "Short event title",
        "summary": "2-3 sentence summary",
        "category": "military|diplomatic|economic|humanitarian|political",
        "date": "YYYY-MM-DD",
        "risk_score": 7
    },
    "entities": [
        {"name": "Entity Name", "type": "country|person|organization|commodity"}
    ],
    "topics_impacted": [
        {"name": "topic name", "impact": "positive|negative|neutral"}
    ],
    "causal_chain": [
        {
            "from_event": "cause description",
            "to_event": "effect description",
            "confidence": 0.85,
            "explanation": "why this causes that"
        }
    ],
    "intelligence_brief": "3-4 sentence plain English summary of the situation and implications",
    "watch_points": ["thing to monitor 1", "thing to monitor 2"]
}
"""

def analyze_articles(articles: list, user_query: str) -> dict:
    """
    Takes list of news articles and produces a structured intelligence brief.
    """
    articles_text = ""
    for i, article in enumerate(articles[:8], 1):
        articles_text += f"""
Article {i}:
Title: {article.get('title', '')}
Source: {article.get('source', '')}
Published: {article.get('published_at', '')}
Description: {article.get('description', '')}
---"""

    print(f"[AnalysisAgent] Analyzing {min(len(articles), 8)} articles...")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""You are a geopolitical intelligence analyst.
Given news articles, extract structured intelligence data.
Always respond with valid JSON only. No markdown, no extra text.
{ANALYSIS_SCHEMA}"""
            },
            {
                "role": "user",
                "content": f"User Query: {user_query}\n\nNews Articles:\n{articles_text}"
            }
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    # Clean markdown if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    try:
        brief = json.loads(raw_text)
        print(f"[AnalysisAgent] Analysis complete. Risk score: {brief['event']['risk_score']}/10")
        return brief
    except json.JSONDecodeError as e:
        print(f"[AnalysisAgent] JSON parse error: {e}")
        print(f"Raw response: {raw_text[:300]}")
        return {}


def save_brief_to_neo4j(brief: dict):
    """Save intelligence brief to Neo4j graph."""
    if not brief:
        print("[AnalysisAgent] Empty brief, skipping Neo4j save.")
        return

    print("[AnalysisAgent] Saving to Neo4j...")

    event = brief.get("event", {})
    if event:
        create_event(event)

    for entity in brief.get("entities", []):
        create_entity(entity["name"], entity["type"])
        if event.get("id"):
            link_event_involves_entity(event["id"], entity["name"])

    for topic in brief.get("topics_impacted", []):
        create_topic(topic["name"])
        if event.get("id"):
            link_event_impacts_topic(event["id"], topic["name"], topic["impact"])

    causal_chain = brief.get("causal_chain", [])
    for i, link in enumerate(causal_chain):
        from_id = f"{event.get('id', 'unknown')}_cause_{i}"
        to_id = f"{event.get('id', 'unknown')}_effect_{i}"

        create_event({
            "id": from_id,
            "title": link.get("from_event", ""),
            "summary": link.get("explanation", ""),
            "category": "causal",
            "date": event.get("date", ""),
            "risk_score": 0
        })
        create_event({
            "id": to_id,
            "title": link.get("to_event", ""),
            "summary": link.get("explanation", ""),
            "category": "causal",
            "date": event.get("date", ""),
            "risk_score": 0
        })
        link_event_causes_event(
            from_id, to_id,
            confidence=link.get("confidence", 0.5),
            explanation=link.get("explanation", "")
        )

    print("[AnalysisAgent] Saved to Neo4j successfully.")


def analyze_and_save(articles: list, user_query: str) -> dict:
    """Full pipeline: analyze → save to Neo4j → return brief."""
    brief = analyze_articles(articles, user_query)
    save_brief_to_neo4j(brief)
    return brief


if __name__ == "__main__":
    sample_articles = [
        {
            "title": "Iran threatens to close Strait of Hormuz after Trump ultimatum",
            "source": "Reuters",
            "published_at": "2026-03-24T10:00:00Z",
            "description": "Iran has threatened to completely close the Strait of Hormuz, through which 20% of global oil passes, following a US ultimatum over nuclear negotiations."
        },
        {
            "title": "Oil Price crosses $100 as Iran conflict escalates",
            "source": "Bloomberg",
            "published_at": "2026-03-24T12:00:00Z",
            "description": "Crude oil prices surged past $100 per barrel as markets reacted to escalating tensions in the Middle East and fears of supply disruption."
        },
        {
            "title": "Global stock markets tumble on Iran war fears",
            "source": "Financial Times",
            "published_at": "2026-03-24T14:00:00Z",
            "description": "Stock markets across Asia and Europe fell sharply as investors fled to safe haven assets including gold and US treasuries amid rising Iran conflict fears."
        },
        {
            "title": "Iran war energy crisis is a renewable energy wake-up call",
            "source": "Associated Press",
            "published_at": "2026-03-22T22:01:03Z",
            "description": "Energy experts say the Iran war fuel crisis is accelerating the transition to renewable energy as countries seek to reduce dependence on Middle East oil."
        }
    ]

    test_query = "How is the Iran war affecting oil prices and the global economy?"

    print("=" * 60)
    print(f"Query: {test_query}")
    print("=" * 60)

    brief = analyze_and_save(sample_articles, test_query)

    if brief:
        print("\n--- INTELLIGENCE BRIEF ---")
        print(f"\nEvent: {brief['event']['title']}")
        print(f"Risk Score: {brief['event']['risk_score']}/10")
        print(f"Category: {brief['event']['category']}")
        print(f"\nSummary: {brief['event']['summary']}")
        print(f"\nKey Actors: {[e['name'] for e in brief.get('entities', [])]}")
        print(f"\nTopics Impacted: {[t['name'] for t in brief.get('topics_impacted', [])]}")
        print(f"\nCausal Chain:")
        for chain in brief.get('causal_chain', []):
            print(f"  {chain['from_event']} → {chain['to_event']} (confidence: {chain['confidence']})")
        print(f"\nIntelligence Brief:\n{brief.get('intelligence_brief', '')}")
        print(f"\nWatch Points: {brief.get('watch_points', [])}")