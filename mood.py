"""
Skill: pemantauan suasana hati / kondisi psikologis (BUKAN alat diagnosis).

Claude membaca nada dan isi pesan pengguna, lalu mencatat estimasi suasana hati
lewat tool `log_mood`. Data disimpan lokal di mood_log.json dan hanya dipakai
untuk melihat tren. Hasilnya bukan diagnosis medis.
"""
import datetime
import json
from collections import Counter
from pathlib import Path

FILE = Path(__file__).parent / "mood_log.json"


def _load() -> list:
    if FILE.exists():
        try:
            return json.loads(FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def log_mood(score: int, emotions: list = None, stress: int = None, note: str = "") -> str:
    score = max(1, min(10, int(score)))
    entries = _load()
    entries.append({
        "time": datetime.datetime.now().isoformat(timespec="minutes"),
        "score": score,
        "emotions": emotions or [],
        "stress": None if stress is None else max(1, min(10, int(stress))),
        "note": note[:200],
    })
    _save(entries)
    return f"Suasana hati tercatat (skor {score}/10)."


def _save(entries: list) -> None:
    FILE.write_text(json.dumps(entries[-500:], ensure_ascii=False, indent=2), encoding="utf-8")


def mood_report(days: int = 7) -> str:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=int(days))
    entries = [e for e in _load() if datetime.datetime.fromisoformat(e["time"]) >= cutoff]
    if not entries:
        return f"Belum ada catatan suasana hati dalam {days} hari terakhir."

    scores = [e["score"] for e in entries]
    avg = sum(scores) / len(scores)
    emo = Counter(x for e in entries for x in e["emotions"]).most_common(3)
    stress_vals = [e["stress"] for e in entries if e["stress"] is not None]

    trend = "stabil"
    if len(scores) >= 4:
        half = len(scores) // 2
        diff = sum(scores[half:]) / len(scores[half:]) - sum(scores[:half]) / half
        trend = "membaik" if diff >= 1 else "menurun" if diff <= -1 else "stabil"

    lines = [
        f"Ringkasan {days} hari terakhir ({len(entries)} catatan):",
        f"- Rata-rata suasana hati: {avg:.1f}/10 (tren {trend})",
    ]
    if stress_vals:
        lines.append(f"- Rata-rata stres: {sum(stress_vals) / len(stress_vals):.1f}/10")
    if emo:
        lines.append("- Emosi tersering: " + ", ".join(f"{k} ({v}x)" for k, v in emo))
    if len(scores) >= 3 and (avg <= 4 or all(s <= 4 for s in scores[-3:])):
        lines.append(
            "- CATATAN: suasana hati cenderung rendah belakangan ini. Sampaikan dengan empati, "
            "dan sarankan berbicara dengan orang tepercaya atau tenaga profesional bila berlanjut."
        )
    return "\n".join(lines)


TOOLS = [
    {
        "name": "log_mood",
        "description": (
            "Catat estimasi suasana hati pengguna berdasarkan apa yang mereka tulis/ucapkan. "
            "Panggil saat pengguna mengungkapkan perasaan atau saat check-in. Ini estimasi, bukan diagnosis."
        ),
        "input_schema": {"type": "object", "properties": {
            "score": {"type": "integer", "description": "1 (sangat buruk) sampai 10 (sangat baik)"},
            "emotions": {"type": "array", "items": {"type": "string"}, "description": "mis. cemas, lelah, senang"},
            "stress": {"type": "integer", "description": "Tingkat stres 1-10 (opsional)"},
            "note": {"type": "string", "description": "Ringkasan singkat penyebab/konteks"},
        }, "required": ["score"]},
    },
    {
        "name": "mood_report",
        "description": "Ringkasan dan tren suasana hati pengguna dalam beberapa hari terakhir.",
        "input_schema": {"type": "object", "properties": {"days": {"type": "integer"}}},
    },
]

HANDLERS = {
    "log_mood": lambda a: log_mood(a["score"], a.get("emotions"), a.get("stress"), a.get("note", "")),
    "mood_report": lambda a: mood_report(a.get("days", 7)),
}
