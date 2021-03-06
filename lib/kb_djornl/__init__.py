""" kb_djornl code """

import configparser
import json
import os
import shutil
import sqlite3
import subprocess
import uuid

import pandas as pd
import yaml

from relation_engine_client import REClient

DATA_ROOT = os.environ.get("KBDJORNL_DATA_ROOT") or "/data/exascale_data/"

re_client = REClient(
    "https://ci.kbase.us/services/relation_engine_api", os.environ["KB_AUTH_TOKEN"]
)


def cytoscape_node(node, seed=False):
    """ convert nodedata into cytoscape format """
    return dict(
        id=node["_id"],
        geneSymbol=node.get("gene_symbol", ""),
        GOTerms=node.get("go_terms", []),
        transcripts=node.get("transcripts", []),
        mapmanInfos=node.get("mapman_infos", {}),
        seed=seed,
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


def genes_to_rwr_tsv(genes):
    """ convert a list of genes to a tsv string for use with RWR tools"""
    return "".join([f"report\t{gene}\n" for gene in genes])


def get_wsurl():
    """ Get the workspace url for this environment. """
    config_file = os.environ.get("KB_DEPLOYMENT_CONFIG")
    config_p = configparser.ConfigParser()
    config_p.read(config_file)
    return config_p["kb_djornl"]["workspace-url"]


def load_manifest():
    """ Load the manifest yaml file """
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    return manifest


def normalized_node_id(node_id):
    """ normalize node id """
    if "/" in node_id:
        return node_id.split("/")[1]
    return node_id


def object_info_as_dict(object_info):
    """ Convert a KBase object_info list into a dictionary. """
    [
        _id,
        _name,
        _type,
        _save,
        _version,
        _owner,
        _ws,
        _ws_name,
        _md5,
        _size,
        _meta,
    ] = object_info
    return dict(
        objid=_id,
        name=_name,
        type=_type,
        save_date=_save,
        ver=_version,
        saved_by=_owner,
        wsid=_ws,
        workspace=_ws_name,
        chsum=_md5,
        size=_size,
        meta=_meta,
    )


def put_graph_metadata(metadata, config):
    """Save graph metadata to a file
    Create a workspace state object.
    """
    dfu = config["dfu"]
    report_name = config["report_name"]
    reports_path = config["reports_path"]
    ws_name = config["ws_name"]
    # create object to store state metadata
    report_state_params = {
        "id": dfu.ws_name_to_id(ws_name),
        "objects": [
            {
                "type": "KBaseNarrative.Metadata-3.0",
                "name": f"{report_name}-state",
                "data": {
                    "data_dependencies": [],
                    "description": "{}",
                    "format": "JSON",
                },
            }
        ],
    }
    report_state = dfu.save_objects(report_state_params)
    report_state_objid = object_info_as_dict(report_state[0])["objid"]
    # add extra metadata
    metadata["objid"] = report_state_objid
    metadata["wsurl"] = get_wsurl()
    # save metadata
    metadata_path = os.path.join(reports_path, "graph-metadata.json")
    with open(metadata_path, "w") as metadata_json:
        metadata_json.write(json.dumps(metadata))


QUERY_EDGE = """SELECT *
	FROM "{table}"
	WHERE 1=0
		OR node1 in {nodes_sql}
		OR node2 in {nodes_sql}
"""
QUERY_NODE = """SELECT *
	FROM "{table}"
	WHERE node_id in {nodes_sql}
"""


def query_sqlite(genes):  # pylint: disable=too-many-locals
    """ Query the data loaded into sqlite3 based on seed genes """
    networks_path = os.path.join(DATA_ROOT, "networks.db")
    con = sqlite3.connect(networks_path)
    manifest = load_manifest()
    edge_tables = [
        entry["path"] for entry in manifest["file_list"] if entry["data_type"] == "edge"
    ]
    tmpl_id = "djornl_node/{}"
    edges = []
    seeds_sql = "".join(('("', '", "'.join(genes), '")'))
    for edge_table in edge_tables:
        query_edge = QUERY_EDGE.format(table=edge_table, nodes_sql=seeds_sql)
        edges_raw = pd.read_sql(query_edge, con).T
        edges.extend(
            [
                dict(
                    _from=tmpl_id.format(row["node1"]),
                    _id="djornl_edge/{}".format(
                        "-".join((row["node1"], row["node2"], row["edge_type"]))
                    ),
                    _to=tmpl_id.format(row["node2"]),
                    score=row["score"],
                    edge_type=row["edge_type"],
                )
                for ix, row in tuple(edges_raw.items())
            ]
        )
    # have to add all nodes from edges here
    nodes_all = tuple(
        frozenset(
            sum(
                [
                    (normalized_node_id(edge["_from"]), normalized_node_id(edge["_to"]))
                    for edge in edges
                ],
                (),
            )
        )
    )
    nodes_sql = "".join(('("', '", "'.join(nodes_all), '")'))
    query_node = QUERY_NODE.format(table="nodes", nodes_sql=nodes_sql)
    nodes_raw = pd.read_sql(query_node, con).T

    def cell_raw_process(cell):
        distinct = sorted(
            frozenset([json.dumps(item) for item in json.loads(cell) if item])
        )
        return [json.loads(item) for item in distinct]

    def node_row_clean(row):
        return dict(
            _id=tmpl_id.format(row["node_id"]),
            gene_symbol=row.get("gene_symbol", "") or "",
            go_terms=cell_raw_process(row["go_terms"]),
            mapman_infos=cell_raw_process(row["mapman_infos"]),
            transcripts=cell_raw_process(row["transcripts"]),
        )

    def node_shadow(node_id):
        return dict(
            _id=tmpl_id.format(node_id),
            mapman_infos=[],
        )

    nodes_data = {
        row["node_id"]: node_row_clean(row) for ix, row in tuple(nodes_raw.items())
    }

    nodes = [nodes_data.get(node_id, node_shadow(node_id)) for node_id in nodes_all]
    return [nodes, edges]


def re_subgraph(seeds, genes_top, output_path):
    """
    This function writes graph output
    get re output using djornl_fetch_genes stored query with distance 1
    """
    # get re output using djornl_fetch_genes stored query with distance 1
    genes = set(seeds + genes_top)
    seeds_set = frozenset(seeds)
    nodes_raw, edges_raw = query_sqlite(genes)
    # filter stored query for seed nodes (gene_keys) and ranked nodes
    nodes = [node for node in nodes_raw if normalized_node_id(node["_id"]) in genes]
    edges = [
        edge
        for edge in edges_raw
        if (
            normalized_node_id(edge["_from"]) in genes
            and normalized_node_id(edge["_to"]) in genes
        )
    ]

    def node_is_seed(node_id, seeds):
        return normalized_node_id(node_id) in seeds

    # graph data
    cytoscape_nodes = [
        dict(data=cytoscape_node(node, node_is_seed(node["_id"], seeds_set)))
        for node in nodes
    ]
    cytoscape_edges = [dict(data=cytoscape_edge(edge)) for edge in edges]
    cytoscape_data = dict(
        nodes=cytoscape_nodes,
        edges=cytoscape_edges,
    )
    cytoscape_path = os.path.join(output_path, "graph.json")
    with open(cytoscape_path, "w") as cytoscape_json:
        cytoscape_json.write(json.dumps(cytoscape_data))
    # graph metadata
    return dict(
        nodes=len(nodes),
        edges=len(edges),
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
    manifest = load_manifest()
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
    cytoscape_path = os.path.join(reports_path, "graph.json")
    with open(cytoscape_path, "w") as cytoscape_json:
        cytoscape_json.write(json.dumps(cytoscape_data))
    # graph metadata
    cytoscape_metadata = dict(
        nodes=len(nodes),
        edges=len(edges),
    )
    cytoscape_metadata_path = os.path.join(reports_path, "graph-metadata.json")
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
            "report_object_name": f"kb_djornl_report_{str(uuid.uuid4())}",
            "workspace_name": params["workspace_name"],
        }
    )
    return {
        "report_name": report_info["name"],
        "report_ref": report_info["ref"],
    }


