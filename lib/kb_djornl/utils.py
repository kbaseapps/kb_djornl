""" kb_djornl utils """
import configparser
import json
import os
import sqlite3
import subprocess

import pandas as pd
import yaml

DATA_ROOT = os.environ.get("KBDJORNL_DATA_ROOT") or "/data/exascale_data/"


def create_tair10_featureset(
    genes, config, dfu, gsu
):  # pylint: disable=too-many-locals
    """Create an Arabidopsis thaliana featureset from a list of genes."""
    params = config.get("params")
    workspace_id = params["workspace_id"]
    genome_ref = "Phytozome_Genomes/Athaliana_TAIR10"
    genome_features = gsu.search(
        {
            "ref": genome_ref,
            "limit": len(genes),
            "structured_query": {"$or": [{"feature_id": gene} for gene in genes]},
            "sort_by": [["feature_id", True]],
        }
    )["features"]
    genes_found = {feature.get("feature_id") for feature in genome_features}
    genes_matched = [gene for gene in genes_found if gene in genes_found]
    genes_unmatched = set(genes).difference(genes_found)
    if len(genes_unmatched) > 0:
        genes_unmatched_str = ", ".join(genes_unmatched)
        print(
            """WARNING: The following genes were not found in the genome: """
            f"""{genes_unmatched_str}"""
        )
    new_feature_set = dict(
        description=params.get("description", ""),
        element_ordering=genes_matched,
        elements={gene: [genome_ref] for gene in genes_matched},
    )
    save_objects_params = {
        "id": workspace_id,
        "objects": [
            {
                "type": "KBaseCollections.FeatureSet",
                "data": new_feature_set,
                "name": params["output_name"],
            }
        ],
    }
    dfu_resp = dfu.save_objects(save_objects_params)[0]
    featureset_obj_ref = f"{dfu_resp[6]}/{dfu_resp[0]}/{dfu_resp[4]}"
    return [{"ref": featureset_obj_ref, "description": "Feature Set"}]


def cytoscape_node(node, rank, seed=False):
    """convert nodedata into cytoscape format"""
    return dict(
        defline=node["defline"],
        geneSymbols=node["gene_symbols"],
        GOInfos=node["go_infos"],
        id=node["_id"],
        KOEffects=node["ko_effects"],
        mapmanInfos=node["mapman_infos"],
        names=node["names"],
        rank=rank,
        seed=seed,
    )


def cytoscape_edge(edge):
    """convert edge data into cytoscape format"""
    return dict(
        id=edge["_id"],
        edgeType=edge["edge_type"],
        score=edge["score"],
        source=edge["_from"],
        target=edge["_to"],
    )


def fork_rwr_cv(reports_path, params, dfu):
    """Run the RWR_CV tool in a subproces."""
    # Extract parameters
    cv_multiplex = params["multiplex"]
    cv_method = params.get("method", "kfold")
    cv_folds = params.get("folds", "5")
    cv_restart = params.get("restart", ".7")
    cv_tau = params.get("tau", "1")
    featureset_ref = params.get("seeds_feature_set")
    gene_keys = get_genes_from_tair10_featureset(featureset_ref, dfu)
    # gene_keys = params.get("gene_keys", "").split(" ")
    # Write genes to a file to be used with RWR_CV.
    geneset_path = os.path.join(reports_path, "geneset.tsv")
    with open(geneset_path, "w") as geneset_file:
        geneset_file.write(genes_to_rwr_tsv(gene_keys))
    # Run RWR_CV
    rwrtools_env = dict(os.environ)
    rwrtools_data_path = "/data/RWRtools"
    if os.path.isdir(rwrtools_data_path):
        rwrtools_env["RWR_TOOLS_REPO"] = rwrtools_data_path
    rwrtools_env[
        "RWR_TOOLS_COMMAND"
    ] = f"""Rscript inst/scripts/run_cv.R
                --data='multiplexes/{cv_multiplex}'
                --geneset='{geneset_path}'
                --method='{cv_method}'
                --folds='{cv_folds}'
                --restart='{cv_restart}'
                --tau='{cv_tau}'
                --numranked='1'
                --outdir='/opt/work/tmp'
                --out-fullranks='/opt/work/tmp/fullranks.tsv'
                --out-medianranks='/opt/work/tmp/medianranks.tsv'
                --verbose
    """
    subprocess.run(
        "/kb/module/scripts/rwrtools-run.sh".split(" "),
        check=True,
        env=rwrtools_env,
    )
    return gene_keys, cv_folds


