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

def get_experiment_flow():
    """Get subject, session, neuron, region in that order."""
    cypher = """
    MATCH (s:Subject)-[:HAS_SESSION]->(sess:Session)-[:HAS_NEURON]->(n:Neuron)-[:LOCATED_IN]->(r:BrainRegion)
    RETURN s, sess, n, r
    LIMIT 100;
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)

def get_neuron_clusters():
    """Get neuron clusters within sessions and which brain regions those sessions were targeted simultaneously.
    """
    cypher = """
    MATCH (sess:Session)-[:HAS_NEURON]->(n:Neuron)-[:LOCATED_IN]->(r:BrainRegion)
    RETURN sess, n, r
    LIMIT 100;
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)

def get_multi_region_sessions():
    """Get sessions that experimented on multiple brain regions."""
    cypher = """
    MATCH (sess:Session)-[:HAS_NEURON]->(n:Neuron)-[:LOCATED_IN]->(r:BrainRegion)
    WITH sess, collect(distinct r.name) AS regions, count(n) AS unitCount
    WHERE size(regions) > 1
    RETURN sess.session_id, regions, unitCount
    ORDER BY unitCount DESC;
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher):
            results.append(record.data())
    driver.close()
    return pd.DataFrame(results)
