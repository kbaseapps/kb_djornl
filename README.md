# kb_djornl

This is a [KBase](https://kbase.us) module generated by the [KBase Software
Development Kit (SDK)](https://github.com/kbase/kb_sdk).

You will need to have the SDK installed to use this module. [Learn more about
the SDK and how to use it](https://kbase.github.io/kb_sdk_docs/).

You can also learn more about the apps implemented in this module from its
[catalog page](https://narrative.kbase.us/#catalog/modules/kb_djornl) or its
[spec file](kb_djornl.spec).

# Setup and test

Add your KBase developer token to `test_local/test.cfg` and run the following:

```bash
$ make
$ kb-sdk test
```

After making any additional changes to this repo, run `kb-sdk test` again to
verify that everything still works.

# Installation from another module

To use this code in another SDK module, call `kb-sdk install kb_djornl` in the
other module's root directory.

# Contributing

Note: By default the module image uses Python 3.7.0, and these instructions are
tested with this version, but will probably work with any higher version.
Follow the following instructions to configure your development environment.

0. Install prerequisites:
    - kb-sdk
    - node >= 14.15.4
    - python >= 3.7.0
1. Make a virtual environment and activate it.
```
python -m venv $VENV
source $VENV/bin/activate
```
2. Install Python requirements:
```
pip install \
    --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt
```
2. Run `kb-sdk test`. This will generate a sample report.
3. Install JS requirements:
```
npm install
```
4. Start a server to serve the sample report:
```
npm run serve
```
By default this server listens on port 8080, but you can specify any port with
the following invocation:
```
npm run serve -- --port $PORT
```
5. (Optional) Enable the pre-commit hooks:
```
cp scripts/pre-commit.sh .git/hooks/pre-commit
```

# Help

You may find the answers to your questions in our [FAQ][kbase-faq] or
[Troubleshooting Guide](kbase-troubleshooting).
[kbase-faq]: https://kbase.github.io/kb_sdk_docs/references/questions_and_answers.html
[kbase-troubleshooting]: https://kbase.github.io/kb_sdk_docs/references/troubleshooting.html
