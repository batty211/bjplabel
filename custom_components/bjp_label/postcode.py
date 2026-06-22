"""Offline Thai postcode lookup for customer label addresses."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

_DATA_PATH = Path(__file__).parent / "frontend" / "postcodes.json"
_SPACE = re.compile(r"\s+")


@lru_cache(maxsize=1)
def _postcode_rows() -> tuple[tuple[str, str, str, str], ...]:
    """Load the bundled compact postcode data once per process."""
    with _DATA_PATH.open(encoding="utf-8") as data_file:
        rows = json.load(data_file)
    return tuple((row["s"], row["d"], row["p"], str(row["z"])) for row in rows)


def lookup_postcodes(address: str) -> tuple[str, ...]:
    """Return possible postcodes ordered by confidence, empty when unmatched."""
    text = _normalize(address)
    if not text:
        return ()

    province = _extract(text, (r"(?:จังหวัด|จ\.)\s*([^\s,]+)",))
    district = _extract(text, (r"(?:อำเภอ|อ\.|เขต)\s*([^\s,]+)",))
    subdistrict = _extract(text, (r"(?:ตำบล|ต\.|แขวง)\s*([^\s,]+)",))

    matches: list[tuple[str, str, str, str]] = []
    for row in _postcode_rows():
        subdistrict_name, district_name, province_name, _postcode = row
        if province and not _location_matches(province, province_name, "province"):
            continue
        if district and not _location_matches(district, district_name, "district"):
            continue
        if subdistrict and not _location_matches(
            subdistrict, subdistrict_name, "subdistrict"
        ):
            continue
        matches.append(row)

    # Organization names can contain a misleading word after "ตำบล", such as
    # "โรงพยาบาล...ตำบลบ้านดงกลาง". Fall back to district + province only when
    # the strict combination found nothing; uniqueness is still checked by caller.
    if not matches and subdistrict and (district or province):
        matches = [
            row
            for row in _postcode_rows()
            if (not province or _location_matches(province, row[2], "province"))
            and (not district or _location_matches(district, row[1], "district"))
        ]

    # Explicit markers are the safest signal. If none were present, allow full
    # location names found in the text but require at least two matching levels.
    if not any((province, district, subdistrict)):
        matches = [
            row
            for row in _postcode_rows()
            if sum(
                _name_in_text(name, text, kind)
                for name, kind in zip(row[:3], ("subdistrict", "district", "province"))
            )
            >= 2
        ]

    return tuple(dict.fromkeys(row[3] for row in matches))


def _normalize(value: str) -> str:
    return _SPACE.sub(" ", str(value or "").replace("กรุงเทพฯ", "กรุงเทพมหานคร")).strip()


def _extract(text: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip(" .")
    return ""


def _plain_name(value: str, kind: str) -> str:
    prefixes = {
        "province": ("จังหวัด",),
        "district": ("อำเภอ", "เขต"),
        "subdistrict": ("ตำบล", "แขวง"),
    }[kind]
    result = value
    for prefix in prefixes:
        if result.startswith(prefix):
            result = result[len(prefix) :]
    return result


def _location_matches(query: str, actual: str, kind: str) -> bool:
    query = _plain_name(query, kind)
    actual = _plain_name(actual, kind)
    if query == actual:
        return True
    # Addresses commonly abbreviate "อำเภอเมืองนครปฐม" to "อ.เมือง".
    return kind == "district" and query == "เมือง" and actual.startswith("เมือง")


def _name_in_text(name: str, text: str, kind: str) -> bool:
    plain = _plain_name(name, kind)
    return len(plain) >= 3 and plain in text
