# Neuronal Electrophysiology Analysis Using DANDI 000004

Neuroscience is a vast field, subject to domain experts. As such, there are terabytes of publicly available datasets on the topic, running from literature review to experimental design and analysis. One such database containing these datasets is DANDI: Distributed Archives for Neurophysiology Data Integration. Considered the gold standard for electrophysiology, DANDI uses the .nwb format (Neurodata Without Borders, a proprietary data format, organized into “Dandisets”) that plays nicely with vector databases, graph databases, and tabular databases. We explain our proposed approach below, using Dandiset 000004, “A NWB-based dataset and processing pipeline of human single-neuron activity during a declarative memory task”.

Vector DB: The dataset includes labels and descriptions of images and words shown to subjects during a declarative memory task. These stimuli will be recorded as a vector that can be searched by the user to find embeddings. Example: “A user searches for CAT. Qdrant will find CAT in the stimuli embeddings and ask other DBs which neurons were fired with the CAT shown.”

Graph DB: The brain is very much hierarchical. With nodes like SUBJECT, SESSION, REGION, NEURON, STIMULUS, we can query the edges to find the path that a query follows. Example: “A user searches for NEURON 12345. Neo4j will find the edges and nodes directed to it, such as the location being in region DG, connected to SESSION 999, on SUBJECT Alice; or pointing away from it such as being presented with the STIMULUS man.

Tabular DB (if we have time): We will assume that time series data is a core component of this dataset. Therefore, we will allow the user to perform summary statistics. Example: “Postgres query for firing statistics (mean, median, min, max, counts) of GABAergic neurons found in mossy fiber pathway in SESSION 999.”

Slides will be done with Jupyter RISE 5.7.2 (reveal.js) if we are feeling fancy.