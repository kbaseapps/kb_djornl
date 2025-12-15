# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import uuid
import shlex
import subprocess

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeSearchUtilClient import GenomeSearchUtil
from installed_clients.KBaseReportClient import KBaseReport

from . import run_rwr_cv, run_rwr_loe

# Call R via micromamba 'grin' env
RSCRIPT = "/usr/local/bin/micromamba run -n grin Rscript"
GRIN_R  = "/opt/GRIN/R/GRIN.R"
#END_HEADER


class kb_djornl:
    '''
    Module Name:
    kb_djornl

    Module Description:
    A KBase module: kb_djornl
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
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

    # Helper: FeatureSet -> GRIN TSV (set_name<TAB>feature_id)
    def _feature_set_to_geneset_tsv(self, fs_ref, scratch_dir, set_name_hint=None):
        objs = self.dfu.get_objects2({'objects': [{'ref': fs_ref}]})['data']
        if not objs:
            raise ValueError(f"FeatureSet not found: {fs_ref}")
        obj = objs[0]
        data = obj['data']
        info = obj['info']  # [obj_id, name, type, save_date, ver, saved_by, ws_id, ws_name, checksum, size, meta]
        fs_name = info[1]
        set_name = (set_name_hint or fs_name or "FeatureSet").strip()

        feats = set()
        elements = data.get('elements') or data.get('feature_ids') or {}
        if isinstance(elements, dict):
            for _, v in elements.items():
                if isinstance(v, dict):
                    if 'feature_id' in v and isinstance(v['feature_id'], str):
                        feats.add(v['feature_id'])
                    if 'feature_ids' in v and isinstance(v['feature_ids'], list):
                        feats.update([x for x in v['feature_ids'] if isinstance(x, str)])
                    if 'features' in v and isinstance(v['features'], list):
                        for f in v['features']:
                            if isinstance(f, dict):
                                fid = f.get('feature_id') or f.get('id')
                                if isinstance(fid, str):
                                    feats.add(fid)
                            elif isinstance(f, str):
                                feats.add(f)
                elif isinstance(v, list):
                    for f in v:
                        if isinstance(f, dict):
                            fid = f.get('feature_id') or f.get('id')
                            if isinstance(fid, str):
                                feats.add(fid)
                        elif isinstance(f, str):
                            feats.add(f)
        elif isinstance(elements, list):
            for f in elements:
                if isinstance(f, dict):
                    fid = f.get('feature_id') or f.get('id')
                    if isinstance(fid, str):
                        feats.add(fid)
                elif isinstance(f, str):
                    feats.add(f)

        if not feats:
            raise ValueError(f"No feature IDs found in FeatureSet {fs_ref}")

        out_path = os.path.join(scratch_dir, f"geneset_{uuid.uuid4().hex}.tsv")
        with open(out_path, "w") as fh:
            for fid in sorted(feats):
                fh.write(f"{set_name}\t{fid}\n")
        return out_path

    # Helper: map built-in multiplex IDs -> baked-in file paths
    def _builtin_multiplex_path(self, multiplex_id):
        mp = {
            "djornl_v1_10layer": "/kb/module/data/multiplex/djornl_v1_10layer.RData"
        }.get(multiplex_id)
        if not mp or not os.path.exists(mp):
            raise RuntimeError(f"Built-in multiplex '{multiplex_id}' missing at {mp}")
        return mp

    # Helper: create report with zipped HTML + file attachments
    def _mk_report(self, ws, html_dir, attachments, message):
        html_links, file_links = [], []

        # Zip HTML dir and upload
        zip_path = self.dfu.pack_file({
            'file_path': html_dir,
            'pack': 'zip',
            'output_file_name': f"{os.path.basename(html_dir)}.zip"
        })['file_path']
        html_sid = self.dfu.file_to_shock({'file_path': zip_path, 'make_handle': 0})['shock_id']
        html_links.append({'shock_id': html_sid, 'name': 'index.html', 'label': 'Open report'})

        # Upload attachments (if present)
        for f in attachments or []:
            if os.path.exists(f):
                sid = self.dfu.file_to_shock({'file_path': f, 'make_handle': 0})['shock_id']
                file_links.append({'shock_id': sid, 'name': os.path.basename(f), 'label': os.path.basename(f)})

        rep = self.report.create_extended_report({
            'workspace_name': ws,
            'message': message,
            'direct_html_link_index': 0 if html_links else None,
            'html_links': html_links,
            'file_links': file_links
        })
        return {'report_name': rep['name'], 'report_ref': rep['ref']}
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
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
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_rwr_cv
        clients = params.get("clients")
        if not clients:
            clients = self.clients
        config = dict(
            params=params,
            shared=self.shared_folder,
        )
        output = run_rwr_cv(config, clients)
        #END run_rwr_cv

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_rwr_cv return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_rwr_loe(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_rwr_loe
        clients = params.get("clients")
        if not clients:
            clients = self.clients
        config = dict(
            params=params,
            shared=self.shared_folder,
        )
        output = run_rwr_loe(config, clients)
        #END run_rwr_loe

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_rwr_loe return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_grin(self, ctx, params):
        """
        Run GRIN inside kb_djornl.
        UI (non-advanced): feature_set_ref (KBaseCollections.FeatureSet),
                           multiplex_id (built-in only),
                           output_name.
        Advanced: restart, tau_csv, verbosity, plot, simple_filenames.
        """
        # return variables are: output
        #BEGIN run_grin
        ws = params.get('workspace_name')
        if not ws:
            raise ValueError("workspace_name is required")

        fs_ref = params.get('feature_set_ref')
        if not fs_ref:
            raise ValueError("feature_set_ref (KBaseCollections.FeatureSet) is required")

        multiplex_id = (params.get('multiplex_id') or 'djornl_v1_10layer').strip()
        output_name = (params.get('output_name') or 'GRIN_Report').strip()

        # Advanced defaults
        restart = float(params.get('restart', 0.7))
        tau_csv = params.get('tau_csv', '1,1,1,1,1,1,1,1,1,1')
        verbosity = int(params.get('verbosity', 0))
        plot_flag = '-p' if self._boolish(params.get('plot')) else ''
        simple_flag = '-s' if self._boolish(params.get('simple_filenames', 1)) else ''
        verbose_flag = '-v' if verbosity > 0 else ''

        # Output dir in scratch
        safe_label = "".join(c if c.isalnum() or c in ('-', '_') else "_" for c in output_name)
        outdir = os.path.join(self.shared_folder, f"{safe_label}_{uuid.uuid4().hex}")
        os.makedirs(outdir, exist_ok=True)

        # Convert FeatureSet -> TSV expected by GRIN (use FS name as set_name)
        geneset_tsv = self._feature_set_to_geneset_tsv(fs_ref, self.shared_folder, set_name_hint=None)

        # Built-in multiplex only
        multiplex = self._builtin_multiplex_path(multiplex_id)

        # Build GRIN command (no run label, no threads)
        cmd = (
            f"{RSCRIPT} {shlex.quote(GRIN_R)} "
            f"-d {shlex.quote(multiplex)} "
            f"-g {shlex.quote(geneset_tsv)} "
            f"-r {restart} "
            f"-t {shlex.quote(tau_csv)} "
            f"-o {shlex.quote(outdir)} "
            f"{plot_flag} {simple_flag} {verbose_flag}"
        )

        # Execute and capture log
        log = self._run_cmd(cmd)

        # Create minimal HTML report (command + log)
        html_dir = os.path.join(outdir, "html")
        os.makedirs(html_dir, exist_ok=True)
        with open(os.path.join(html_dir, "index.html"), "w") as fh:
            fh.write("<h2>GRIN finished</h2>\n<h3>Command</h3>\n")
            fh.write(f"<pre>{cmd}</pre>\n<h3>Log</h3>\n<pre>{log}</pre>\n")

        # Attach common outputs if present
        attachments = []
        for fname in ("retained_genes.txt", "removed_genes.txt",
                      "duplicates.txt", "not_in_multiplex.txt"):
            fpath = os.path.join(outdir, fname)
            if os.path.exists(fpath):
                attachments.append(fpath)

        output = self._mk_report(
            ws, html_dir, attachments, message=f"GRIN completed: {safe_label}"
        )
        #END run_grin

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_grin return value ' +
                             'output is not type dict as required.')
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
