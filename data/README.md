# data

This directory contains any reference data required for this module to run.

For any reference data that is too large to host on Github (greater than
100MB), follow the [Reference Data Guide][ref-data-guide] for an alternative.

[ref-data-guide]: https://kbase.github.io/kb_sdk_docs/howtos/work_with_reference_data.html

## rwrtools.yml

The conda environment description to run RWRtools. This will go away once
RWRtools are published.

## static.txt

A list of static assets required for this report to run locally.
Each line is a path to an asset in a KBase environment. For example,
    /narrative/static/style/style.min.css
refers to
    https://narrative.kbase.us/narrative/static/style/style.min.css
in the production environment.
