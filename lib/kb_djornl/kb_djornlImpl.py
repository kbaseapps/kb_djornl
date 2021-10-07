# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeSearchUtilClient import GenomeSearchUtil
from installed_clients.KBaseReportClient import KBaseReport

from . import run_rwr_cv, run_rwr_loe
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
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
