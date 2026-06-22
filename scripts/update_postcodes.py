#!/usr/bin/env python3
"""Refresh BJP Label's compact offline Thai postcode dataset."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

SOURCE_URL = (
    "https://raw.githubusercontent.com/kongvut/thai-province-data/"
    "refs/heads/master/api/latest/sub_district_with_district_and_province.json"
)
OUTPUT = (
    Path(__file__).parents[1]
    / "custom_components"
    / "bjp_label"
    / "frontend"
    / "postcodes.json"
)


def main() -> None:
    with urlopen(SOURCE_URL, timeout=60) as response:  # noqa: S310
        source = json.load(response)
    compact = [
        {
            "s": item["name_th"],
            "d": item["district"]["name_th"],
            "p": item["district"]["province"]["name_th"],
            "z": item["zip_code"],
        }
        for item in source
        if item.get("zip_code") and item.get("district", {}).get("province")
    ]
    OUTPUT.write_text(
        json.dumps(compact, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {len(compact):,} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
