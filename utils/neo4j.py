"""
Helper functions for querying Neo4j graph DB.
"""

import pandas as pd
from neo4j import GraphDatabase
import config


def _driver():
    return GraphDatabase.driver(
        config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASS)
    )


def get_graph_summary():
    """Return node counts grouped by label using a simple Cypher query."""
    cypher = """
    MATCH (n)
    RETURN labels(n) AS labels, count(n) AS count
    ORDER BY count DESC
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)

def get_brain_regions():
    """Get all brain regions with their neuron counts."""
    cypher = """
    MATCH (br:BrainRegion)<-[:LOCATED_IN]-(n:Neuron)
    RETURN br.name AS brain_region, count(n) AS n_neurons
    ORDER BY n_neurons DESC
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)

def get_neurons_per_session():
    """Get neuron count per session."""
    cypher = """
    MATCH (sess:Session)-[:HAS_NEURON]->(n:Neuron)
    RETURN sess.session_id AS session_id, count(n) AS n_neurons
    ORDER BY n_neurons DESC
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)