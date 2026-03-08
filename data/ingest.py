"""
Download one NWB session from DANDI 000004 and load into PostgreSQL + Neo4j.
File is cached in data/ so subsequent runs are instant.
"""
import os
import numpy as np
import psycopg
from pynwb import read_nwb
from dandi.download import download
from neo4j import GraphDatabase
import config

# asset download hardcode link from dandiset 000004 (~72 MB) via DANDI API
# change this to download another session
NWB_URL  = 'https://api.dandiarchive.org/api/assets/0f57f0b0-f021-42bb-8eaa-56cd482e2a29/download/'
NWB_PATH = 'data/sub-P11HMH_ses-20061101_ecephys+image.nwb'

def open_nwb():
    if not os.path.exists(NWB_PATH):
        print("Downloading NWB file (~72 MB) ...")
        download(NWB_URL, "data/")
    return read_nwb(NWB_PATH)

def ingest_postgres(nwb):
    session_id = nwb.identifier
    subject_id = str(nwb.subject.subject_id)
    units_df = nwb.units.to_dataframe()
    trials_df = nwb.trials.to_dataframe() if nwb.trials else None

    # each unit's 'electrodes' cell is a small df of the referenced electrode rows.
    # .iloc[0]['location'] gives the brain region string for that unit.
    regions = {
        i: str(units_df['electrodes'].iloc[i]['location'].iloc[0])
        for i in range(len(units_df))
    }

    with psycopg.connect(config.PG_DSN) as conn, conn.cursor() as cur:
        cur.execute(
            'INSERT INTO subjects (subject_id, age, sex, species, institution) '
            'VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
            (subject_id, nwb.subject.age, nwb.subject.sex,
             nwb.subject.species, nwb.institution))

        cur.execute(
            'INSERT INTO sessions (session_id, subject_id, session_date) '
            'VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
            (session_id, subject_id, nwb.session_start_time))

        neuron_ids = {}
        for i in range(len(nwb.units)):
            spikes = np.array(nwb.units["spike_times"][i], dtype=float)
            dur = float(spikes[-1] - spikes[0]) if len(spikes) > 1 else 1.0
            iso = units_df['IsolationDist'].iloc[i]
            snr = units_df['SNR'].iloc[i]
            cur.execute(
                'INSERT INTO neurons (session_id, unit_index, brain_region, '
                'n_spikes, mean_firing_rate, spike_times, orig_cluster_id, isolation_dist, snr) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING neuron_id',
                (session_id, i, regions[i], len(spikes), len(spikes) / dur, spikes.tolist(),
                 int(units_df['origClusterID'].iloc[i]),
                 None if np.isnan(iso) else float(iso),
                 None if np.isnan(snr) else float(snr)))
            neuron_ids[i] = cur.fetchone()[0]

        if trials_df is not None:
            for j, row in trials_df.iterrows():
                cur.execute(
                    'INSERT INTO trials (session_id, trial_index, stim_phase, '
                    'start_time, stop_time, stim_on_time, stim_off_time, '
                    'delay1_time, delay2_time, stim_category, category_name, '
                    'external_image_file, new_old_labels_recog, response_value, response_time) '
                    'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (session_id, j, row['stim_phase'],
                     row['start_time'], row['stop_time'],
                     row['stim_on_time'], row['stim_off_time'],
                     row['delay1_time'], row['delay2_time'],
                     int(row['stimCategory']), row['category_name'],
                     row['external_image_file'], row['new_old_labels_recog'],
                     row['response_value'], row['response_time']))

        conn.commit()

    n_trials = len(trials_df) if trials_df is not None else 0
    print(f'[Postgres] {len(neuron_ids)} neurons, {n_trials} trials.')
    return neuron_ids, session_id, subject_id, regions

def ingest_neo4j(nwb, neuron_ids, session_id, subject_id, regions):
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASS))
    with driver.session() as s:
        s.run('MATCH (n) DETACH DELETE n')  # clear for idempotent re-runs
        s.run('MERGE (su:Subject {subject_id:$id})', id=subject_id)
        s.run('MERGE (se:Session {session_id:$id}) SET se.date=$dt',
              id=session_id, dt=str(nwb.session_start_time))
        s.run('MATCH (su:Subject {subject_id:$subj}),(se:Session {session_id:$sess}) '
              'MERGE (su)-[:HAS_SESSION]->(se)', subj=subject_id, sess=session_id)

        for region in set(regions.values()):
            s.run('MERGE (:BrainRegion {name:$r})', r=region)

        for i, db_id in neuron_ids.items():
            s.run('MERGE (n:Neuron {db_id:$id}) SET n.unit_index=$ui, n.brain_region=$br',
                  id=db_id, ui=i, br=regions[i])
            s.run('MATCH (se:Session {session_id:$sess}),(n:Neuron {db_id:$id}) '
                  'MERGE (se)-[:HAS_NEURON]->(n)', sess=session_id, id=db_id)
            s.run('MATCH (n:Neuron {db_id:$id}),(br:BrainRegion {name:$r}) '
                  'MERGE (n)-[:LOCATED_IN]->(br)', id=db_id, r=regions[i])

    driver.close()
    print(f'[Neo4j] {len(neuron_ids)} neurons.')

if __name__ == '__main__':
    nwb = open_nwb()
    print(f'Session: {nwb.identifier}')
    neuron_ids, session_id, subject_id, regions = ingest_postgres(nwb)
    ingest_neo4j(nwb, neuron_ids, session_id, subject_id, regions)
    nwb.get_read_io().close()