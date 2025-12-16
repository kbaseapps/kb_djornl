""" kb_djornl unit tests """
# -*- coding: utf-8 -*-
# pylint: disable=import-error
# pylint: disable=logging-fstring-interpolation
import json
import logging
import os
import shutil
import subprocess
import time
import unittest

from collections import defaultdict
from configparser import ConfigParser
from urllib.parse import urlparse

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeSearchUtilClient import GenomeSearchUtil
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.WorkspaceClient import Workspace

from kb_djornl.utils import fork_rwr_cv, fork_rwr_loe
from kb_djornl.kb_djornlImpl import kb_djornl
from kb_djornl.kb_djornlServer import MethodContext
from kb_djornl.authclient import KBaseAuth as _KBaseAuth


def echo(*args, **kwargs):
    """echo arguments"""
    logging.info(f"args: {args}")
    logging.info(f"kwargs: {kwargs}")
    return defaultdict(dict)


class EchoMock:  # pylint: disable=too-few-public-methods
    """echo mocker"""

    def __getattribute__(self, name):
        assert name
        return echo


class MockDFU:
    """mock dfu"""

    def save_objects(self, params):
        """mock dfu save_objects"""
        assert self, params
        return [[None] * 11]

    def ws_name_to_id(self, name):
        """mock workspace name to id"""
        assert self
        return len(name)

    def get_objects(self, params):
        """mock get_objects"""
        assert self
        ref = params["object_refs"][0]
        mock_filenames = dict(
            loe_seeds="./data/loe_seeds.ci.json",
            loe_targets="./data/loe_targets.ci.json",
        )
        # use the cv_seeds by default
        mock_filename = mock_filenames.get(ref, "./data/cv_seeds.ci.json")
        with open(mock_filename) as dfu_response_mock:
            results = json.load(dfu_response_mock)
        return results


