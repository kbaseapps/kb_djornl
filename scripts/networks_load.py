#!/usr/bin/env python
""" Load network data into a sqlite database """
import json
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

def merge_edge_metadata(manifest):
    """ Load the edge metadata yaml file """
    edge_yaml_path = os.path.join(
        DATA_ROOT, "../relation_engine/spec/datasets/djornl/edge_type.yaml"
    )
    edge_metadata = {
        manifest_file["path"].split("/")[1][:-4]: manifest_file
        for manifest_file in manifest["file_list"]
        if manifest_file["data_type"] == "edge"
    }
    with open(edge_yaml_path) as edge_yaml_file:
        edge_yaml = yaml.safe_load(edge_yaml_file)
    citations = {
        "AT-UU-CD-00-AA-01" : "https://doi.org/10.1093/nar/gku1053",
        "AT-UU-DU-67-AA-01" : "https://doi.org/10.1101/2020.01.28.923730",
        "AT-UU-GA-01-AA-01" : "https://doi.org/10.1111/nph.13557",
        "AT-UU-GO-05-AA-01" : "https://doi.org/10.1093/bioinformatics/btq064",
        "AT-UU-KS-00-AA-01" : "https://doi.org/10.1186/s13007-015-0053-y",
        # "AT-UU-PP-00-AA-01" : "",
        "AT-UU-PX-01-AA-01" : "https://doi.org/10.1016/j.cell.2016.06.044",
        "AT-UU-PY-01-LF-01" : "https://doi.org/10.1016/j.cell.2016.06.044",
        "AT-UU-RE-00-AA-01" : "https://doi.org/10.1093/molbev/msv058",
        "AT-UU-RP-03-AA-01" : "https://doi.org/10.1093/nar/gkz1020",
        "AT-UU-RX-00-AA-01" : "https://doi.org/10.1104/pp.102.017236",
    }
    edge_metadata_updates = [
        edge_metadata.get(edge_type["const"], {}).update({
            "description_re": edge_type["description"],
            "title_re": edge_type["title"],
            "cite": citations.get(edge_type["const"]),
        })
        for edge_type in edge_yaml["oneOf"]
    ]
    assert len(edge_metadata_updates) == len(edge_yaml["oneOf"])
    with open(
        os.path.join(DATA_ROOT, "edge-metadata.json"), "w"
    ) as edge_metadata_json:
        json.dump(edge_metadata, edge_metadata_json)
    return edge_yaml

def main():
    """ Load clusters, edges and nodes into a local sqlite3 db. """
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    merge_edge_metadata(manifest)
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
