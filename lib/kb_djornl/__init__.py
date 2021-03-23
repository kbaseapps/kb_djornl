""" kb_djornl code """

import json
import os
import shutil
import subprocess
import uuid

import yaml

from relation_engine_client import REClient

DATA_ROOT = "/opt/work/exascale_data/"


def cytoscape_node(node):
    """ convert nodedata into cytoscape format """
    return dict(
        id=node["_id"],
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
    """ convert edge data into cytoscape format """
    return dict(
        id=edge["_id"],
        edgeType=edge["edge_type"],
        score=edge["score"],
        source=edge["_from"],
        target=edge["_to"],
    )


def run(config, report):  # pylint: disable=too-many-locals
    """ run the kb_djornl app """
    params = config.get("params")
    shared = config.get("shared")
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree(
        "/opt/work/build/",
        os.path.join(reports_path),
    )
    # manifest
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
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

    # graph data
    cytoscape_nodes = [dict(data=cytoscape_node(node)) for node in nodes]
    cytoscape_edges = [dict(data=cytoscape_edge(edge)) for edge in edges]
    cytoscape_data = dict(
        nodes=cytoscape_nodes,
        edges=cytoscape_edges,
    )
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
            "message": """The magic words are `squeamish ossifrage`.""",
            "report_object_name": f"kb_checkv_report_{str(uuid.uuid4())}",
            "workspace_name": params["workspace_name"],
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }


def run_rwr_cv(config, report):  # pylint: disable=too-many-locals
    """ run RWR_CV and generate a report """
    params = config.get("params")
    shared = config.get("shared")
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree("/opt/work/build/", reports_path)
    # manifest
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
    geneset_path = os.path.join(reports_path, "geneset.tsv")
    gene_keys = params.get("gene_keys", "").split(" ")
    gene_keys_tsv = "".join([f"report\t{gene_key}\n" for gene_key in gene_keys])
    with open(geneset_path, "w") as geneset_file:
        geneset_file.write(gene_keys_tsv)
    node_rank_max = int(params.get("node_rank_max", 10))
    cv_method = params.get("method", "kfold")
    cv_folds = params.get("folds", "5")
    cv_restart = params.get("restart", ".7")
    cv_tau = params.get("tau", "1")
    # run RWR_CV
    rwrtools_env = dict(os.environ)
    rwrtools_data_path = "/data/RWRtools"
    if os.path.isdir(rwrtools_data_path):
        rwrtools_env["RWR_TOOLS_REPO"] = rwrtools_data_path
    rwrtools_env[
        "RWR_TOOLS_COMMAND"
    ] = f"""Rscript RWR_CV.R
                --data='multiplexes/Athal_PPI_KO_PENEX_DOM.Rdata'
                --geneset='{geneset_path}'
                --method='{cv_method}'
                --folds='{cv_folds}'
                --restart='{cv_restart}'
                --tau='{cv_tau}'
                --modname='report'
                --numranked='1'
                --outdir='/opt/work/tmp'
                --verbose='TRUE'
    """
    subprocess.run(
        "/kb/module/scripts/rwrtools-run.sh".split(" "),
        check=True,
        env=rwrtools_env,
    )
    tsv_out_tmpl = "data/RWR-CV_report_report_ARANET_PEN_PIN-PPI_KNOCKOUT.{}.tsv"
    fullranks_path = os.path.join(reports_path, tsv_out_tmpl.format("fullranks"))
    medianranks_path = os.path.join(reports_path, tsv_out_tmpl.format("medianranks"))
    shutil.copytree(
        "/opt/work/tmp/",
        os.path.join(reports_path, "data"),
    )
    # fake output data for now
    _id = f"djornl_node/{gene_keys[0]}"
    nodes = [dict(_id=_id) for gene_key in gene_keys]
    edges = [
        dict(
            _from=_id,
            _id="edge",
            _to=_id,
            edge_type="protein-protein-interaction_Mentha_A_thaliana_3702_040319",
            score=1,
        )
        for key in gene_keys
    ]
    # graph data
    cytoscape_nodes = [dict(data=cytoscape_node(node)) for node in nodes]
    cytoscape_edges = [dict(data=cytoscape_edge(edge)) for edge in edges]
    cytoscape_data = dict(
        nodes=cytoscape_nodes,
        edges=cytoscape_edges,
    )
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
            "report_object_name": f"kb_checkv_report_{str(uuid.uuid4())}",
            "workspace_name": params["workspace_name"],
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }
