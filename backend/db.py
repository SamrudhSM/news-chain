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

def create_event(event: dict, user_id: str):
    with driver.session() as session:
        session.run("""
            MERGE (e:Event {id: $id, user_id: $user_id})
            SET e.title      = $title,
                e.summary    = $summary,
                e.category   = $category,
                e.date       = $date,
                e.risk_score = $risk_score
        """,
            id=event.get("id", ""),
            user_id=user_id,
            title=event.get("title", ""),
            summary=event.get("summary", ""),
            category=event.get("category", ""),
            date=event.get("date", ""),
            risk_score=event.get("risk_score", 0)
        )

def create_entity(name: str, entity_type: str, user_id: str):
    with driver.session() as session:
        session.run("""
            MERGE (n:Entity {name: $name, user_id: $user_id})
            SET n.type = $entity_type
        """, name=name, entity_type=entity_type, user_id=user_id)

def create_topic(name: str, user_id: str):
    with driver.session() as session:
        session.run("MERGE (t:Topic {name: $name, user_id: $user_id})", name=name, user_id=user_id)

def link_event_causes_event(from_id: str, to_id: str, confidence: float, explanation: str, user_id: str):
    with driver.session() as session:
        session.run("""
            MATCH (a:Event {id: $from_id, user_id: $user_id})
            MATCH (b:Event {id: $to_id, user_id: $user_id})
            MERGE (a)-[r:CAUSES]->(b)
            SET r.confidence  = $confidence,
                r.explanation = $explanation
        """, from_id=from_id, to_id=to_id, confidence=confidence, explanation=explanation, user_id=user_id)

def link_event_impacts_topic(event_id: str, topic_name: str, impact: str, user_id: str):
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id, user_id: $user_id})
            MERGE (t:Topic {name: $topic_name, user_id: $user_id})
            MERGE (e)-[r:IMPACTS]->(t)
            SET r.impact = $impact
        """, event_id=event_id, topic_name=topic_name, impact=impact, user_id=user_id)

def link_event_involves_entity(event_id: str, entity_name: str, user_id: str):
    with driver.session() as session:
        session.run("""
            MATCH (e:Event {id: $event_id, user_id: $user_id})
            MATCH (n:Entity {name: $entity_name, user_id: $user_id})
            MERGE (e)-[:INVOLVES]->(n)
        """, event_id=event_id, entity_name=entity_name, user_id=user_id)

def get_causal_chain(entity_name: str, user_id: str, depth: int = 3):
    with driver.session() as session:
        result = session.run("""
            MATCH (n:Entity {name: $entity_name, user_id: $user_id})<-[r1:INVOLVES]-(e:Event {user_id: $user_id})
            OPTIONAL MATCH (e)-[r2:IMPACTS]->(t:Topic {user_id: $user_id})
            OPTIONAL MATCH (e)-[r3:INVOLVES]->(other:Entity {user_id: $user_id})
            RETURN e, t, other, n, r1, r2, r3
        """, entity_name=entity_name, user_id=user_id)
        return [record for record in result]

def get_events_impacting_topic(topic_name: str, user_id: str):
    """
    Get all events that impact a specific topic.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event {user_id: $user_id})-[r:IMPACTS]->(t:Topic {name: $topic_name, user_id: $user_id})
            RETURN e, r.impact AS impact
            ORDER BY e.date DESC
            LIMIT 20
        """, topic_name=topic_name, user_id=user_id)
        return [{"event": dict(record["e"]), "impact": record["impact"]} for record in result]

def get_recent_events(user_id: str, limit: int = 10):
    """
    Get most recent events for the feed.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event {user_id: $user_id})
            WHERE e.category <> 'causal'
            RETURN e
            ORDER BY e.date DESC
            LIMIT $limit
        """, limit=limit, user_id=user_id)
        return [dict(record["e"]) for record in result]

def get_all_graph_data(user_id: str):
    """
    Get all nodes and relationships for full graph visualization.
    """
    with driver.session() as session:
        nodes_result = session.run("MATCH (n {user_id: $user_id}) RETURN n", user_id=user_id)
        nodes = []
        for record in nodes_result:
            node = record["n"]
            nodes.append({
                "id": str(node.element_id),
                "labels": list(node.labels),
                "properties": dict(node)
            })

        edges_result = session.run("MATCH (a {user_id: $user_id})-[r]->(b {user_id: $user_id}) RETURN r", user_id=user_id)
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

def get_event_graph(event_id: str, user_id: str):
    """
    Get only nodes and relationships for a specific event.
    Max 15 nodes to keep graph clean.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event {id: $event_id, user_id: $user_id})
            OPTIONAL MATCH (e)-[r1:INVOLVES]->(entity:Entity {user_id: $user_id})
            OPTIONAL MATCH (e)-[r2:IMPACTS]->(topic:Topic {user_id: $user_id})
            OPTIONAL MATCH (e)-[r3:CAUSES]->(effect:Event {user_id: $user_id})
            RETURN e, entity, topic, effect, r1, r2, r3
            LIMIT 15
        """, event_id=event_id, user_id=user_id)
        return [record for record in result]


if __name__ == "__main__":
    test_connection()
    create_schema()