def run_rwr_cv(
    config, report, dfu
):  # pylint: disable=too-many-locals too-many-statements
    """ run RWR_CV and generate a report """
    params = config.get("params")
    shared = config.get("shared")
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree("/opt/work/build/", reports_path)
    # manifest
    manifest = load_manifest()
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
    geneset_path = os.path.join(reports_path, "geneset.tsv")
    gene_keys = params.get("gene_keys", "").split(" ")
    with open(geneset_path, "w") as geneset_file:
        geneset_file.write(genes_to_rwr_tsv(gene_keys))
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
                --verbose
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
    # filter fullranks based on node_rank_max to get ranked nodes
    fullranks_limit = min(int(cv_folds), len(gene_keys)) * node_rank_max + 1
    with open(fullranks_path) as fullranks_tsv:
        fullranks_head = [next(fullranks_tsv) for i in range(fullranks_limit)]
    # get re output using djornl_fetch_genes stored query with distance 1
    genes_ranked_top = [
        line.split("\t")[0]
        for line in fullranks_head[1:]
        if int(line.split("\t")[2]) <= node_rank_max
    ]
    # Get subgraph to display from RE and save to file
    graph_metadata = re_subgraph(gene_keys, genes_ranked_top, reports_path)
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


def run_rwr_loe(config, report, dfu):  # pylint: disable=too-many-locals
    """ run RWR_LOE and generate a report """
    params = config.get("params")
    shared = config.get("shared")
    reports_path = os.path.join(shared, "reports")
    # include javascript app assets in report
    shutil.copytree("/opt/work/build/", reports_path)
    # manifest
    manifest = load_manifest()
    manifest_json_path = os.path.join(reports_path, "manifest.json")
    with open(manifest_json_path, "w") as manifest_json:
        manifest_json.write(json.dumps(manifest))
    geneset_path = os.path.join(reports_path, "geneset.tsv")
    gene_keys = params["gene_keys"].split(" ") if params["gene_keys"] else []
    with open(geneset_path, "w") as geneset_file:
        geneset_file.write(genes_to_rwr_tsv(gene_keys))
    gene_keys2 = []
    if "gene_keys2" in params and params["gene_keys2"]:
        gene_keys2 = params["gene_keys2"].split(" ")
    second_geneset = ""
    if gene_keys2:
        geneset2_path = os.path.join(reports_path, "geneset2.tsv")
        with open(geneset2_path, "w") as geneset2_file:
            geneset2_file.write(genes_to_rwr_tsv(gene_keys2))
        second_geneset = f"--geneset2='{geneset2_path}'"
    node_rank_max = int(params.get("node_rank_max", 10))
    loe_restart = params.get("restart", ".7")
    loe_tau = params.get("tau", "1")
    # run RWR_LOE
    rwrtools_env = dict(os.environ)
    rwrtools_data_path = "/data/RWRtools"
    if os.path.isdir(rwrtools_data_path):
        rwrtools_env["RWR_TOOLS_REPO"] = rwrtools_data_path
    rwrtools_env[
        "RWR_TOOLS_COMMAND"
    ] = f"""Rscript RWR_LOE.R
                --data='multiplexes/Athal_PPI_KO_PENEX_DOM.Rdata'
                --geneset1='{geneset_path}'
                {second_geneset}
                --restart='{loe_restart}'
                --tau='{loe_tau}'
                --modname=''
                --numranked='1'
                --outdir='/opt/work/tmp'
                --verbose
    """
    subprocess.run(
        ["/kb/module/scripts/rwrtools-run.sh"],
        check=True,
        env=rwrtools_env,
    )
    tsv_out = "data/RWR-LOE__.ranks.tsv"
    if second_geneset:
        tsv_out = "data/RWR-LOE_1v2_..ranks.tsv"
    output_path = os.path.join(reports_path, tsv_out)
    shutil.copytree(
        "/opt/work/tmp/",
        os.path.join(reports_path, "data"),
    )
    with open(output_path) as output_tsv:
        output_ranks_lines = output_tsv.readlines()

    def keyfunc(item):
        return int(item[2]) if item[2].isdecimal() else float("inf")

    output_ranks = sorted(
        [line.split("\t") for line in output_ranks_lines], key=keyfunc
    )
    genes_ranked_top = list(next(zip(*output_ranks[:node_rank_max])))
    # Get subgraph to display from RE and save to file
    graph_metadata = re_subgraph(gene_keys, gene_keys2 + genes_ranked_top, reports_path)
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
