import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

# Import the individual agent capabilities
from agents.news_fetcher import fetch_news_for_query
from agents.analyzer import analyze_articles, save_brief_to_neo4j

# 1. Define the Pipeline State
class AgentState(TypedDict):
    query: str
    articles: List[dict]
    brief: dict
    dry_run: bool

# 2. Define the Nodes (Agent Functions)
def fetch_news_node(state: AgentState):
    """Fetches news based on the query."""
    print(f"\n[Orchestrator] Node 1: Fetching news for: {state['query']}")
    # Call the News Fetcher logic
    result = fetch_news_for_query(state["query"])
    return {"articles": result.get("articles", [])}

def analyze_news_node(state: AgentState):
    """Analyzes the fetched articles and generates an intelligence brief."""
    print(f"\n[Orchestrator] Node 2: Analyzing {len(state.get('articles', []))} articles...")
    if not state.get("articles"):
        print("[Orchestrator] No articles to analyze. Skipping.")
        return {"brief": {}}
        
    brief = analyze_articles(state["articles"], state["query"])
    return {"brief": brief}

def save_to_graph_node(state: AgentState):
    """Saves the intelligence brief to the Neo4j database."""
    print(f"\n[Orchestrator] Node 3: Saving insights to Neo4j database...")
    brief = state.get("brief", {})
    if brief:
        save_brief_to_neo4j(brief)
    return {}

# 3. Create the StateGraph Builder
workflow = StateGraph(AgentState)

# Add all nodes to the graph
workflow.add_node("news_fetcher", fetch_news_node)
workflow.add_node("analyzer", analyze_news_node)
workflow.add_node("graph_saver", save_to_graph_node)

# Define the sequential pipeline flow
workflow.add_edge(START, "news_fetcher")
workflow.add_edge("news_fetcher", "analyzer")

# Add conditional logic for the optional dry-run feature
def decide_save(state: AgentState):
    """Decide whether to save to database based on dry_run flag."""
    if state.get("dry_run", False):
        print("\n[Orchestrator] Link: Dry-run enabled. Skipping database save path.")
        return END
    
    # Also skip saving if the brief is completely empty
    if not state.get("brief"):
        print("\n[Orchestrator] Link: Empty brief. Skipping database save path.")
        return END
        
    return "graph_saver"

workflow.add_conditional_edges("analyzer", decide_save)
workflow.add_edge("graph_saver", END)

# Compile the graph into a runnable app
orchestrator_app = workflow.compile()


def run_intelligence_pipeline(user_query: str, dry_run: bool = False) -> dict:
    """
    Main entry point to run the intelligence pipeline.
    
    Args:
        user_query (str): The high-level topic to research and map out.
        dry_run (bool): If True, it will skip saving nodes to Neo4j (helpful for testing).
        
    Returns:
        dict: The final pipeline state including articles and intelligence brief.
    """
    print("="*60)
    print(f"Starting Orchestrator Pipeline for: '{user_query}'")
    print(f"Dry Run Mode: {dry_run}")
    print("="*60)
    
    # Initialize the starting state
    initial_state = {
        "query": user_query,
        "articles": [],
        "brief": {},
        "dry_run": dry_run
    }
    
    # Invoke the LangGraph pipeline
    final_state = orchestrator_app.invoke(initial_state)
    
    print("\n" + "="*60)
    print("Pipeline Complete")
    print("="*60)
    
    return final_state

if __name__ == "__main__":
    # A simple test run
    test_q = "How are technological sanctions impacting China's semiconductor industry?"
    
    # Set dry_run=True so we don't immediately push random test events to the Neo4j database
    final_result = run_intelligence_pipeline(test_q, dry_run=False)
    
    print("\nExtracted Intelligence Brief:")
    import json
    print(json.dumps(final_result.get("brief", {}), indent=2))
