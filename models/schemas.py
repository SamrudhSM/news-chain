from pydantic import BaseModel, Field
from typing import List, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., description="The high-level geopolitical query to run")
    dry_run: bool = Field(default=False, description="If true, avoids saving to the Neo4j database")

class QueryResponse(BaseModel):
    query: str
    articles: List[Dict[str, Any]]
    brief: Dict[str, Any]
    dry_run: bool

class GraphNode(BaseModel):
    id: str
    labels: List[str]
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
