#!/usr/bin/env python
""" Load network data into a sqlite database """
import os
import sqlite3

import pandas as pd
import yaml

DATA_ROOT = os.environ.get("KBDJORNL_DATA_ROOT") or "/data/exascale_data/"

CONCAT_QUERY = """
SELECT
    MIN("index") AS mindex,
    node_id,
    node_type,
    gene_model_type,
    gene_symbol,
    pheno_aragwas_id,
    pheno_description,
    pheno_pto_description,
    pheno_pto_name,
    pheno_reference,
    '['
    || group_concat(
        CASE WHEN length(transcript)>0
        THEN printf('"%s"', transcript)
        ELSE '""' END
    )
    || ']' AS transcripts,
    '['
    || group_concat(
        CASE WHEN length(go_terms)>0
        THEN printf('"%s"', go_terms)
        ELSE '""' END
    )
    || ']' as go_terms,
    '['
    || group_concat(
        CASE WHEN length(go_terms)>0
        THEN printf(
            '{"transcript": "%s", "go_term": "%s", "go_description": "%s"}',
            transcript, go_terms, go_description
        )
        ELSE '{}' END
    )
    || ']' AS go_infos,
    '['
    || group_concat(
        CASE WHEN length(mapman_bin)>0
        THEN printf(
            '{"transcript": "%s", "bin": "%s", "name": "%s", "description": "%s"}',
            transcript, mapman_bin, mapman_name, mapman_description
        )
        ELSE '{}' END
    )
    || ']' AS mapman_infos,
    '['
    || group_concat(
        CASE WHEN length(tair_short_description)>0
        THEN printf(
            '{
                "transcript": "%s",
                "gene_model_type": "%s",
                "tair_short_description": "%s",
                "tair_curator_summary": "%s",
                "tair_computational_description": "%s"
            }',
            transcript,
            gene_model_type,
            tair_short_description,
            tair_curator_summary,
            tair_computational_description
        )
        ELSE '{}' END
    )
    || ']' AS tair_infos
FROM nodes_raw
GROUP BY node_id, node_type
ORDER BY count(*) DESC
"""

def create_tables_node(con):
    """ create schema to store nodes """
    nodes_raw_table = """CREATE TABLE IF NOT EXISTS nodes_raw (
        "index" INTEGER,
        "node_id" TEXT,
        "node_type" TEXT,
        "gene_model_type" TEXT,
        "gene_symbol" TEXT,
        "go_description" TEXT,
        "go_terms" TEXT,
        "mapman_bin" TEXT,
        "mapman_description" TEXT,
        "mapman_name" TEXT,
        "pheno_aragwas_id" TEXT,
        "pheno_description" TEXT,
        "pheno_pto_description" TEXT,
        "pheno_pto_name" TEXT,
        "pheno_reference" TEXT,
        "tair_computational_description" TEXT,
        "tair_curator_summary" TEXT,
        "tair_short_description" TEXT,
        "transcript" TEXT
    )"""

    nodes_table = """CREATE TABLE IF NOT EXISTS nodes (
        "mindex" INTEGER,
        "node_id" TEXT,
        "node_type" TEXT,
        "gene_model_type" TEXT,
        "gene_symbol" TEXT,
        "pheno_aragwas_id" TEXT,
        "pheno_description" TEXT,
        "pheno_pto_description" TEXT,
        "pheno_pto_name" TEXT,
        "pheno_reference" TEXT,
        "transcripts" TEXT,
        "go_terms" TEXT,
        "go_infos" TEXT,
        "mapman_infos" TEXT,
        "tair_infos" TEXT
    )"""

    cur_nodes_raw = con.execute(nodes_raw_table)
    cur_nodes = con.execute(nodes_table)

    assert cur_nodes_raw.fetchall() == []
    assert cur_nodes.fetchall() == []

def load_manifest_items(manifest_items, con):
    """ load edge files into db """
    for manifest in manifest_items:
        manifest_tsv_name = manifest["path"]
        manifest_tsv_path = os.path.join(DATA_ROOT, "prerelease/", manifest_tsv_name)
        manifest_tsv = pd.read_csv(manifest_tsv_path, sep="\t")
        manifest_tsv.to_sql(manifest_tsv_name, con, if_exists="replace")

def load_nodes(node_items, con):
    """ Load all the nodes from the node_tables.
        The magic happens in CONCAT_QUERY
    """
    for node_item in node_items:
        node_df = pd.read_csv(node_item, sep="\t")
        node_df.to_sql("nodes_raw", con, if_exists="append")
    cur_catted = con.execute(f"""INSERT INTO nodes {CONCAT_QUERY}""")
    assert cur_catted.fetchall() == []
    con.commit()

def load_nodes_merged(con):
    """ Load nodes from the merged file. """
    columns_nodes_raw = list(
      pd.read_sql("""SELECT * FROM nodes_raw""", con).columns
    )
    merge_df = pd.read_csv(
        f"{DATA_ROOT}/prerelease/aranet2-aragwas-MERGED-AMW-v2_091319_nodeTable.csv",
        usecols=lambda col: col in columns_nodes_raw
    )
    merge_df.to_sql("nodes_raw", con, if_exists="append")


def main():
    """ Load clusters, edges and nodes into a local sqlite3 db. """
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    # index manifest by nodes, edges and clusters
    manifest_index = {
        "node": [],
        "edge": [],
        "cluster": [],
    }
    manifest_indexed = [
        manifest_index[entry["data_type"]].append(entry)
        for entry in manifest["file_list"]
    ]
    assert len(manifest_indexed) > 0
    networks_path = os.path.join(DATA_ROOT, "networks.db")
    con = sqlite3.connect(networks_path)
    load_manifest_items(manifest_index["edge"], con)
    load_manifest_items(manifest_index["cluster"], con)
    create_tables_node(con)
    load_nodes_merged(con)
    node_table_prefix = "/prerelease/node_tables/20210107_ExaKBase_AT_nodetab_"
    node_items = [
        f"{DATA_ROOT}{node_table_prefix}gene-MapMan-vX4.2.tsv",
        f"{DATA_ROOT}{node_table_prefix}gene-TAIR-v2018.tsv",
        f"{DATA_ROOT}{node_table_prefix}pheno-AraPheno-v062716.tsv",
        f"{DATA_ROOT}{node_table_prefix}gene-GOslimTAIR-v010121.tsv",
    ]
    load_nodes(node_items, con)

if __name__ == "__main__":
    main()
