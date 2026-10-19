from __future__ import annotations

"""Blizzard talent loadout string helpers.

Format documented in Blizzard_ClassTalentImportExport.lua:
- Custom base64 alphabet (not stdlib base64)
- Header: serialization version (8 bits), spec id (16 bits), tree hash (128 bits)
"""

from app.domain.models import TalentImportResult

# Blizzard export alphabet (not standard base64)
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_CHAR_TO_VAL = {c: i for i, c in enumerate(_ALPHABET)}


class BitReader:
    def __init__(self, data: str) -> None:
        # Blizzard ExportUtil packs each alphabet character as 6 bits, LSB first.
        self._bits: list[int] = []
        for ch in data.strip():
            if ch not in _CHAR_TO_VAL:
                raise ValueError("Invalid character in talent export string")
            val = _CHAR_TO_VAL[ch]
            for _ in range(6):
                self._bits.append(val & 1)
                val >>= 1
        self._pos = 0

    def extract(self, width: int) -> int:
        if self._pos + width > len(self._bits):
            raise ValueError("Talent string truncated")
        value = 0
        for i in range(width):
            value |= self._bits[self._pos] << i
            self._pos += 1
        return value


def import_talent_string(export_string: str, expected_spec_id: int | None = None) -> TalentImportResult:
    text = export_string.strip()
    if not text:
        return TalentImportResult(ok=False, exportString=text, error="Empty talent string")

    try:
        reader = BitReader(text)
        version = reader.extract(8)
        spec_id = reader.extract(16)
        # Tree hash (128 bits) — read to advance stream; may be zero-filled by third parties
        _tree_hash = reader.extract(128)
    except ValueError as exc:
        return TalentImportResult(ok=False, exportString=text, error=str(exc))

    warnings: list[str] = []
    if version not in (1, 2):
        return TalentImportResult(
            ok=False,
            exportString=text,
            serializationVersion=version,
            specId=spec_id,
            error=f"Unsupported talent serialization version {version}",
        )

    if expected_spec_id is not None and spec_id != expected_spec_id:
        return TalentImportResult(
            ok=False,
            exportString=text,
            serializationVersion=version,
            specId=spec_id,
            error=f"Talent string specId {spec_id} does not match expected {expected_spec_id}",
        )

    if version == 1:
        warnings.append("Serialization version 1 detected; prefer a fresh in-game export (v2).")

    warnings.append(
        "Node contents accepted for SimulationCraft talents= passthrough; "
        "full tree-hash validation requires a Blizzard API talent snapshot."
    )

    return TalentImportResult(
        ok=True,
        exportString=text,
        serializationVersion=version,
        specId=spec_id,
        warnings=warnings,
    )


def export_talent_passthrough(export_string: str) -> str:
    """MVP export returns the stored Blizzard string unchanged."""
    return export_string.strip()
