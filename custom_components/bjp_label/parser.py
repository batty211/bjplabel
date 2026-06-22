"""Lightweight extraction for Thai customer label text."""

from __future__ import annotations

from dataclasses import dataclass
import re

import phonenumbers
from phonenumbers import PhoneNumberFormat, PhoneNumberMatcher

from .postcode import lookup_postcodes

_THAI_WORD = re.compile(r"[ก-๙]+")
_POSTAL_CODE = re.compile(r"(?<!\d)(\d{5})(?!\d)")
_SEND_PREFIX = re.compile(r"^\s*#?\s*ส่ง\s*")
_HONORIFIC = re.compile(r"^(นางสาว|นาย|นาง|คุณ)\s*")
_ADDRESS_MARKERS = (
    "โรงพยาบาล",
    "รพ.",
    "บริษัท",
    "หจก.",
    "ร้าน",
    "เลขที่",
    "หมู่บ้าน",
    "ถนน",
    "ซอย",
    "แขวง",
    "เขต",
    "ตำบล",
    "อำเภอ",
    "จังหวัด",
    "ต.",
    "อ.",
    "จ.",
    "ม.",
)
_NAME_STOP_WORDS = {
    "ส่ง",
    "บ้าน",
    "หมู่",
    "ถนน",
    "ซอย",
    "ตำบล",
    "อำเภอ",
    "จังหวัด",
    "โรงพยาบาล",
    "บริษัท",
    "ร้าน",
}


class ParseError(ValueError):
    """Raised when required customer data cannot be extracted."""


@dataclass(frozen=True)
class ParsedLabel:
    """Structured customer label data."""

    name: str
    phone: str
    address: str
    postal_code: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class _NameCandidate:
    name: str
    line_index: int
    start: int
    end: int
    score: int


def parse_customer_text(text: str) -> ParsedLabel:
    """Extract a customer name, Thai phone, address, and postal code."""
    normalized = _normalize_text(text)
    if not normalized:
        raise ParseError("กรุณาวางข้อมูลลูกค้า")

    phone_matches = [
        match
        for match in PhoneNumberMatcher(normalized, "TH")
        if phonenumbers.is_possible_number(match.number)
        and phonenumbers.region_code_for_number(match.number) == "TH"
    ]
    if not phone_matches:
        raise ParseError("ไม่พบเบอร์โทรศัพท์ กรุณาตรวจสอบข้อความ")

    selected_phone = phone_matches[0]
    phone = _format_thai_phone(selected_phone.number)
    postal_matches = [
        match
        for match in _POSTAL_CODE.finditer(normalized)
        if not _overlaps(match.start(), match.end(), selected_phone.start, selected_phone.end)
    ]
    postal_match = postal_matches[-1] if postal_matches else None

    lines = normalized.splitlines()
    candidates = _find_name_candidates(lines)
    if not candidates:
        raise ParseError("ไม่พบชื่อและนามสกุล กรุณาตรวจสอบข้อความ")

    candidates.sort(key=lambda item: (-item.score, item.line_index, item.start))
    selected_name = candidates[0]
    warnings = []
    if len(phone_matches) > 1:
        warnings.append("พบหลายเบอร์โทร กรุณาตรวจสอบเบอร์ที่เลือก")
    if len(candidates) > 1 and candidates[1].score >= selected_name.score - 1:
        warnings.append("พบชื่อที่เป็นไปได้มากกว่าหนึ่งรายการ กรุณาตรวจสอบ")

    address = _build_address(
        lines,
        selected_name,
        selected_phone.raw_string,
        postal_match.group(0) if postal_match else "",
    )
    postal_code = postal_match.group(1) if postal_match else ""
    if not postal_code:
        possible_postcodes = lookup_postcodes(address)
        if len(possible_postcodes) == 1:
            postal_code = possible_postcodes[0]
            warnings.append(f"เติมรหัสไปรษณีย์ {postal_code} ให้อัตโนมัติ กรุณาตรวจสอบ")
        elif len(possible_postcodes) > 1:
            preview = ", ".join(possible_postcodes[:4])
            suffix = "…" if len(possible_postcodes) > 4 else ""
            warnings.append(
                f"พบรหัสไปรษณีย์ได้หลายค่า: {preview}{suffix} กรุณาเลือกและกรอกเอง"
            )
        else:
            warnings.append("ไม่พบรหัสไปรษณีย์ กรุณากรอกเอง")

    return ParsedLabel(
        name=selected_name.name,
        phone=phone,
        address=address,
        postal_code=postal_code,
        warnings=tuple(warnings),
    )