def fork_rwr_loe(reports_path, params, dfu):  # pylint: disable=too-many-locals
    """Run the RWR_LOE tool in a subproces."""
    loe_multiplex = params["multiplex"]
    loe_restart = params.get("restart", ".7")
    loe_tau = params.get("tau", "1")
    # Write genes to a file to be used with RWR_LOE.
    geneset_path = os.path.join(reports_path, "geneset.tsv")
    seeds_featureset_ref = params.get("seeds_feature_set")
    gene_keys = get_genes_from_tair10_featureset(seeds_featureset_ref, dfu)
    with open(geneset_path, "w") as geneset_file:
        geneset_file.write(genes_to_rwr_tsv(gene_keys))
    # Write the second set of genes to a file to be used with RWR_LOE.
    targets_featureset_ref = params.get("targets_feature_set")
    gene_keys2 = []
    if "targets_featureset_ref" in params and params["targets_featureset_ref"]:
        gene_keys2 = get_genes_from_tair10_featureset(targets_featureset_ref, dfu)
    query_geneset = ""
    if gene_keys2:
        geneset2_path = os.path.join(reports_path, "geneset2.tsv")
        with open(geneset2_path, "w") as geneset2_file:
            geneset2_file.write(genes_to_rwr_tsv(gene_keys2))
        query_geneset = f"--query_geneset='{geneset2_path}'"
    rwrtools_env = dict(os.environ)
    rwrtools_data_path = "/data/RWRtools"
    if os.path.isdir(rwrtools_data_path):
        rwrtools_env["RWR_TOOLS_REPO"] = rwrtools_data_path
    rwrtools_env[
        "RWR_TOOLS_COMMAND"
    ] = f"""Rscript inst/scripts/run_loe.R
                --data='multiplexes/{loe_multiplex}'
                --seed_geneset='{geneset_path}'
                {query_geneset}
                --restart='{loe_restart}'
                --tau='{loe_tau}'
                --numranked='1'
                --modname=''
                --outdir='/opt/work/tmp/'
                --verbose
    """
    subprocess.run(
        ["/kb/module/scripts/rwrtools-run.sh"],
        check=True,
        env=rwrtools_env,
    )
    return gene_keys, gene_keys2


def genes_to_rwr_tsv(genes):
    """convert a list of genes to a tsv string for use with RWR tools"""
    return "".join([f"report\t{gene}\n" for gene in genes])


def get_wsurl():
    """Get the workspace url for this environment."""
    config_file = os.environ.get("KB_DEPLOYMENT_CONFIG")
    config_p = configparser.ConfigParser()
    config_p.read(config_file)
    return config_p["kb_djornl"]["workspace-url"]


def get_genes_from_tair10_featureset(featureset_ref, dfu):
    """Read genes from a A. thaliana featureset."""
    featureset_response = dfu.get_objects({"object_refs": [featureset_ref]})
    featureset = featureset_response["data"][0]["data"]
    return featureset["element_ordering"]


