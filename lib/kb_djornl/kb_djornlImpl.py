# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.KBaseReportClient import KBaseReport

from . import run, run_rwr_cv, run_rwr_loe
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
    GIT_COMMIT_HASH = "b9407fdd6d3f424209c12af493b529ff9f6a5a91"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_kb_djornl(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_djornl
        report = KBaseReport(self.callback_url, service_ver="dev")
        config = dict(
            params=params,
            shared=self.shared_folder,
        )
        output = run(config, report)
        #END run_kb_djornl

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_djornl return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_rwr_cv(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_rwr_cv
        report = KBaseReport(self.callback_url, service_ver="dev")
        dfu = DataFileUtil(self.callback_url)
        config = dict(
            params=params,
            shared=self.shared_folder,
        )
        output = run_rwr_cv(config, report, dfu)
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
        report = KBaseReport(self.callback_url, service_ver="dev")
        dfu = DataFileUtil(self.callback_url)
        config = dict(
            params=params,
            shared=self.shared_folder,
        )
        output = run_rwr_loe(config, report, dfu)
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
