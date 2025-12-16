# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import uuid
import shlex
import subprocess
import json

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

    def _read_grin_retained_gene_symbols(self, path):
        """
        Read GRIN retained table like:
          setid  gene_symbol  rank  weight  set
          arabi  AT5G...      1600  1       Retained

        Returns: de-duped list of gene_symbol in file order.
        Filters to rows where last column == 'Retained' (case-insensitive) when present.
        """
        if not path or not os.path.exists(path):
            return []

        genes = []
        seen = set()

        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue

                low = line.lower()
                if low.startswith("setid") or low.startswith("#"):
                    continue

                parts = line.split("\t") if "\t" in line else line.split()
                if len(parts) < 2:
                    continue

                gene = (parts[1] or "").strip()
                if not gene:
                    continue

                # If there's a "set/status" column, keep only Retained rows
                if len(parts) >= 5:
                    status = (parts[4] or "").strip().lower()
                    if status and status != "retained":
                        continue

                if gene not in seen:
                    seen.add(gene)
                    genes.append(gene)

        return genes

    # Inline report (same cell) with downloadable HTML and created objects
    def _mk_report_inline(self, ws, index_html_text, index_html_file, attachments, message, objects_created=None):
        """
        Create a KBase extended report that renders HTML inline AND provides downloadable artifacts.

        Current KBaseReport validation requires:
          - if 'html_links' is provided, 'direct_html_link_index' must be set.
        So we upload index.html into html_links[0] and set direct_html_link_index=0.
        """
        html_links, file_links = [], []

        # Upload HTML file (index.html) as Shock + html_links
        if index_html_file and os.path.exists(index_html_file):
            index_sid = self.dfu.file_to_shock(
                {'file_path': index_html_file, 'make_handle': 0}
            )['shock_id']
            html_links.append({
                'shock_id': index_sid,
                'name': 'index.html',
                'label': 'Download HTML report'
            })

        # Upload extra files (retained/removed lists, etc.)
        for f in attachments or []:
            if f and os.path.exists(f):
                sid = self.dfu.file_to_shock({'file_path': f, 'make_handle': 0})['shock_id']
                file_links.append({
                    'shock_id': sid,
                    'name': os.path.basename(f),
                    'label': os.path.basename(f)
                })

        # Build report params safely (only include lists if non-empty)
        report_params = {
            'workspace_name': ws,
            'objects_created': objects_created or [],
            'message': message
        }

        # Prefer html_links + direct_html_link_index for inline rendering
        if html_links:
            report_params['html_links'] = html_links
            report_params['direct_html_link_index'] = 0
        else:
            # Fallback: if for some reason we couldn't upload index.html
            report_params['direct_html'] = index_html_text or "<html><body><pre>No HTML was generated.</pre></body></html>"

        if file_links:
            report_params['file_links'] = file_links

        rep = self.report.create_extended_report(report_params)
        return {'report_name': rep['name'], 'report_ref': rep['ref']}

    # Save a new FeatureSet from GRIN retained table by filtering the source FeatureSet
    def _save_retained_feature_set(self, ws_name, source_fs_ref, retained_txt_path, output_name):
        if not retained_txt_path or not os.path.exists(retained_txt_path):
            return None, None

        # Read retained IDs from GRIN retained table (gene_symbol col)
        retained = self._read_grin_retained_gene_symbols(retained_txt_path)

        # Fallback: if file isn't in the GRIN table format, try first token per line
        if not retained:
            retained = []
            with open(retained_txt_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    tok = line.strip().split()
                    if tok and tok[0].lower() not in ("setid", "gene_symbol"):
                        retained.append(tok[0])

        retained_set = set(retained)
        if not retained_set:
            return None, None

        # Load source FeatureSet
        src_obj = self.dfu.get_objects({'object_refs': [source_fs_ref]})['data'][0]
        src_data = src_obj['data']
        src_info = src_obj['info']  # [obj_id, name, type, save_date, ver, saved_by, ws_id, ws_name, checksum, size, meta]
        src_name = src_info[1]

        # Filter element_ordering (preserve original order)
        element_ordering_in = src_data.get('element_ordering', [])
        element_ordering_out = [fid for fid in element_ordering_in if fid in retained_set]

        # If none matched (IDs mismatch), still allow saving as ordering=retained list
        # (but usually you'll want to ensure the input FS uses ATxG ids)
        if not element_ordering_out and retained:
            element_ordering_out = retained

        # Filter elements while preserving structure
        elements_in = src_data.get('elements')
        elements_out = {}
        if isinstance(elements_in, dict):
            for k, v in elements_in.items():
                if not isinstance(v, dict):
                    continue
                new_v = None
                if 'feature_ids' in v and isinstance(v['feature_ids'], list):
                    ids = [fid for fid in v['feature_ids'] if fid in retained_set]
                    if ids:
                        new_v = v.copy()
                        new_v['feature_ids'] = ids
                elif 'features' in v and isinstance(v['features'], list):
                    kept = []
                    for f in v['features']:
                        if isinstance(f, dict):
                            fid = f.get('feature_id') or f.get('id')
                            if isinstance(fid, str) and fid in retained_set:
                                kept.append(f)
                        elif isinstance(f, str) and f in retained_set:
                            kept.append(f)
                    if kept:
                        new_v = v.copy()
                        new_v['features'] = kept
                if new_v:
                    elements_out[k] = new_v

        new_data = {
            'description': f"GRIN retained subset of {src_name}",
            'element_ordering': element_ordering_out
        }
        if elements_out:
            new_data['elements'] = elements_out

        # Save new FeatureSet
        ws_id = self.dfu.ws_name_to_id(ws_name)
        safe_base = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in (output_name or 'GRIN'))
        new_name = f"{safe_base}.GRIN_retained"
        save_ret = self.dfu.save_objects({
            'id': ws_id,
            'objects': [{
                'type': 'KBaseCollections.FeatureSet',
                'data': new_data,
                'name': new_name
            }]
        })
        info = save_ret[0]  # obj_info tuple
        # ref = ws_id/obj_id/ver
        new_ref = f"{info[6]}/{info[0]}/{info[4]}"
        return new_ref, new_name
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

        # --- Create a FeatureSet from retained genes (subset of the input FeatureSet) ---
        fs_new_ref, fs_new_name = (None, None)
        if retained_path:
            fs_new_ref, fs_new_name = self._save_retained_feature_set(ws, fs_ref, retained_path, output_name)

        objects_created = []
        if fs_new_ref and fs_new_name:
            objects_created.append({'ref': fs_new_ref, 'description': f"GRIN retained FeatureSet ({fs_new_name})"})
        else:
            logging.warning("No retained FeatureSet created (retained_path missing or no retained IDs matched).")

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
