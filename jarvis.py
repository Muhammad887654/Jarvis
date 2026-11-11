"""
JARVIS - Asisten pribadi yang terhubung dengan Claude (Anthropic API).
 
Cara pakai:
    python jarvis.py            # mode teks
    python jarvis.py --voice    # mode suara (mic + text-to-speech)
"""
import argparse
import datetime
import json
import os
import webbrowser
from pathlib import Path
 
import anthropic
from dotenv import load_dotenv
 
import mood
import tasks
 
load_dotenv()
 
MODEL = os.getenv("JARVIS_MODEL", "claude-sonnet-5-5")
LANG = os.getenv("JARVIS_LANG", "id-ID")
MEMORY_FILE = Path(__file__).parent / "memory.json"
MAX_HISTORY = 40  # batasi jumlah pesan yang disimpan
 
SYSTEM_PROMPT = """Kamu adalah JARVIS, asisten pribadi yang cerdas, sopan, dan efisien.
- Jawab dalam bahasa yang dipakai pengguna (default: Bahasa Indonesia).
- Jawaban singkat dan jelas, terutama dalam mode suara.
- Gunakan tool yang tersedia bila diperlukan (waktu, membuka website, catatan, tugas, suasana hati).
- Panggil pengguna dengan sopan. Jangan mengarang informasi yang tidak kamu ketahui.
 
PEMANTAUAN TUGAS:
- Bila pengguna menyebut tugas/rencana/deadline, tawarkan atau langsung catat dengan add_task.
- Ubah tenggat relatif ("besok", "Jumat") menjadi tanggal YYYY-MM-DD berdasarkan tanggal hari ini.
- Beri semangat saat tugas selesai; saat ada tugas terlambat, bantu memprioritaskan tanpa menghakimi.
 
PEMANTAUAN KONDISI PSIKOLOGIS:
- Perhatikan nada dan isi pesan pengguna (lelah, cemas, sedih, marah, senang). Bila terlihat jelas,
  catat dengan log_mood (estimasi skor 1-10) dan respons dengan empati, bukan nasihat panjang.
- Kamu BUKAN psikolog dan tidak boleh mendiagnosis. Gunakan bahasa seperti "sepertinya kamu sedang...".
- Sesekali (jangan berlebihan) tanyakan kabar pengguna. Bila diminta, tampilkan tren dengan mood_report.
- Jika ada tanda krisis (keinginan menyakiti diri/mengakhiri hidup, putus asa berat), tanggapi dengan
  hangat dan serius, tanyakan keadaannya, dorong menghubungi orang terdekat atau layanan darurat/kesehatan
  jiwa setempat (di Indonesia misalnya 119 ext. 8), dan jangan menawarkan tugas atau produktivitas saat itu.
- Jangan pernah menyalahkan pengguna atas perasaannya."""
 
 
def build_system_prompt() -> str:
    today = datetime.date.today()
    return SYSTEM_PROMPT + f"\n\nTanggal hari ini: {today.isoformat()} ({today.strftime('%A')})."
 
# ---------------------------------------------------------------------------
# TOOLS (kemampuan lokal yang bisa dipanggil Claude)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "get_datetime",
        "description": "Mendapatkan tanggal dan jam saat ini di komputer pengguna.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "open_website",
        "description": "Membuka sebuah website di browser pengguna.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL lengkap, contoh https://youtube.com"}},
            "required": ["url"],
        },
    },
    {
        "name": "save_note",
        "description": "Menyimpan catatan singkat ke file notes.txt.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Isi catatan"}},
            "required": ["text"],
        },
    },
]
 
 
TOOLS += tasks.TOOLS + mood.TOOLS
HANDLERS = {**tasks.HANDLERS, **mood.HANDLERS}
 
 
def run_tool(name: str, args: dict) -> str:
    if name == "get_datetime":
        return datetime.datetime.now().strftime("%A, %d %B %Y, pukul %H:%M:%S")
    if name == "open_website":
        url = args.get("url", "")
        if not url.startswith(("http://", "https://")):
            return "URL tidak valid."
        webbrowser.open(url)
        return f"Berhasil membuka {url}"
    if name == "save_note":
        with open(Path(__file__).parent / "notes.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {args.get('text', '')}\n")
        return "Catatan tersimpan."
    if name in HANDLERS:
        try:
            return HANDLERS[name](args)
        except Exception as e:
            return f"Gagal menjalankan {name}: {e}"
    return f"Tool '{name}' tidak dikenal."
 
 
# ---------------------------------------------------------------------------
# MEMORI PERCAKAPAN
# ---------------------------------------------------------------------------
def load_memory() -> list:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []
 
 
def save_memory(messages: list) -> None:
    # Hanya simpan pesan teks sederhana agar file tetap valid saat dimuat ulang
    simple = [m for m in messages if isinstance(m["content"], str)]
    MEMORY_FILE.write_text(
        json.dumps(simple[-MAX_HISTORY:], ensure_ascii=False, indent=2), encoding="utf-8"
    )
 
 
# ---------------------------------------------------------------------------
# SUARA (opsional)
# ---------------------------------------------------------------------------
class Voice:
    def __init__(self):
        import pyttsx3
        import speech_recognition as sr
 
        self.sr = sr
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)
 
    def listen(self) -> str:
        with self.sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Mendengarkan...")
            audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
        try:
            return self.recognizer.recognize_google(audio, language=LANG)
        except (self.sr.UnknownValueError, self.sr.RequestError):
            return ""
 
    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()
 
 
# ---------------------------------------------------------------------------
# OTAK JARVIS
# ---------------------------------------------------------------------------
def ask_claude(client: anthropic.Anthropic, messages: list) -> str:
    """Kirim percakapan ke Claude, tangani tool use hingga jawaban final."""
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=build_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )
 
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text").strip()
 
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"🔧 Tool: {block.name} {block.input}")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": run_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": results})
 
 
def main():
    parser = argparse.ArgumentParser(description="JARVIS x Claude")
    parser.add_argument("--voice", action="store_true", help="Aktifkan mode suara")
    parser.add_argument("--fresh", action="store_true", help="Mulai tanpa memori lama")
    args = parser.parse_args()
 
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY belum diatur. Salin .env.example menjadi .env dan isi key-nya.")
 
    client = anthropic.Anthropic()
    messages = [] if args.fresh else load_memory()
    voice = Voice() if args.voice else None
 
    greeting = "Halo, saya JARVIS. Ada yang bisa saya bantu?"
    print(f"🤖 {greeting}")
    print(f"📋 {tasks.briefing()}")
    if voice:
        voice.speak(greeting + " " + tasks.briefing())
 
    while True:
        try:
            user_input = voice.listen() if voice else input("\nKamu: ").strip()
        except KeyboardInterrupt:
            break
        except Exception as e:  # timeout mic, dll.
            print(f"(input gagal: {e})")
            continue
 
        if not user_input:
            continue
        print(f"Kamu: {user_input}") if voice else None
 
        if user_input.lower() in {"exit", "keluar", "quit", "sampai jumpa"}:
            break
 
        messages.append({"role": "user", "content": user_input})
        try:
            answer = ask_claude(client, messages)
        except anthropic.APIError as e:
            print(f"⚠️ Error API: {e}")
            messages.pop()
            continue
 
        messages.append({"role": "assistant", "content": answer})
        print(f"🤖 JARVIS: {answer}")
        if voice:
            voice.speak(answer)
        save_memory(messages)
 
    bye = "Sampai jumpa!"
    print(f"🤖 {bye}")
    if voice:
        voice.speak(bye)
 
 
if __name__ == "__main__":
    main()