class kb_djornlTest(unittest.TestCase):  # pylint: disable=invalid-name
    """kb_djornl unit test class"""

    @classmethod
    def setUpClass(cls):
        token = os.environ.get("KB_AUTH_TOKEN", None)
        config_file = os.environ.get("KB_DEPLOYMENT_CONFIG", None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items("kb_djornl"):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg["auth-service-url"]  # pylint: disable=invalid-name
        auth_client = _KBaseAuth(authServiceUrl)
        auth_service_url = urlparse(authServiceUrl)
        cls.env = auth_service_url.netloc.split(".")[0]
        logging.info(f"Detected environment: {cls.env}")
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update(
            {
                "token": token,
                "user_id": user_id,
                "provenance": [
                    {
                        "service": "kb_djornl",
                        "method": "please_never_use_it_in_production",
                        "method_params": [],
                    }
                ],
                "authenticated": 1,
            }
        )
        cls.wsURL = cls.cfg["workspace-url"]
        cls.wsClient = Workspace(cls.wsURL)
        cls.callback_url = os.environ["SDK_CALLBACK_URL"]
        cls.dfu = DataFileUtil(cls.callback_url)
        cls.gsu = GenomeSearchUtil(cls.callback_url)
        cls.serviceImpl = kb_djornl(cls.cfg)
        cls.scratch = cls.cfg["scratch"]
        cls.report = KBaseReport(cls.callback_url)
        cls.reports_path = os.path.join(cls.scratch, "reports")
        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_djornl_" + str(suffix)
        ret = cls.wsClient.create_workspace({"workspace": cls.wsName})
        cls.workspace_id = ret[0]
        with open("../ui/narrative/methods/run_rwr_cv/spec.json") as cv_spec:
            cls.spec_rwr_cv = json.load(cv_spec)
        with open("../ui/narrative/methods/run_rwr_loe/spec.json") as loe_spec:
            cls.spec_rwr_loe = json.load(loe_spec)
        env_featureset_ref = dict(appdev="61397/3/1", ci="59690/138/1")
        cls.seed0_ref = env_featureset_ref[cls.env]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "wsName"):
            cls.wsClient.delete_workspace({"workspace": cls.wsName})
            logging.info("Test workspace was deleted")

    def setUp(self):
        """remove report dir before each test"""
        # the scratch dir is named shared in kb_djornlImpl
        shutil.rmtree(self.reports_path, ignore_errors=True)

    def _get_multiplex_params(self, multiplex):
        """Make parameters for RWR_CV and RWR_LOE mutliplex tests"""
        return {
            "workspace_id": self.workspace_id,
            "workspace_name": self.wsName,
            "gene_keys": "ATCG00280 AT1G01100 AT1G18590",
            "multiplex": multiplex,
            "node_rank_max": "10",
            "output_name": f"genesMatched-{multiplex[:5]}",
        }

    """
    NOTE: According to Python unittest naming rules test method names should
    start with 'test'. The numbers determine the order for the tests. Tests
    with the same number may be run in any order. From the official unittest
    documentation:
    > The order in which the various tests will be run is determined by sorting
    > the test method names with respect to the built-in ordering for strings.
    """
    @unittest.skip("Skip test for debugging")
    def test_00_rwr_cv_multiplexes(self):
        """Run RWR CV on each available multiplex"""
        multiplexes = [
            option["value"]
            for option in [
                param
                for param in self.spec_rwr_cv["parameters"]
                if param["id"] == "multiplex"
            ][0]["dropdown_options"]["options"]
        ]

        for multiplex in multiplexes:
            with self.subTest(msg=f"Querying multiplex {multiplex}"):
                self.setUp()
                os.makedirs(self.reports_path, exist_ok=True)
                params = self._get_multiplex_params(multiplex)
                try:
                    fork_rwr_cv(self.reports_path, params, MockDFU())
                except subprocess.CalledProcessError:
                    logging.info(f"""Multiplex "{multiplex}" failed for RWR_CV.""")
                    continue

    @unittest.skip("Skip test for debugging")
    def test_01_run_rwr_cv(self):  # pylint: disable=too-many-locals
        """RWR CV test case"""
        ret = self.serviceImpl.run_rwr_cv(
            self.ctx,
            {
                "workspace_id": self.workspace_id,
                "workspace_name": self.wsName,
                # classic test
                # "gene_keys": "ATCG00280 AT1G01100 AT1G18590 X",
                "seeds_feature_set": self.seed0_ref,
                "multiplex": "High_Confidence_AT_d0.5_v01.RData",
                "node_rank_max": "10",
                "output_name": "genesMatched",
                "method": "kfold",
                "folds": "6",
                "restart": ".8",
                "tau": ".4,.8,1.2,1.6",
                # test for shadow gene ATCG00680
                # "gene_keys": (
                #     "ATCG00280 AT1G01100 AT1G18590 "
                #     "AT1G74100 AT2G27720 AT5G51545 "
                #     "AT4G00810 ATCG00350"
                # ),
                # "node_rank_max": "100",
            },
        )
        ref = ret[0]["report_ref"]
        out = self.wsClient.get_objects2({"objects": [{"ref": ref}]})
        report = out["data"][0]["data"]
        # Assert report name is index.html
        self.assertEqual(report["html_links"][0]["name"], "index.html")
        reports_zip_node_url = urlparse(report["html_links"][0]["URL"])
        reports_zip_node = reports_zip_node_url.path.split("/")[-1]
        reports_zip_path = os.path.join(self.scratch, "test/reports.zip")
        self.dfu.shock_to_file(
            dict(
                file_path=reports_zip_path,
                shock_id=reports_zip_node,
                unpack="unpack",
            )
        )
        graph_metadata_path = os.path.join(self.scratch, "test/graph-metadata.json")
        with open(graph_metadata_path) as graph_metadata_file:
            graph_metadata = json.load(graph_metadata_file)
        graph_state_objid = graph_metadata["objid"]
        graph_state_ref = f"{self.wsName}/{graph_state_objid}"
        graph_state_obj = self.dfu.get_objects({"object_refs": [graph_state_ref]})
        graph_state_json = graph_state_obj["data"][0]["data"]["description"]
        self.assertEqual(graph_state_json, "{}")
   
    @unittest.skip("Skip test for debugging")
    def test_00_run_rwr_loe_multiplexes(self):
        """Run RWR LOE on each available multiplex"""
        multiplexes = [
            option["value"]
            for option in [
                param
                for param in self.spec_rwr_loe["parameters"]
                if param["id"] == "multiplex"
            ][0]["dropdown_options"]["options"]
        ]
        for multiplex in multiplexes:
            with self.subTest(msg=f"Querying multiplex {multiplex}"):
                self.setUp()
                os.makedirs(self.reports_path, exist_ok=True)
                params = self._get_multiplex_params(multiplex)
                try:
                    fork_rwr_loe(self.reports_path, params, MockDFU())
                except subprocess.CalledProcessError:
                    logging.info(f"""Multiplex "{multiplex}" failed for RWR_LOE.""")
                    continue
    @unittest.skip("Skip test for debugging")
    def test_01_run_rwr_loe_context_analysis(self):
        """RWR LOE context_analysis test case"""
        self.serviceImpl.run_rwr_loe(
            self.ctx,
            {
                "workspace_name": self.wsName,
                "workspace_id": self.workspace_id,
                "seeds_feature_set": self.seed0_ref,
                "multiplex": "High_Confidence_AT_d0.5_v01.RData",
                "node_rank_max": "10",
                "output_name": "genesMatched",
                "restart": ".8",
                "tau": ".4,.8,1.2,1.6",
                "clients": {
                    "report": EchoMock(),
                    "dfu": MockDFU(),
                    "gsu": EchoMock(),
                },
            },
        )
    @unittest.skip("Skip test for debugging")
    def test_01_run_rwr_loe_target(self):
        """RWR LOE target test case"""
        self.serviceImpl.run_rwr_loe(
            self.ctx,
            {
                "workspace_id": self.workspace_id,
                "workspace_name": self.wsName,
                # results missing AT1G15550 AT1G02910 ??
                "seeds_feature_set": "loe_seeds",
                "targets_feature_set": "loe_targets",
                "multiplex": "High_Confidence_AT_d0.5_v01.RData",
                "node_rank_max": "200",
                "output_name": "genesMatched",
                "restart": ".8",
                "tau": ".4,.8,1.2,1.6",
                "clients": {
                    "report": EchoMock(),
                    "dfu": MockDFU(),
                    "gsu": EchoMock(),
                },
            },
        )

    def test_00_run_grin(self):
        """RWR GRIN test case"""
        self.serviceImpl.run_grin(
            self.ctx,
            {
                "workspace_id": self.workspace_id,
                "workspace_name": self.wsName,
                "feature_set_ref": "72238/42/1",
                "multiplex_id": "High_Confidence_AT_d0.5_v01.RData",
                "output_name": "grintest00",
                "restart": ".7",
                "tau_csv": "1,1,1,1",
                "clients": {
                    "report": EchoMock(),
                    "dfu": MockDFU(),
                    "gsu": EchoMock(),
                },
            },
        )