def _normalize_text(text: str) -> str:
    lines = []
    for raw_line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = " ".join(raw_line.split())
        if line:
            lines.append(line)
    return "\n".join(lines)


def _format_thai_phone(number) -> str:
    national = phonenumbers.format_number(number, PhoneNumberFormat.NATIONAL)
    digits = re.sub(r"\D", "", national)
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 9 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 9:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return national.replace(" ", "-")


def _find_name_candidates(lines: list[str]) -> list[_NameCandidate]:
    candidates = []
    for line_index, original_line in enumerate(lines):
        line = _SEND_PREFIX.sub("", original_line)
        marker_positions = [line.find(marker) for marker in _ADDRESS_MARKERS if marker in line]
        boundary = min(marker_positions) if marker_positions else len(line)
        segment = line[:boundary].strip(" ,:-")

        # A number before the name-like segment usually means this is an address line.
        if re.search(r"\d", segment):
            phone_position = _phone_like_position(segment)
            if phone_position is None:
                continue
            segment = segment[:phone_position].strip()

        title_match = _HONORIFIC.match(segment)
        title = title_match.group(1) if title_match else ""
        name_part = segment[title_match.end() :] if title_match else segment
        words = list(_THAI_WORD.finditer(name_part))
        if len(words) < 2:
            continue

        first_two = words[:2]
        values = [word.group(0) for word in first_two]
        if any(value in _NAME_STOP_WORDS or len(value) < 2 for value in values):
            continue

        start = (title_match.start() if title_match else first_two[0].start())
        end = first_two[-1].end() + (title_match.end() if title_match else 0)
        name = f"{title}{values[0]} {values[1]}"
        score = 5
        if title:
            score += 6
        if not any(marker in original_line for marker in _ADDRESS_MARKERS):
            score += 3
        if _contains_phone(original_line):
            score += 2
        if len(words) == 2:
            score += 2

        original_start = original_line.find(segment)
        candidates.append(
            _NameCandidate(
                name=name,
                line_index=line_index,
                start=max(0, original_start + start),
                end=max(0, original_start + end),
                score=score,
            )
        )
    return candidates


def _contains_phone(text: str) -> bool:
    return any(
        phonenumbers.is_possible_number(match.number)
        for match in PhoneNumberMatcher(text, "TH")
    )


def _phone_like_position(text: str) -> int | None:
    matches = list(PhoneNumberMatcher(text, "TH"))
    return matches[0].start if matches else None


def _build_address(
    lines: list[str], candidate: _NameCandidate, phone_raw: str, postal_code: str
) -> str:
    address_lines = []
    for index, line in enumerate(lines):
        cleaned = line
        if index == candidate.line_index:
            cleaned = cleaned[: candidate.start] + cleaned[candidate.end :]
            cleaned = _SEND_PREFIX.sub("", cleaned)
        cleaned = cleaned.replace(phone_raw, " ")
        cleaned = re.sub(r"(?:โทร(?:ศัพท์)?|เบอร์(?:โทรศัพท์)?)\s*:?\s*$", " ", cleaned)
        if postal_code:
            cleaned = re.sub(
                rf"(?<!\d){re.escape(postal_code)}(?!\d)", " ", cleaned, count=1
            )
        cleaned = " ".join(cleaned.strip(" ,:-#").split())
        if cleaned:
            address_lines.append(cleaned)
    return _wrap_address_lines(address_lines)


def _wrap_address_lines(lines: list[str], width: int = 34, max_lines: int = 3) -> str:
    """Wrap address words into at most three readable label lines."""
    wrapped: list[str] = []
    for source_line in lines:
        current = ""
        for word in source_line.split():
            proposed = f"{current} {word}".strip()
            if current and len(proposed) > width:
                wrapped.append(current)
                current = word
            else:
                current = proposed
        if current:
            wrapped.append(current)

    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)
    return "\n".join(wrapped[: max_lines - 1] + [" ".join(wrapped[max_lines - 1 :])])


def _overlaps(start: int, end: int, other_start: int, other_end: int) -> bool:
    return start < other_end and other_start < end
