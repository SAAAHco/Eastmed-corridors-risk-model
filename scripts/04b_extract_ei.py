"""Extract natural-gas tables (bcm) from the EI Statistical Review 2026 PDF.

Rows are rebuilt from word coordinates: each number is assigned to the year
column whose header is horizontally nearest. Output: data/processed/ei_gas_bcm.csv
"""
import os
import re

import pandas as pd
import pdfplumber

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PDF = os.path.join(H, "data", "raw", "manual", "Statistical Review of World Energy.pdf")
TABLES = {"production": "Production in billion cubic metres", "consumption": "Consumption in billion cubic metres"}
KEEP = ["Egypt", "Israel", "Türkiye", "Greece", "Italy", "Bulgaria", "Romania", "Croatia", "Algeria", "Libya",
        "Total Europe", "European Union", "Total Middle East", "Total Africa", "Other Middle East"]
NUM = re.compile(r"^-?\d+(\.\d+)?$")


def page_rows(page):
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    rows = {}
    for w in words:
        rows.setdefault(round(w["top"] / 3), []).append(w)        # 3-pt row buckets
    return [sorted(v, key=lambda w: w["x0"]) for _, v in sorted(rows.items())]


out = []
with pdfplumber.open(PDF) as pdf:
    for pno, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        for var, title in TABLES.items():
            if title not in text:
                continue
            rows = page_rows(page)
            hdr = next((r for r in rows if sum(1 for w in r if re.fullmatch(r"20(1[5-9]|2[0-5])", w["text"])) >= 10), None)
            if hdr is None:          # e.g. the contents page repeats the table titles
                continue
            years = {}
            for w in hdr:      # first occurrence only: later "2025" headers label growth/share columns
                if re.fullmatch(r"20(1[5-9]|2[0-5])", w["text"]) and int(w["text"]) not in years:
                    years[int(w["text"])] = (w["x0"] + w["x1"]) / 2
            for r in rows:
                label = " ".join(w["text"] for w in r if not NUM.match(w["text"].replace(",", "")) and "%" not in w["text"])
                if label not in KEEP:
                    continue
                for w in r:
                    t = w["text"].replace(",", "")
                    if not NUM.match(t):
                        continue
                    xc = (w["x0"] + w["x1"]) / 2
                    yr, x = min(years.items(), key=lambda kv: abs(kv[1] - xc))
                    if abs(x - xc) < 12:
                        out.append({"variable": var, "country": label, "year": yr, "bcm": float(t), "pdf_page": pno})
df = pd.DataFrame(out).drop_duplicates(["variable", "country", "year"])
df.to_csv(os.path.join(H, "data", "processed", "ei_gas_bcm.csv"), index=False)
pv = df.pivot_table(index=["variable", "country"], columns="year", values="bcm")
pd.set_option("display.width", 250)
print(pv.loc[:, 2019:].to_string())
