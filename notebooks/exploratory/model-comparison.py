"""
Compare gpt-4o-mini vs gpt-5-mini on a curated set of geo-validation edge cases.
Reads from adm1_validation_sample.csv, fetches article text, runs both models,
and saves a side-by-side CSV to data/test/model_comparison.csv.
"""

import json
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.geo_validator.fetch import fetch_all_articles
from tools.geo_validator.prompts import build_messages

SELECTED_IDS = [
    415962864,   # Dubai            — yes  (URL slug, broken link)
    988030605,   # Sudbury          — yes  (URL slug, broken link)
    765182678,   # Colombo          — yes  (title confirms)
    889281438,   # Afghanistan      — no   (capital city bias, title)
    951293442,   # Botswana         — no   (institution confusion)
    1112162181,  # Copenhagen       — no   (slug names Geneva)
    698564814,   # Reunion          — no   (French article about Marseille)
    973494563,   # Myanmar          — uncertain (nationwide strike)
    436950060,   # Cambodia         — uncertain (broken link, vague slug)
    772001373,   # Albania/Tirana   — language edge (human=uncertain, LLM reads Albanian)
    550187700,   # Austria/Vienna   — language edge (French article → actually Gournay, France)
    697528857,   # Sarajevo         — language edge (Bosnian article)
    571988290,   # Bolivia/Yunguyo  — language edge (Spanish, Peru/Bolivia border)
    650951100,   # Brazil/Guarulhos — language edge (Spanish general strike)
    901855462,   # Northumberland   — geographic knowledge gap (KPRDSB school board)
    582677386,   # Seoul            — yes  (Hyundai strike, English)
    852444177,   # Delhi            — yes  (doctors boycott, English)
    852874651,   # India/Ernakulam  — uncertain (nationwide doctors strike)
    957661582,   # Nigeria/Abuja    — has BBC Pidgin title
    987732212,   # São Paulo        — article fetched but content unrelated
]

MODELS = ["gpt-4o-mini", "gpt-5-mini"]


def call_model(client: OpenAI, model: str, row: dict) -> dict:
    is_gpt5    = model.startswith("gpt-5")
    token_kwarg = "max_completion_tokens" if is_gpt5 else "max_tokens"
    max_tok    = 4000 if is_gpt5 else 120
    extra      = {} if is_gpt5 else {"temperature": 0}

    try:
        resp = client.chat.completions.create(
            model=model,
            **{token_kwarg: max_tok},
            **extra,
            response_format={"type": "json_object"},
            messages=build_messages(row),
        )
        parsed = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"    ERROR ({model}): {e}")
        parsed = {}

    return {
        "match":      parsed.get("match", "uncertain"),
        "extracted":  parsed.get("extracted_location", "unknown"),
        "corrected":  parsed.get("corrected_location"),
        "reasoning":  parsed.get("reasoning", ""),
    }


def main():
    client = OpenAI()

    sample = pd.read_csv(ROOT / "data/test/adm1_validation_sample.csv")
    sample["GLOBALEVENTID"] = sample["GLOBALEVENTID"].astype("int64")
    selected = sample[sample["GLOBALEVENTID"].isin(SELECTED_IDS)].copy()
    selected = selected.rename(columns={"source_url": "SOURCEURL"})

    print(f"Fetching article text for {len(selected)} events...")
    selected = fetch_all_articles(selected, try_wayback=True)
    fetched = selected["article_text"].notna().sum()
    print(f"Text retrieved for {fetched}/{len(selected)} events.\n")

    rows = []
    for i, (_, row) in enumerate(selected.iterrows(), 1):
        print(f"[{i:02d}/{len(selected)}] {row['ActionGeo_FullName']}")
        result = {"GLOBALEVENTID": row["GLOBALEVENTID"],
                  "ActionGeo_FullName": row["ActionGeo_FullName"],
                  "ActionGeo_CountryCode": row.get("ActionGeo_CountryCode"),
                  "source_url": row.get("SOURCEURL"),
                  "article_source": row.get("article_source", "none"),
                  "human_correct": str(row.get("adm1_correct", "")).strip(),
                  "human_notes": str(row.get("notes", "")).strip()}

        for model in MODELS:
            print(f"  → {model} ...", end=" ", flush=True)
            out = call_model(client, model, row.to_dict())
            tag = model.replace("-", "_").replace(".", "_")
            result[f"{tag}_match"]     = out["match"]
            result[f"{tag}_extracted"] = out["extracted"]
            result[f"{tag}_corrected"] = out["corrected"]
            result[f"{tag}_reasoning"] = out["reasoning"]
            print(out["match"])

        rows.append(result)

    out_path = ROOT / "data/test/model_comparison.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    # Summary
    df = pd.DataFrame(rows)
    for model in MODELS:
        tag = model.replace("-", "_").replace(".", "_")
        print(f"\n{model}:")
        print(df[f"{tag}_match"].value_counts().to_string())

    # Agreement between models
    tag4o  = "gpt_4o_mini"
    tag5   = "gpt_5_mini"
    agree  = (df[f"{tag4o}_match"] == df[f"{tag5}_match"]).sum()
    print(f"\nModel agreement: {agree}/{len(df)} ({agree/len(df)*100:.0f}%)")


if __name__ == "__main__":
    main()
