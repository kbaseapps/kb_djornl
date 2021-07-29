#!/usr/bin/env python
""" Load network data into a sqlite database """
import os
import sqlite3

import pandas as pd
import yaml

DATA_ROOT = os.environ.get("KBDJORNL_DATA_ROOT") or "/data/exascale_data/"

def create_tables_node(con):
    """ create schema to store nodes """

    nodes_table = """CREATE TABLE IF NOT EXISTS "nodes" (
    "index" INTEGER,
      "GID" TEXT,
      "defline" TEXT,
      "symbols" TEXT,
      "names" TEXT,
      "KO_effect" TEXT,
      "GO" TEXT,
      "GOdesc" TEXT,
      "mapman_code" TEXT,
      "mapman_name" TEXT,
      "mapman_desc" TEXT
    )"""

    cur_nodes = con.execute(nodes_table)

    assert cur_nodes.fetchall() == []

def load_manifest_items(manifest_items, con):
    """ load edge files into db """
    for manifest in manifest_items:
        manifest_tsv_name = manifest["path"]
        manifest_tsv_path = os.path.join(DATA_ROOT, "prerelease/", manifest_tsv_name)
        manifest_tsv = pd.read_csv(manifest_tsv_path, sep="\t")
        manifest_tsv.to_sql(manifest_tsv_name, con, if_exists="replace")

def load_nodes(con):
    """ Load all the nodes from the node_tables. """
    nodes_df = pd.read_csv(
        f"{DATA_ROOT}/prerelease/node_tables/Ath_master_annotation_v01.txt",
        sep="\t",
    )
    nodes_df.to_sql("nodes", con, if_exists="replace")

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
    load_nodes(con)

if __name__ == "__main__":
    main()
