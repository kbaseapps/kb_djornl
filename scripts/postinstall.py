#!/usr/bin/env python
"""
Postinstall script for JS report development
"""

import configparser
import os
import subprocess

from urllib.parse import urlparse

import requests


def download_assets(assets, endpoint, cookies):
    """Download assets from endpoint using cookies."""
    destination_path = "test_local/workdir/tmp/reports"
    for asset in assets:
        asset_url = endpoint._replace(path=asset).geturl()
        resp = requests.get(asset_url, cookies=cookies)
        print(f"GET {asset}: {resp.status_code}")
        if resp.status_code > 299:
            continue
        path = os.path.join(destination_path, asset[1:])
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        with open(path, "wb") as asset_file:
            asset_file.write(resp.content)


def load_config():
    """Get token and endpoint from configuration file."""
    with open("test_local/test.cfg") as test_cfg:
        config_string = "[kbase]\n" + test_cfg.read()
    config = configparser.ConfigParser()
    config.read_string(config_string)
    token = config["kbase"]["test_token"]
    kbase_endpoint = config["kbase"]["kbase_endpoint"]
    return token, kbase_endpoint


def main():
    """Run KBase tests, collect static assets and start server."""
    if os.environ.get("NO_POSTINSTALL"):
        print("Skipping postinstall script.")
        return
    print("Running KBase app tests.")
    token, kbase_endpoint = load_config()

    env = dict(os.environ)
    env["KB_AUTH_TOKEN"] = token
    subprocess.run("time kb-sdk test".split(" "), check=True, env=env)

    print("Loading KBase environment static assets")
    if not token:
        raise Exception("Please update your token in test_local/test.cfg.")
    with open("data/static.txt") as assets_file:
        assets = assets_file.read().split("\n")[:-1]
    if len(assets) == 0:
        print("No assets retrieved.")
    kbase_endpoint_url = urlparse(kbase_endpoint)
    asset_first = assets[0]
    kbase_url = kbase_endpoint_url._replace(path=asset_first).geturl()
    initial = requests.get(kbase_url, cookies=dict(kbase_session=token))
    narrative_session = initial.cookies.get("narrative_session")
    cookies = dict(kbase_session=token, narrative_session=narrative_session)
    download_assets(assets, kbase_endpoint_url, cookies)


if __name__ == "__main__":
    main()
