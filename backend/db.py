from neo4j import GraphDatabase, TrustAll
from dotenv import load_dotenv
import os

load_dotenv()

URI      = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Connected to Nexus News DB' AS message")
        print(result.single()["message"])

def create_schema():
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:NewsArticle) REQUIRE a.url IS UNIQUE")
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.date)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.category)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)")
        print("Schema created successfully.")

def create_event(event: dict):
    with driver.session() as session:
        session.run("""
            MERGE (e:Event {id: $id})
            SET e.title      = $title,
                e.summary    = $summary,
                e.category   = $category,
                e.date       = $date,
                e.risk_score = $risk_score
        """,
            id=event.get("id", ""),
            title=event.get("title", ""),
            summary=event.get("summary", ""),
            category=event.get("category", ""),
            date=event.get("date", ""),
            risk_score=event.get("risk_score", 0)
        )

def create_entity(name: str, entity_type: str):
    with driver.session() as session:
        session.run("""
            MERGE (n:Entity {name: $name})
            SET n.type = $entity_type
        """, name=name, entity_type=entity_type)

def create_topic(name: str):
    with driver.session() as session:
        session.run("MERGE (t:Topic {name: $name})", name=name)

def link_event_causes_event(from_id: str, to_id: str, confidence: float, explanation: str):
    with driver.session() as session:
        session.run("""
            MATCH (a:Event {id: $from_id})
            MATCH (b:Event {id: $to_id})
            MERGE (a)-[r:CAUSES]->(b)
            SET r.confidence  = $confidence,
                r.explanation = $explanation
        """, from_id=from_id, to_id=to_id, confidence=confidence, explanation=explanation)

def link_event_impacts_topic(event_id: str, topic_name: str, impact: str):
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id})
            MERGE (t:Topic {name: $topic_name})
            MERGE (e)-[r:IMPACTS]->(t)
            SET r.impact = $impact
        """, event_id=event_id, topic_name=topic_name, impact=impact)

def link_event_involves_entity(event_id: str, entity_name: str):
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id})
            MATCH (n:Entity {name: $entity_name})
            MERGE (e)-[:INVOLVES]->(n)
        """, event_id=event_id, entity_name=entity_name)

def get_causal_chain(entity_name: str, depth: int = 3):
    with driver.session() as session:
        result = session.run("""
            MATCH (n:Entity {name: $entity_name})<-[r1:INVOLVES]-(e:Event)
            OPTIONAL MATCH (e)-[r2:IMPACTS]->(t:Topic)
            OPTIONAL MATCH (e)-[r3:INVOLVES]->(other:Entity)
            RETURN e, t, other, n, r1, r2, r3
        """, entity_name=entity_name)
        return [record for record in result]

def get_events_impacting_topic(topic_name: str):
    """
    Get all events that impact a specific topic.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event)-[r:IMPACTS]->(t:Topic {name: $topic_name})
            RETURN e, r.impact AS impact
            ORDER BY e.date DESC
            LIMIT 20
        """, topic_name=topic_name)
        return [{"event": dict(record["e"]), "impact": record["impact"]} for record in result]

def get_recent_events(limit: int = 10):
    """
    Get most recent events for the feed.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event)
            WHERE e.category <> 'causal'
            RETURN e
            ORDER BY e.date DESC
            LIMIT $limit
        """, limit=limit)
        return [dict(record["e"]) for record in result]

def get_all_graph_data():
    """
    Get all nodes and relationships for full graph visualization.
    """
    with driver.session() as session:
        nodes_result = session.run("MATCH (n) RETURN n")
        nodes = []
        for record in nodes_result:
            node = record["n"]
            nodes.append({
                "id": str(node.element_id),
                "labels": list(node.labels),
                "properties": dict(node)
            })

        edges_result = session.run("MATCH ()-[r]->() RETURN r")
        edges = []
        for record in edges_result:
            rel = record["r"]
            edges.append({
                "id": str(rel.element_id),
                "source": str(rel.start_node.element_id),
                "target": str(rel.end_node.element_id),
                "type": rel.type,
                "properties": dict(rel)
            })

        return {"nodes": nodes, "edges": edges}

def get_event_graph(event_id: str):
    """
    Get only nodes and relationships for a specific event.
    Max 15 nodes to keep graph clean.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event {id: $event_id})
            OPTIONAL MATCH (e)-[r1:INVOLVES]->(entity:Entity)
            OPTIONAL MATCH (e)-[r2:IMPACTS]->(topic:Topic)
            OPTIONAL MATCH (e)-[r3:CAUSES]->(effect:Event)
            RETURN e, entity, topic, effect, r1, r2, r3
            LIMIT 15
        """, event_id=event_id)
        return [record for record in result]


if __name__ == "__main__":
    test_connection()
    create_schema()