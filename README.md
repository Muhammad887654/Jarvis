# JARVIS x Claude

Asisten pribadi berbasis Python yang terhubung ke Claude lewat Anthropic API.

## Isi proyek
| File | Fungsi |
|------|--------|
| `jarvis.py` | Program utama (chat, suara, tool use, memori) |
| `requirements.txt` | Daftar library |
| `.env.example` | Contoh konfigurasi API key |

## Instalasi
1. Pastikan Python 3.9+ terpasang.
2. (Disarankan) buat virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```
3. Pasang library:
   ```
   pip install -r requirements.txt
   ```
   Jika hanya butuh mode teks, cukup `pip install anthropic python-dotenv`.
4. Salin `.env.example` menjadi `.env`, lalu isi `ANTHROPIC_API_KEY`
   (dapatkan di https://console.anthropic.com).

## Menjalankan
```
python jarvis.py            # mode teks
python jarvis.py --voice    # mode suara
python jarvis.py --fresh    # tanpa memori lama
```
Ketik `exit` atau ucapkan "keluar" untuk berhenti.

## Kemampuan bawaan
- Mengobrol dengan memori percakapan (`memory.json`)
- Cek tanggal & jam
- Membuka website di browser
- Menyimpan catatan ke `notes.txt`

## Menambah kemampuan baru
1. Tambahkan definisi tool di list `TOOLS`.
2. Tambahkan logikanya di fungsi `run_tool()`.

## Catatan
- Pemasangan PyAudio di Windows kadang gagal; coba `pip install pipwin && pipwin install pyaudio`.
- Mode suara memakai Google Speech Recognition (butuh internet).
- Jangan bagikan file `.env` atau API key kamu.
