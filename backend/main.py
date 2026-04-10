import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from models.schemas import QueryRequest, QueryResponse, GraphResponse
from agents.orchestrator import run_intelligence_pipeline
from backend.db import get_causal_chain, get_recent_events, get_event_graph
import logging

security = HTTPBearer()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not SUPABASE_JWT_SECRET:
        # If secret not set yet in dev, just decode without verification to keep moving
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub", "")
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        return payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

app = FastAPI(title="NewsChain API", description="AI Agentic Geopolitical Graph API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "NewsChain API is running"}


@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest, user_id: str = Depends(get_current_user)):
    """
    Run a full intelligence pipeline: fetch news, analyze it, and optionally save to graph.
    """
    try:
        logging.info(f"Running pipeline with query: {req.query}, dry_run={req.dry_run}, user={user_id}")
        final_state = run_intelligence_pipeline(req.query, user_id=user_id, dry_run=req.dry_run)
        
        return QueryResponse(
            query=final_state.get("query", ""),
            articles=final_state.get("articles", []),
            brief=final_state.get("brief", {}),
            dry_run=final_state.get("dry_run", False)
        )
    except Exception as e:
        logging.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def serialize_neo4j_paths(records) -> dict:
    nodes = {}
    edges = {}

    for record in records:
        for key in record.keys():
            item = record[key]
            if item is None:
                continue
            
            # Check if it's a relationship
            if hasattr(item, 'start_node'):
                rel_id = str(item.element_id)
                if rel_id not in edges:
                    edges[rel_id] = {
                        "id": rel_id,
                        "source": str(item.start_node.element_id),
                        "target": str(item.end_node.element_id),
                        "type": item.type,
                        "properties": dict(item)
                    }
            # It's a node
            elif hasattr(item, 'labels'):
                node_id = str(item.element_id)
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "labels": list(item.labels),
                        "properties": dict(item)
                    }

    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values())
    }


@app.get("/graph/{entity}", response_model=GraphResponse)
def get_entity_graph(entity: str, depth: int = 3, user_id: str = Depends(get_current_user)):
    """
    Get the causal chain / graph for a specific entity.
    """
    try:
        paths = get_causal_chain(entity, depth=depth, user_id=user_id)
        graph_data = serialize_neo4j_paths(paths)
        return GraphResponse(**graph_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/event/{event_id}", response_model=GraphResponse)
def get_event_graph_endpoint(event_id: str, user_id: str = Depends(get_current_user)):
    """
    Get clean graph for a specific event only.
    """
    try:
        records = get_event_graph(event_id, user_id=user_id)
        graph_data = serialize_neo4j_paths(records)
        return GraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feed")
def get_feed(limit: int = 10, user_id: str = Depends(get_current_user)):
    """Get recent intelligence events for the feed."""
    try:
        events = get_recent_events(limit=limit, user_id=user_id)
        return {"events": events, "total": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
