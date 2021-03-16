""" kb_djornl unit tests """
# -*- coding: utf-8 -*-
import os
import time
import shutil
import unittest
from configparser import ConfigParser
from pprint import pprint

from installed_clients.WorkspaceClient import Workspace  # pylint: disable=import-error

from kb_djornl.kb_djornlImpl import kb_djornl  # pylint: disable=import-error
from kb_djornl.kb_djornlServer import MethodContext  # pylint: disable=import-error
from kb_djornl.authclient import (  # pylint: disable=import-error,no-name-in-module
    KBaseAuth as _KBaseAuth,
)


class kb_djornlTest(unittest.TestCase):  # pylint: disable=invalid-name
    """ kb_djornl unit test class """

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
        cls.serviceImpl = kb_djornl(cls.cfg)
        cls.scratch = cls.cfg["scratch"]
        cls.callback_url = os.environ["SDK_CALLBACK_URL"]
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace(  # noqa pylint: disable=unused-variable
            {"workspace": cls.wsName}
        )

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "wsName"):
            cls.wsClient.delete_workspace({"workspace": cls.wsName})
            print("Test workspace was deleted")

    def setUp(self):
        """ remove report dir before each test"""
        # the scratch dir is named shared in kb_djornlImpl
        shutil.rmtree(os.path.join(self.scratch, "reports"), ignore_errors=True)

    # NOTE: According to Python unittest naming rules test method names should
    # start with 'test'.
    def test_run_kb_djornl(self):
        """test case"""
        param = """The magic words are `squeamish ossifrage`."""
        ret = self.serviceImpl.run_kb_djornl(
            self.ctx,
            {
                "workspace_name": self.wsName,
                # "distance": "1", "gene_keys": "ATCG00280",  # 7 nodes, 19 edges
                "distance": "2",
                "gene_keys": "ATCG00280",  # 49 nodes, 135 edges
                # 23 nodes, 52 egdes
                # "distance": "1", "gene_keys": "AT1G01100 AT1G18590",
                # 1599 nodes, 25135 edges
                # "distance": "2", "gene_keys": "AT1G01100 AT1G18590",
                # "distance": "1", "gene_keys": "AT3G13175",  # 125 nodes, 478 edges
                # "distance": "1", "gene_keys": "AT1G17280",  # 464 nodes, 2776 edges
                # "distance": "2", "gene_keys": "AT3G13175",  # 1500 nodes, 23729 edges
            },
        )
        ref = ret[0]["report_ref"]
        out = self.wsClient.get_objects2({"objects": [{"ref": ref}]})
        report = out["data"][0]["data"]
        print(f">>>>>>>REPORT, ref: {ref}")
        pprint(report)
        self.assertEqual(out["data"][0]["data"]["text_message"], param)

    def test_run_rwr_cv(self):
        """test case"""
        ret = self.serviceImpl.run_rwr_cv(
            self.ctx,
            {
                "workspace_name": self.wsName,
                "gene_keys": "ATCG00280",
                "node_rank_max": "10",
            },
        )
        ref = ret[0]["report_ref"]
        out = self.wsClient.get_objects2({"objects": [{"ref": ref}]})
        report = out["data"][0]["data"]
        print(f">>>>>>>REPORT, ref: {ref}")
        pprint(report)
        self.assertEqual(report["html_links"][0]["name"], "index.html")
