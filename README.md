JARVIS x Claude

Asisten pribadi berbasis Python yang terhubung ke Claude lewat Anthropic API.

Isi proyek
File	Fungsi
jarvis.py	Program utama (chat, suara, tool use, memori)
tasks.py	Skill pemantauan tugas harian (tasks.json)
mood.py	Skill pemantauan suasana hati (mood_log.json)
requirements.txt	Daftar library
.env.example	Contoh konfigurasi API key
Instalasi
Pastikan Python 3.9+ terpasang.
(Disarankan) buat virtual environment:
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
Pasang library:
   pip install -r requirements.txt

Jika hanya butuh mode teks, cukup pip install anthropic python-dotenv. 4. Salin .env.example menjadi .env, lalu isi ANTHROPIC_API_KEY (dapatkan di https://console.anthropic.com).

Menjalankan
python jarvis.py            # mode teks
python jarvis.py --voice    # mode suara
python jarvis.py --fresh    # tanpa memori lama

Ketik exit atau ucapkan "keluar" untuk berhenti.

Kemampuan bawaan
Mengobrol dengan memori percakapan (memory.json)
Cek tanggal & jam
Membuka website di browser
Menyimpan catatan ke notes.txt
Skill pemantauan tugas harian

Contoh perintah:

"Tambah tugas kirim laporan besok, prioritas tinggi"
"Apa saja tugasku hari ini?"
"Tugas nomor 2 sudah selesai"
"Bagaimana progres tugasku hari ini?"

Saat JARVIS dinyalakan, ringkasan tugas tertunda ditampilkan otomatis.

Skill pemantauan kondisi psikologis

JARVIS membaca nada dan isi pesanmu, lalu mencatat estimasi suasana hati (skor 1-10, emosi, stres) dan merespons dengan empati. Contoh: "Aku capek banget hari ini" atau "Tunjukkan tren mood-ku minggu ini".

Penting: ini bukan alat diagnosis dan tidak menggantikan psikolog/psikiater. Bila kamu merasa tertekan berkepanjangan atau memiliki pikiran menyakiti diri, hubungi orang terdekat atau tenaga profesional. Di Indonesia, layanan kesehatan jiwa Kemenkes dapat dihubungi lewat 119 ext. 8 (pastikan nomor terbaru di situs resmi Kemenkes). Data mood disimpan lokal di komputermu.

Menambah kemampuan baru
Tambahkan definisi tool di list TOOLS.
Tambahkan logikanya di fungsi run_tool().
Catatan
Pemasangan PyAudio di Windows kadang gagal; coba pip install pipwin && pipwin install pyaudio.
Mode suara memakai Google Speech Recognition (butuh internet).
Jangan bagikan file .env atau API key kamu.
