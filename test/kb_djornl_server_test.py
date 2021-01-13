""" kb_djornl unit tests """
# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser
from pprint import pprint

from installed_clients.WorkspaceClient import Workspace

from kb_djornl.kb_djornlImpl import kb_djornl
from kb_djornl.kb_djornlServer import MethodContext
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

    # NOTE: According to Python unittest naming rules test method names should
    # start from 'test'. # noqa
    def test_your_method(self):
        """test case"""
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        param = """The magic words are `squeamish ossifrage`."""
        ret = self.serviceImpl.run_kb_djornl(
            self.ctx,
            {
                "workspace_name": self.wsName,
                "gene_keys": "AT1G01100 AT1G18590",
                "distance": "1",
                "parameter_1": param,
            },
        )
        ref = ret[0]["report_ref"]
        out = self.wsClient.get_objects2({"objects": [{"ref": ref}]})
        report = out["data"][0]["data"]
        print(f">>>>>>>REPORT, ref: {ref}")
        pprint(report)
        self.assertEqual(out["data"][0]["data"]["text_message"], param)
