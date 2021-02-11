""" kb_djornl code """

import json
import os
import shutil
import sqlite3
import subprocess
import time
import uuid

from collections import Counter

import pandas as pd
import yaml

from jinja2 import Environment, PackageLoader, select_autoescape

from relation_engine_client import REClient

DATA_ROOT = "/opt/work/exascale_data/"
con = sqlite3.connect(":memory:")
nodes_df = pd.read_csv(
    os.path.join(
        DATA_ROOT,
        "prerelease/aranet2-aragwas-MERGED-AMW-v2_091319_nodeTable.csv",
    )
)

cluster_tsvs = (
    "out.aranetv2_subnet_AT-CX_top10percent_anno_AF_082919.abc.I2_named.tsv",
    "out.aranetv2_subnet_AT-CX_top10percent_anno_AF_082919.abc.I4_named.tsv",
    "out.aranetv2_subnet_AT-CX_top10percent_anno_AF_082919.abc.I6_named.tsv",
)

nodes_df.to_sql("nodes", con, if_exists="replace")
for i in (2, 4, 6):
    tsv_path = os.path.join(
        DATA_ROOT, "prerelease/cluster_data", cluster_tsvs[i // 2 - 1]
    )
    df = pd.read_csv(tsv_path, delimiter="\t")
    df.to_sql(f"i{i}", con, if_exists="replace")


def check_gene_key_match(gene_keys, node_id):
    """Return True if any gene_key in gene_keys matches node_id."""
    return any([f"/{key}" in node_id for key in gene_keys])


CLUSTER_MEMBERS_QUERY = """
SELECT node_ids from i{inflation} where cluster_id='{cluster_name}'
"""


def get_cluster_length(cluster):
    """ get a cluster and return its length """
    cluster_id, inflation = cluster
    cluster_name = f"Cluster{cluster_id}"
    return len(
        pd.read_sql(
            CLUSTER_MEMBERS_QUERY.format(
                inflation=inflation, cluster_name=cluster_name
            ),
            con,
        )["node_ids"][0].split(",")
    )


GO_TERM_QUERY = """
SELECT "GO_terms"
FROM nodes
WHERE 1
    AND INSTR('{node_ids}', node_id) > 0
"""


def get_go_terms(node_ids):
    """ get the go terms by node_id """
    return pd.read_sql(GO_TERM_QUERY.format(node_ids=node_ids), con)


def go_terms_stats(node_ids):
    """ aggregate and rank the go terms by a list of node_ids """
    go_terms_raw = get_go_terms(node_ids)
    go_terms_flat = sum(
        [terms.split(", ") for terms in list(go_terms_raw["GO_terms"]) if terms], []
    )
    return Counter(go_terms_flat)


def go_terms_by_cluster(cluster_id, inflation):
    """ aggregate and rank the go terms for a given cluster """
    cluster_name = f"Cluster{cluster_id}"
    node_ids = pd.read_sql(
        CLUSTER_MEMBERS_QUERY.format(inflation=inflation, cluster_name=cluster_name),
        con,
    )["node_ids"][0]
    return go_terms_stats(node_ids)


def parse_cluster_name(cluster):
    """ take a cluster name and return its id and inflation """
    method, cluster_id = cluster.split(":")
    inflation = method[-1:]
    return cluster_id, inflation


def run(config, report):  # pylint: disable=too-many-locals
    """ run the kb_djornl app """
    params = config.get("params")
    shared = config.get("shared")
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree(
        "/kb/module/report/",
        os.path.join(reports_path),
    )
    subprocess.run(
        f"npm run build -- --mode production --output-path {reports_path}".split(" "),
        check=True,
    )

    # manifest
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    edge_types = {
        entry["path"]: entry["title"]
        for entry in manifest["file_list"]
        if entry["data_type"] == "edge"
    }
    print("edge_types", edge_types)
    # arango query
    re_client = REClient(
        "https://ci.kbase.us/services/relation_engine_api", os.environ["KB_AUTH_TOKEN"]
    )
    gene_keys = params.get("gene_keys", "").split(" ")
    distance = int(params.get("distance", 1))
    response = re_client.stored_query(
        "djornl_fetch_genes", dict(gene_keys=gene_keys, distance=distance)
    )
    nodes = response["results"][0]["nodes"]
    edges = response["results"][0]["edges"]

    def cytoscape_node(node):
        return dict(
            id=node["_id"],
            type="node",
            geneSymbol=node.get("gene_symbol", ""),
            GOTerms=node.get("go_terms", []),
            mapmanBin=node.get("mapman_bin", ""),
            mapmanName=node.get("mapman_name", ""),
            mapman=dict(
                bin=node.get("mapman_bin", ""),
                desc=node.get("mapman_desc"),
                name=node.get("mapman_name"),
            ),
        )

    def cytoscape_edge(edge):
        return dict(
            id=edge["_id"],
            edgeType=edge["edge_type"],
            source=edge["_from"],
            target=edge["_to"],
            type="edge",
        )

    # graph data
    cytoscape_nodes = [dict(data=cytoscape_node(node)) for node in nodes]
    cytoscape_edges = [dict(data=cytoscape_edge(edge)) for edge in edges]
    cytoscape_data = cytoscape_nodes + cytoscape_edges
    cytoscape_path = os.path.join(reports_path, "djornl.json")
    with open(cytoscape_path, "w") as cytoscape_json:
        cytoscape_json.write(json.dumps(cytoscape_data))
    # graph metadata
    cytoscape_metadata = dict(
        nodes=len(nodes),
        edges=len(edges),
    )
    cytoscape_metadata_path = os.path.join(reports_path, "djornl-metadata.json")
    with open(cytoscape_metadata_path, "w") as cytoscape_metadata_json:
        cytoscape_metadata_json.write(json.dumps(cytoscape_metadata))

    # cluster data
    ## nodes_requested === seed node
    nodes_requested = [
        node for node in nodes if check_gene_key_match(gene_keys, node["_id"])
    ]
    clusters_matched = sum([node["clusters"] for node in nodes_requested], [])
    cluster_infos = [parse_cluster_name(cluster) for cluster in clusters_matched]
    go_terms = {
        cluster_info: go_terms_by_cluster(*cluster_info)
        for cluster_info in cluster_infos
    }
    table = [
        (
            cluster_id,
            inflation,
            get_cluster_length((cluster_id, inflation)),
            go_terms[(cluster_id, inflation)].most_common(5),
        )
        for cluster_id, inflation in cluster_infos
    ]
    table_html = "\n".join(
        [
            "\n".join(
                ["<tr>", "\n".join([f"<td>{cell}</td>" for cell in row]), "</tr>"]
            )
            for row in table
        ]
    )
    table_content = f"<table>{table_html}</table>"
    print(table_content)
    title_genes = params.get("gene_keys", "")
    report_title = f"Arabidopsis thaliana genes: {title_genes}"
    env = Environment(loader=PackageLoader("kb_djornl", "templates"))
    template = env.get_template("index.html")
    ctx = template.new_context(vars=dict(content="", title=report_title))
    out = template.render(ctx)

    with open(os.path.join(reports_path, "index.html"), "w") as report_file:
        report_file.write(out)

    html_links = [
        {
            "description": "report",
            "name": "index.html",
            "path": reports_path,
        },
    ]
    report_info = report.create_extended_report(
        {
            "direct_html_link_index": 0,
            "html_links": html_links,
            "message": params["parameter_1"],
            "report_object_name": f"kb_checkv_report_{str(uuid.uuid4())}",
            "workspace_name": params["workspace_name"],
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }
