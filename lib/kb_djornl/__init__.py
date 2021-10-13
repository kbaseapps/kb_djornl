""" kb_djornl code """

import json
import operator
import os
import shutil
import uuid

import pandas as pd
import yaml

from .utils import (
    create_tair10_featureset,
    fork_rwr_cv,
    fork_rwr_loe,
    genes_to_rwr_tsv,
    load_manifest,
    put_graph_metadata,
    query_subgraph,
)


def run_rwr_cv(config, clients):  # pylint: disable=too-many-locals
    """ run RWR_CV and generate a report """
    params = config.get("params")
    shared = config.get("shared")
    dfu = clients["dfu"]
    gsu = clients["gsu"]
    report = clients["report"]
    reports_path = os.path.join(shared, "reports")
    # Include compiled Javascript app assets in report.
    shutil.copytree("/opt/work/build/", reports_path)
    # Load manifest and write to report.
    manifest = load_manifest()
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
    node_rank_max = int(params.get("node_rank_max", 10))
    # Run RWR_CV with the given parameters
    gene_keys, cv_folds = fork_rwr_cv(reports_path, params, dfu)
    fullranks_path = os.path.join(reports_path, "data/fullranks.tsv")
    medianranks_path = os.path.join(reports_path, "data/medianranks.tsv")
    shutil.copytree(
        "/opt/work/tmp/",
        os.path.join(reports_path, "data"),
    )
    # This limit is an upper bound since each fold could potentially have
    # entirely distinct genes with rank up to node_rank_max.
    fullranks_limit = min(int(cv_folds), len(gene_keys)) * node_rank_max + 1
    with open(fullranks_path) as fullranks_tsv:
        fullranks_head = [next(fullranks_tsv) for i in range(fullranks_limit)]
    # Filter fullranks based on node_rank_max to get ranked nodes.
    output_ranks = {
        line.split("\t")[0]: int(line.split("\t")[2])
        for line in fullranks_head[1:]
        if int(line.split("\t")[2]) <= node_rank_max
    }
    # Create a featureset object with these genes.
    genes_ranked_top = list(
        next(zip(*sorted(output_ranks.items(), key=operator.itemgetter(1))))
    )
    create_tair10_featureset(genes_ranked_top, config, dfu, gsu)
    # Get subgraph to display and save to file.
    graph_metadata = query_subgraph(gene_keys, output_ranks, reports_path)
    report_name = f"kb_rwr_cv_report_{str(uuid.uuid4())}"
    # Save graph metadata to a file in the report.
    ws_name = params["workspace_name"]
    put_graph_metadata(
        graph_metadata,
        dict(
            dfu=dfu,
            report_name=report_name,
            reports_path=reports_path,
            ws_name=ws_name,
        ),
    )
    # create report object
    html_links = [
        {
            "description": "report",
            "name": "index.html",
            "path": reports_path,
        },
        {
            "description": "fullranks",
            "name": "fullranks.tsv",
            "path": fullranks_path,
        },
        {
            "description": "medianranks",
            "name": "medianranks.tsv",
            "path": medianranks_path,
        },
    ]
    report_info = report.create_extended_report(
        {
            "direct_html_link_index": 0,
            "html_links": html_links,
            "message": (f"""Report for RWR_CV with rank <= {node_rank_max}"""),
            "report_object_name": report_name,
            "workspace_name": ws_name,
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }


def run_rwr_loe(
    config, clients
):  # pylint: disable=too-many-locals, too-many-statements
    """ run RWR_LOE and generate a report """
    params = config.get("params")
    shared = config.get("shared")
    dfu = clients["dfu"]
    gsu = clients["gsu"]
    report = clients["report"]
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree("/opt/work/build/", reports_path)
    # manifest
    manifest = load_manifest()
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
    node_rank_max = int(params.get("node_rank_max", 10))
    # Run RWR_LOE with the given parameters
    gene_keys, gene_keys2 = fork_rwr_loe(reports_path, params, dfu)
    tsv_out = "data/ranks.tsv"
    output_path = os.path.join(reports_path, tsv_out)
    shutil.copytree(
        "/opt/work/tmp/",
        os.path.join(reports_path, "data"),
    )
    with open(output_path) as output_tsv:
        output_ranks_lines = output_tsv.readlines()

    output_ranks = {
        line.split("\t")[0]: int(line.split("\t")[2])
        for line in output_ranks_lines[1:]
        if int(line.split("\t")[2]) <= node_rank_max
    }
    # Create a featureset object with these genes.
    genes_ranked_top = list(
        next(zip(*sorted(output_ranks.items(), key=operator.itemgetter(1))))
    )
    create_tair10_featureset(genes_ranked_top, config, dfu, gsu)
    genes_other = {genes_ranked_top[i]: i for i in range(node_rank_max)}
    # Put the target genes into the output
    for gene in gene_keys2:
        genes_other[gene] = None
    # Get subgraph to display and save to file.
    graph_metadata = query_subgraph(gene_keys, genes_other, reports_path)
    report_name = f"kb_rwr_loe_report_{str(uuid.uuid4())}"
    # Save graph metadata to a file in the report.
    ws_name = params["workspace_name"]
    put_graph_metadata(
        graph_metadata,
        dict(
            dfu=dfu,
            report_name=report_name,
            reports_path=reports_path,
            ws_name=ws_name,
        ),
    )
    # create report object
    html_links = [
        {
            "description": "report",
            "name": "index.html",
            "path": reports_path,
        },
        {
            "description": "ranks",
            "name": "ranks.tsv",
            "path": output_path,
        },
    ]
    report_info = report.create_extended_report(
        {
            "direct_html_link_index": 0,
            "html_links": html_links,
            "message": (f"""Report for RWR_CV with rank <= {node_rank_max}"""),
            "report_object_name": report_name,
            "workspace_name": ws_name,
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }
