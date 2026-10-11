"""Download primary data into data/raw/<source>/ and log it in data/raw/MANIFEST.csv.

Files are stored exactly as served (never edited). Re-running skips files
already present unless --force is given. Approved by the authors on 2026-10-08.
"""
import argparse
import csv
import datetime as dt
import hashlib
import os
import sys
import time

import requests

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")
UA = {"User-Agent": "Mozilla/5.0 (research data download; emcorr model)"}
IMF_C = "GRC/CYP/ISR/EGY/TUR/JOR/LBN/ALB/BGR/MKD/MNE/UVK/SRB/BIH/HRV/ROU/SVN/ITA"

FILES = {
    "ember": ("https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv",
              "release_generation_yearly_global.csv"),
    "worldbank": ("https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx",
                  "CMO-Historical-Data-Monthly_2026-10.xlsx"),
    "damodaran": ("https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx", "ctryprem_2026-01.xlsx"),
    "naturalearth": ("https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip", "ne_10m_land.zip"),
    "ecb": ("https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A?format=csvdata", "ecb_usd_per_eur_annual.csv"),
    "eurostat": ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_aind"
                 "?unit=INX_A_AVG&coicop=CP00&geo=EA20&geo=EU27_2020&sinceTimePeriod=2010",
                 "hicp_annual_index.json"),
    "imf_balance": (f"https://www.imf.org/external/datamapper/api/v1/GGXCNL_NGDP/{IMF_C}", "imf_GGXCNL_NGDP.json"),
    "imf_debt": (f"https://www.imf.org/external/datamapper/api/v1/GGXWDG_NGDP/{IMF_C}", "imf_GGXWDG_NGDP.json"),
    "imf_gdp": (f"https://www.imf.org/external/datamapper/api/v1/NGDPD/{IMF_C}", "imf_NGDPD.json"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(source, url, path):
    man = os.path.join(ROOT, "MANIFEST.csv")
    new = not os.path.exists(man)
    with open(man, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["source", "file", "url", "accessed_utc", "bytes", "sha256"])
        w.writerow([source, os.path.relpath(path, ROOT).replace("\\", "/"), url,
                    dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    os.path.getsize(path), sha256(path)])


def fetch(source, url, fname, force=False):
    d = os.path.join(ROOT, source)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, fname)
    if os.path.exists(path) and not force:
        print(f"skip  {source}/{fname} (exists)")
        return path
    for attempt in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(3 * 2 ** attempt)          # 3, 6, 12, 24 s backoff
    with open(path, "wb") as f:
        f.write(r.content)
    log(source, url, path)
    print(f"ok    {source}/{fname}  {len(r.content)/1e6:.2f} MB")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="subset of sources")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    bad = 0
    for src, (url, fn) in FILES.items():
        if a.only and src not in a.only:
            continue
        try:
            fetch(src, url, fn, a.force)
        except Exception as e:  # keep going; report at the end
            bad += 1
            print(f"FAIL  {src}: {e}")
    sys.exit(1 if bad else 0)
