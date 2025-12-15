/*
A KBase module: kb_djornl
*/

module kb_djornl {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    funcdef run_rwr_cv(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_rwr_loe(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_grin(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;
};
