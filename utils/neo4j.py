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
    """Count nodes per label in the graph."""
    cypher = """
        CALL apoc.meta.stats()
        YIELD labels
        RETURN labels
    """
    # Simpler version that doesn't require APOC:
    labels = ['Subject', 'Session', 'Neuron', 'BrainRegion', 'Stimulus']
    driver = _driver()
    counts = {}
    with driver.session() as s:
        for label in labels:
            result = s.run(f'MATCH (n:{label}) RETURN COUNT(n) AS c')
            counts[label] = result.single()['c']
    driver.close()
    return counts

def get_neuron_path(neuron_db_id):
    """
    Return the full path: Subject -> Session -> Neuron -> BrainRegion
    for a given neuron's database ID (the SERIAL id from PostgreSQL).
    """
    cypher = """
        MATCH path =
            (su:Subject)-[:HAS_SESSION]->(se:Session)
                        -[:HAS_NEURON]->(n:Neuron {db_id: $db_id})
                        -[:LOCATED_IN]->(br:BrainRegion)
        RETURN
            su.subject_id  AS subject,
            se.session_id  AS session,
            n.db_id        AS neuron_db_id,
            n.unit_index   AS unit_index,
            n.n_spikes     AS n_spikes,
            n.mean_firing_rate AS mean_firing_rate,
            br.name        AS brain_region
    """
    driver = _driver()
    results = []
    with driver.session() as s:
        for record in s.run(cypher, db_id=neuron_db_id):
            results.append(dict(record))
    driver.close()
    return results