def load_manifest():
    """Load the manifest yaml file"""
    manifest_path = os.path.join(DATA_ROOT, "prerelease/manifest.yaml")
    with open(manifest_path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    return manifest


def normalized_node_id(node_id):
    """normalize node id"""
    if "/" in node_id:
        return node_id.split("/")[1]
    return node_id


def object_info_as_dict(object_info):
    """Convert a KBase object_info list into a dictionary."""
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


def put_graph_metadata(metadata, config):  # pylint: disable=too-many-locals
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
    # Add extra metadata for the workspace.
    metadata["objid"] = report_state_objid
    metadata["wsurl"] = get_wsurl()
    # Save graph metadata.
    metadata_path = os.path.join(reports_path, "graph-metadata.json")
    with open(metadata_path, "w") as metadata_json:
        json.dump(metadata, metadata_json)
    # Copy edge-metadata into the reports directory.
    edge_metadata_source = os.path.join(DATA_ROOT, "edge-metadata.json")
    with open(edge_metadata_source) as edge_metadata_json:
        edge_metadata = json.load(edge_metadata_json)
    edge_metadata_path = os.path.join(reports_path, "edge-metadata.json")
    with open(edge_metadata_path, "w") as edge_metadata_json_out:
        json.dump(edge_metadata, edge_metadata_json_out)


QUERY_EDGE = """SELECT *
    FROM "{table}"
    WHERE 1=0
        OR node1 in {nodes_sql}
        OR node2 in {nodes_sql}
"""
QUERY_NODE = """SELECT "GID" as node_id, *
    FROM nodes
    WHERE "GID" in {nodes_sql}
"""


def query_sqlite(genes):  # pylint: disable=too-many-locals
    """Query the data loaded into sqlite3 based on seed genes"""
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
    query_node = QUERY_NODE.format(nodes_sql=nodes_sql)
    nodes_raw = pd.read_sql(query_node, con).T

    def node_row_clean(row):
        def cell_split(cell):
            return cell.split("|") if cell else []

        go_infos_raw = zip(cell_split(row["GO"]), cell_split(row["GOdesc"]))
        go_infos = [dict(term=term, desc=desc) for term, desc in go_infos_raw]
        mapman_infos_raw = zip(
            cell_split(row["mapman_code"]),
            cell_split(row["mapman_name"]),
            cell_split(row["mapman_desc"]),
        )
        mapman_infos = [
            dict(code=code, desc=desc, name=name)
            for code, name, desc in mapman_infos_raw
        ]

        return dict(
            _id=tmpl_id.format(row["node_id"]),
            defline=row["defline"],
            gene_symbols=cell_split(row["symbols"]),
            go_infos=go_infos,
            ko_effects=cell_split(row["KO_effect"]),
            names=cell_split(row["names"]),
            mapman_infos=mapman_infos,
        )

    def node_shadow(node_id, nodes_data):
        if node_id not in nodes_data:
            print(f"MISSING METADATA FOR {node_id}")
        return dict(
            _id=tmpl_id.format(node_id),
            defline="missing metadata",
            gene_symbols=[],
            go_infos=[],
            ko_effects=[],
            names=[],
            mapman_infos=[],
        )

    nodes_data = {
        row["GID"]: node_row_clean(row) for ix, row in tuple(nodes_raw.items())
    }
    nodes = [
        nodes_data.get(node_id, node_shadow(node_id, nodes_data))
        for node_id in nodes_all
    ]
    return [nodes, edges]


def query_subgraph(seeds, genes_top, output_path):  # pylint: disable=too-many-locals
    """
    This function queries the data, writes the resulting subgraph and returns a
    dictionary containing the number of nodes and edges.
    seeds: list
    genes_top: dict whose keys are genes and values are their ranks
    """
    genes_list = list(genes_top.keys())
    genes = set(seeds + genes_list)
    seeds_set = frozenset(seeds)
    # Produce the induced subgraph of genes in all networks.
    nodes_raw, edges_raw = query_sqlite(genes)
    # Only keep the nodes of interest.
    nodes = [node for node in nodes_raw if normalized_node_id(node["_id"]) in genes]
    edges = [
        edge
        for edge in edges_raw
        if (
            normalized_node_id(edge["_from"]) in genes
            and normalized_node_id(edge["_to"]) in genes
        )
    ]

    def node_is_seed(node_id):
        return normalized_node_id(node_id) in seeds_set

    # graph data
    cytoscape_nodes = [
        dict(
            data=cytoscape_node(
                node,
                genes_top.get(normalized_node_id(node["_id"])),
                seed=node_is_seed(node["_id"]),
            )
        )
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
