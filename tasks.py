"""Skill: pemantauan tugas harian. Data disimpan di tasks.json."""
import datetime
import json
from pathlib import Path

FILE = Path(__file__).parent / "tasks.json"
PRIORITIES = {"high": 0, "normal": 1, "low": 2}


def _load() -> list:
    if FILE.exists():
        try:
            return json.loads(FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def _save(tasks: list) -> None:
    FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def _today() -> str:
    return datetime.date.today().isoformat()


def add_task(title: str, due: str = None, priority: str = "normal") -> str:
    tasks = _load()
    new_id = max([t["id"] for t in tasks], default=0) + 1
    if priority not in PRIORITIES:
        priority = "normal"
    tasks.append({
        "id": new_id, "title": title, "due": due, "priority": priority,
        "done": False, "created": _today(), "completed_on": None,
    })
    _save(tasks)
    return f"Tugas #{new_id} ditambahkan: {title}" + (f" (tenggat {due})" if due else "")


def _fmt(t: dict) -> str:
    mark = "✅" if t["done"] else "⬜"
    due = f" | tenggat {t['due']}" if t.get("due") else ""
    late = " ⚠️TERLAMBAT" if (not t["done"] and t.get("due") and t["due"] < _today()) else ""
    return f"{mark} #{t['id']} [{t['priority']}] {t['title']}{due}{late}"


def list_tasks(filter: str = "pending") -> str:
    tasks = _load()
    today = _today()
    if filter == "pending":
        tasks = [t for t in tasks if not t["done"]]
    elif filter == "done":
        tasks = [t for t in tasks if t["done"]]
    elif filter == "today":
        tasks = [t for t in tasks if not t["done"] and t.get("due") and t["due"] <= today]
    if not tasks:
        return "Tidak ada tugas pada kategori ini."
    tasks.sort(key=lambda t: (t["done"], t.get("due") or "9999", PRIORITIES.get(t["priority"], 1)))
    return "\n".join(_fmt(t) for t in tasks)


def complete_task(id: int) -> str:
    tasks = _load()
    for t in tasks:
        if t["id"] == id:
            t["done"], t["completed_on"] = True, _today()
            _save(tasks)
            return f"Tugas #{id} selesai: {t['title']}. Kerja bagus!"
    return f"Tugas #{id} tidak ditemukan."


def delete_task(id: int) -> str:
    tasks = _load()
    remaining = [t for t in tasks if t["id"] != id]
    if len(remaining) == len(tasks):
        return f"Tugas #{id} tidak ditemukan."
    _save(remaining)
    return f"Tugas #{id} dihapus."


def daily_report() -> str:
    tasks = _load()
    today = _today()
    pending = [t for t in tasks if not t["done"]]
    overdue = [t for t in pending if t.get("due") and t["due"] < today]
    due_today = [t for t in pending if t.get("due") == today]
    done_today = [t for t in tasks if t.get("completed_on") == today]
    total_today = len(done_today) + len(due_today)
    rate = f"{len(done_today) / total_today * 100:.0f}%" if total_today else "-"
    lines = [
        f"Laporan tugas {today}:",
        f"- Selesai hari ini: {len(done_today)}",
        f"- Jatuh tempo hari ini: {len(due_today)}",
        f"- Terlambat: {len(overdue)}",
        f"- Total belum selesai: {len(pending)}",
        f"- Tingkat penyelesaian hari ini: {rate}",
    ]
    if overdue:
        lines.append("Tugas terlambat: " + "; ".join(f"#{t['id']} {t['title']}" for t in overdue))
    return "\n".join(lines)


def briefing() -> str:
    """Ringkasan singkat yang ditampilkan saat JARVIS dinyalakan."""
    tasks = [t for t in _load() if not t["done"]]
    if not tasks:
        return "Tidak ada tugas yang tertunda."
    today = _today()
    overdue = sum(1 for t in tasks if t.get("due") and t["due"] < today)
    due_today = sum(1 for t in tasks if t.get("due") == today)
    return f"Tugas tertunda: {len(tasks)} (hari ini: {due_today}, terlambat: {overdue})."


TOOLS = [
    {
        "name": "add_task",
        "description": "Menambah tugas baru. Tenggat harus format YYYY-MM-DD; ubah kata seperti 'besok' menjadi tanggal berdasarkan tanggal hari ini.",
        "input_schema": {"type": "object", "properties": {
            "title": {"type": "string"},
            "due": {"type": "string", "description": "YYYY-MM-DD (opsional)"},
            "priority": {"type": "string", "enum": ["high", "normal", "low"]},
        }, "required": ["title"]},
    },
    {
        "name": "list_tasks",
        "description": "Menampilkan daftar tugas.",
        "input_schema": {"type": "object", "properties": {
            "filter": {"type": "string", "enum": ["pending", "done", "all", "today"]},
        }},
    },
    {
        "name": "complete_task",
        "description": "Menandai tugas selesai berdasarkan ID.",
        "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "delete_task",
        "description": "Menghapus tugas berdasarkan ID.",
        "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "daily_report",
        "description": "Laporan progres tugas hari ini (selesai, terlambat, tingkat penyelesaian).",
        "input_schema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "add_task": lambda a: add_task(a["title"], a.get("due"), a.get("priority", "normal")),
    "list_tasks": lambda a: list_tasks(a.get("filter", "pending")),
    "complete_task": lambda a: complete_task(int(a["id"])),
    "delete_task": lambda a: delete_task(int(a["id"])),
    "daily_report": lambda a: daily_report(),
}
