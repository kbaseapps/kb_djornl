# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import uuid
import shlex
import subprocess
import json
import pandas as pd


from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeSearchUtilClient import GenomeSearchUtil
from installed_clients.KBaseReportClient import KBaseReport

from . import run_rwr_cv, run_rwr_loe

# Call R via your rwrtools env (matches your current setup)
RSCRIPT = "source activate rwrtools && Rscript"
GRIN_R  = "/kb/module/GRIN/R/GRIN.R"
#END_HEADER


class kb_djornl:
    '''
    Module Name:
    kb_djornl

    Module Description:
    A KBase module: kb_djornl
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    ######################################### noqa
    VERSION = "0.0.2"
    GIT_URL = "git@github.com:kbaseapps/kb_djornl.git"
    GIT_COMMIT_HASH = "c15a9bf9294b68e94c01d8c4abfb25340f944b7b"

    #BEGIN_CLASS_HEADER
    # Helper: parse Narrative checkboxes / text to bool
    def _boolish(self, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        return str(v).strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')

    # Helper: run a shell command and bubble up failures with log attached
    def _run_cmd(self, cmd):
        p = subprocess.run(
            cmd, shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if p.returncode != 0:
            raise RuntimeError(f"Command failed ({p.returncode}):\n{p.stdout}")
        return p.stdout

    def _get_genes_from_featureset(self, featureset_ref, dfu):
        """Read genes from a FeatureSet (expects 'element_ordering')."""
        featureset_response = dfu.get_objects({"object_refs": [featureset_ref]})
        featureset = featureset_response["data"][0]["data"]
        return featureset.get("element_ordering", [])

    # Helper: map built-in multiplex IDs -> baked-in file paths
    def _load_multiplexes(self):
        """Load the multiplex definitions"""
        multiplexes_path = os.path.join("/kb/module/data/multiplexes.json")
        with open(multiplexes_path) as multiplexes_file:
            multiplexes = json.load(multiplexes_file)
        return multiplexes

    def _builtin_multiplex_path(self, multiplex_id):
        mp = {
            "djornl_v1_10layer": "/kb/module/data/multiplex/djornl_v1_10layer.RData"
        }.get(multiplex_id)
        if not mp or not os.path.exists(mp):
            raise RuntimeError(f"Built-in multiplex '{multiplex_id}' missing at {mp}")
        return mp

    def _find_first_existing(self, paths):
        for p in paths:
            if p and os.path.exists(p):
                return p
        return None

    # def _read_grin_retained_gene_symbols(self, path):
    #     """
    #     Read GRIN retained table like:
    #       setid  gene_symbol  rank  weight  set
    #       arabi  AT5G...      1600  1       Retained

    #     Returns: de-duped list of gene_symbol in file order.
    #     Filters to rows where last column == 'Retained' (case-insensitive) when present.
    #     """
    #     if not path or not os.path.exists(path):
    #         return []

    #     genes = []
    #     seen = set()

    #     with open(path, "r", encoding="utf-8", errors="ignore") as fh:
    #         for line in fh:
    #             line = line.strip()
    #             if not line:
    #                 continue

    #             low = line.lower()
    #             if low.startswith("setid") or low.startswith("#"):
    #                 continue

    #             parts = line.split("\t") if "\t" in line else line.split()
    #             if len(parts) < 2:
    #                 continue

    #             gene = (parts[1] or "").strip()
    #             if not gene:
    #                 continue

    #             # If there's a "set/status" column, keep only Retained rows
    #             if len(parts) >= 5:
    #                 status = (parts[4] or "").strip().lower()
    #                 if status and status != "retained":
    #                     continue

    #             if gene not in seen:
    #                 seen.add(gene)
    #                 genes.append(gene)

    #     return genes

    # Inline report (same cell) with downloadable HTML and created objects
    def _to_shock_link(self, path, label=None):
        sid = self.dfu.file_to_shock({'file_path': path, 'make_handle': 0})['shock_id']
        return {
            'shock_id': sid,
            'name': os.path.basename(path),
            'label': label or os.path.basename(path),
        }

    def _mk_report_inline(self, ws, index_html_text=None, index_html_file=None,
                     attachments=None, message="", objects_created=None):
        html_links = []
        if index_html_file and os.path.exists(index_html_file):
            html_links = [self._to_shock_link(index_html_file, "HTML report")]


        file_links = [self._to_shock_link(p) for p in (attachments or []) if p and os.path.exists(p)]

        rp = {'workspace_name': ws, 'message': message, 'objects_created': objects_created or []}
        if html_links:
            rp.update({'html_links': html_links, 'direct_html_link_index': 0})
        else:
            rp['direct_html'] = index_html_text or "<html><body><pre>No HTML generated.</pre></body></html>"
        if file_links:
            rp['file_links'] = file_links

        rep = self.report.create_extended_report(rp)
        return {'report_name': rep['name'], 'report_ref': rep['ref']}


    # # Save a new FeatureSet from GRIN retained table by filtering the source FeatureSet
    # def _save_retained_feature_set(self, ws_name, source_fs_ref, retained_txt_path, output_name):
    #     if not retained_txt_path or not os.path.exists(retained_txt_path):
    #         return None, None

    #     # Read retained IDs from GRIN retained table (gene_symbol col)
    #     retained = self._read_grin_retained_gene_symbols(retained_txt_path)

    #     # Fallback: if file isn't in the GRIN table format, try first token per line
    #     if not retained:
    #         retained = []
    #         with open(retained_txt_path, "r", encoding="utf-8", errors="ignore") as fh:
    #             for line in fh:
    #                 tok = line.strip().split()
    #                 if tok and tok[0].lower() not in ("setid", "gene_symbol"):
    #                     retained.append(tok[0])

    #     retained_set = set(retained)
    #     if not retained_set:
    #         return None, None

    #     # Load source FeatureSet
    #     src_obj = self.dfu.get_objects({'object_refs': [source_fs_ref]})['data'][0]
    #     src_data = src_obj['data']
    #     src_info = src_obj['info']  # [obj_id, name, type, save_date, ver, saved_by, ws_id, ws_name, checksum, size, meta]
    #     src_name = src_info[1]

    #     # Filter element_ordering (preserve original order)
    #     element_ordering_in = src_data.get('element_ordering', [])
    #     element_ordering_out = [fid for fid in element_ordering_in if fid in retained_set]

    #     # If none matched (IDs mismatch), still allow saving as ordering=retained list
    #     # (but usually you'll want to ensure the input FS uses ATxG ids)
    #     if not element_ordering_out and retained:
    #         element_ordering_out = retained

    #     # Filter elements while preserving structure
    #     elements_in = src_data.get('elements')
    #     elements_out = {}
    #     if isinstance(elements_in, dict):
    #         for k, v in elements_in.items():
    #             if not isinstance(v, dict):
    #                 continue
    #             new_v = None
    #             if 'feature_ids' in v and isinstance(v['feature_ids'], list):
    #                 ids = [fid for fid in v['feature_ids'] if fid in retained_set]
    #                 if ids:
    #                     new_v = v.copy()
    #                     new_v['feature_ids'] = ids
    #             elif 'features' in v and isinstance(v['features'], list):
    #                 kept = []
    #                 for f in v['features']:
    #                     if isinstance(f, dict):
    #                         fid = f.get('feature_id') or f.get('id')
    #                         if isinstance(fid, str) and fid in retained_set:
    #                             kept.append(f)
    #                     elif isinstance(f, str) and f in retained_set:
    #                         kept.append(f)
    #                 if kept:
    #                     new_v = v.copy()
    #                     new_v['features'] = kept
    #             if new_v:
    #                 elements_out[k] = new_v

    #     new_data = {
    #         'description': f"GRIN retained subset of {src_name}",
    #         'element_ordering': element_ordering_out
    #     }
    #     if elements_out:
    #         new_data['elements'] = elements_out

    #     # Save new FeatureSet
    #     ws_id = self.dfu.ws_name_to_id(ws_name)
    #     safe_base = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in (output_name or 'GRIN'))
    #     new_name = f"{safe_base}.GRIN_retained"
    #     save_ret = self.dfu.save_objects({
    #         'id': ws_id,
    #         'objects': [{
    #             'type': 'KBaseCollections.FeatureSet',
    #             'data': new_data,
    #             'name': new_name
    #         }]
    #     })
    #     info = save_ret[0]  # obj_info tuple
    #     # ref = ws_id/obj_id/ver
    #     new_ref = f"{info[6]}/{info[0]}/{info[4]}"
    #     return new_ref, new_name


    def _create_tair10_featureset(
            self,genes, config, dfu, gsu):  # pylint: disable=too-many-locals
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
            logging.warning(
                """The following genes were not found in the genome: """
                f"""{genes_unmatched_str}"""
            )
        new_feature_set = dict(
            description=params.get("description", ""),
            element_ordering=genes_matched,
            elements={gene: [genome_ref] for gene in genes_matched},
        )
        print(new_feature_set)
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


    def _grin_to_genelist(self, tsv_path):
        return pd.read_csv(tsv_path, sep="\t", header=0).iloc[:, 1].dropna().tolist()
        
    

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.dfu = DataFileUtil(self.callback_url)
        self.gsu = GenomeSearchUtil(self.callback_url)
        self.report = KBaseReport(self.callback_url)
        self.shared_folder = config['scratch']
        self.clients = dict(report=self.report, dfu=self.dfu, gsu=self.gsu)
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_rwr_cv(self, ctx, params):
        """
        :param params: mapping<string, UnspecifiedObject>
        :returns: ReportResults {report_name, report_ref}
        """
        #BEGIN run_rwr_cv
        clients = params.get("clients")
        if not clients:
            clients = self.clients
        config = dict(params=params, shared=self.shared_folder)
        output = run_rwr_cv(config, clients)
        #END run_rwr_cv

        if not isinstance(output, dict):
            raise ValueError('Method run_rwr_cv return value output is not type dict as required.')
        return [output]

    def run_rwr_loe(self, ctx, params):
        """
        :param params: mapping<string, UnspecifiedObject>
        :returns: ReportResults {report_name, report_ref}
        """
        #BEGIN run_rwr_loe
        clients = params.get("clients")
        if not clients:
            clients = self.clients
        config = dict(params=params, shared=self.shared_folder)
        output = run_rwr_loe(config, clients)
        #END run_rwr_loe

        if not isinstance(output, dict):
            raise ValueError('Method run_rwr_loe return value output is not type dict as required.')
        return [output]

    def run_grin(self, ctx, params):
        """
        Run GRIN inside kb_djornl.
        Non-advanced: feature_set_ref (KBaseCollections.FeatureSet), multiplex_id, output_name.
        Advanced: restart, tau_csv (and any other flags you expose).
        """
        #BEGIN run_grin
        config = dict(params=params, shared=self.shared_folder)
        gsu = self.gsu
        dfu = self.dfu
        
        ws = params.get('workspace_name')
        if not ws:
            raise ValueError("workspace_name is required")

        fs_ref = params.get('feature_set_ref')
        if not fs_ref:
            raise ValueError("feature_set_ref (KBaseCollections.FeatureSet) is required")

        multiplex_id = params.get('multiplex_id')
        output_name = (params.get('output_name') or 'GRIN_Report').strip()

        # Advanced defaults
        restart = float(params.get('restart', 0.7))
        tau_csv = params.get('tau_csv', '1,1,1,1,1,1,1,1,1,1')

        # Scratch / output folder
        safe_label = "".join(c if c.isalnum() or c in ('-', '_') else "_" for c in output_name)
        outdir = os.path.join(self.shared_folder, f"{safe_label}_{uuid.uuid4().hex}")
        os.makedirs(outdir, exist_ok=True)

        # Build seed list TSV for GRIN (use FS content)
        genelist = self._get_genes_from_featureset(fs_ref, self.dfu)
        genes_tsv = os.path.join(self.shared_folder, f"geneset_{uuid.uuid4().hex}.tsv")
        with open(genes_tsv, "w", encoding="utf-8") as f:
            for gene in genelist:
                f.write(f"arabi\t{gene}\t1\n")  # (set_name, feature_id, weight)
        print(f"GRIN seed TSV: {genes_tsv}")

        # Multiplex
        multiplex_path = os.path.join("/data/RWRtools/multiplexes", multiplex_id)

        # Compose command in env var for GRIN-run.sh
        rwrtools_env = dict(os.environ)
        rwrtools_env["GRIN_COMMAND"] = f"""Rscript {GRIN_R}
  -d '{multiplex_path}'
  -g '{genes_tsv}'
  -r '{restart}'
  -t '{tau_csv}'
  -o '{outdir}'
"""
        subprocess.run(
            ["/kb/module/scripts/GRIN-run.sh"],
            check=True,
            env=rwrtools_env,
        )

        # --- Inline HTML report (same cell) ---
        html_dir = os.path.join(outdir, "html")
        os.makedirs(html_dir, exist_ok=True)
        index_html_path = os.path.join(html_dir, "index.html")

        # read log if present
        log_text = ""
        for pth in (os.path.join(outdir, "grin.log"),
                    os.path.join(outdir, "GRIN.log"),
                    os.path.join(outdir, "run.log")):
            if os.path.exists(pth):
                try:
                    with open(pth, "r", encoding="utf-8", errors="ignore") as fh:
                        log_text = fh.read()
                except Exception:
                    pass
                break

        grin_cmd_str = rwrtools_env.get("GRIN_COMMAND", "").strip()
        index_html_text = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>GRIN results</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
pre {{ white-space: pre-wrap; background: #f6f8fa; padding: .75rem; border-radius: 6px; }}
.box {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: .75rem; margin: .75rem 0; }}
</style></head><body>
<h2>GRIN finished</h2>
<div class="box"><h3>Summary</h3>
<ul>
<li><b>Multiplex:</b> {multiplex_id}</li>
<li><b>Restart (-r):</b> {restart}</li>
<li><b>Tau (-t):</b> {tau_csv}</li>
<li><b>Output folder:</b> {outdir}</li>
</ul></div>
<div class="box"><h3>Command</h3><pre>{grin_cmd_str or "(captured by GRIN-run.sh)"}</pre></div>
<div class="box"><h3>Log</h3><pre>{(log_text or "No log file was found.").strip()}</pre></div>
</body></html>
"""
        with open(index_html_path, "w", encoding="utf-8") as fh:
            fh.write(index_html_text)

        # Attach outputs if present
        attachments = []

        # Prefer GRIN default retained file name
        retained_candidates = [
            os.path.join(outdir, "GRIN__default__Retained_Genes.txt"),
            os.path.join(outdir, "retained_genes.txt"),
            os.path.join(outdir, "retained_genes.tsv"),
        ]
        retained_path = self._find_first_existing(retained_candidates)
        genes = self._grin_to_genelist(retained_path)
        print(f"GRIN retained genes: {len(genes)} found in {retained_path}")
        featureset_info = self._create_tair10_featureset(genes,config,dfu,gsu)
        print(f"Featureset info: {featureset_info}")
        print(genes)


        # Collect common sidecar files (add more as you discover GRIN outputs)
        sidecars = [
            "GRIN__default__Retained_Genes.txt",
            "GRIN__default__Removed_Genes.txt",
            "GRIN__default__Duplicates.txt",
            "GRIN__default__Not_In_Multiplex.txt",
            "retained_genes.txt",
            "removed_genes.txt",
            "duplicates.txt",
            "not_in_multiplex.txt",
        ]
        for fname in sidecars:
            fpath = os.path.join(outdir, fname)
            if os.path.exists(fpath):
                attachments.append(fpath)


        objects_created = featureset_info  # already in the correct [{ref,description}, ...] format


        # Inline report in same cell + downloadable HTML + created object(s)
        output = self._mk_report_inline(
            ws,
            index_html_text=index_html_text,
            index_html_file=index_html_path,
            attachments=attachments,
            message=f"GRIN completed: {safe_label}",
            objects_created=objects_created
        )
        #END run_grin

        if not isinstance(output, dict):
            raise ValueError('Method run_grin return value output is not type dict as required.')
        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
