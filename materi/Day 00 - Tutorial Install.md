# Day 0 - Python AI & Backend Development Setup

Panduan ini berisi langkah-langkah inisialisasi project Python menggunakan WSL (Ubuntu), Pyenv, dan UV.

## 1. Persiapan Environment (WSL Ubuntu)

Sebelum menginstall Python, kita perlu menginstall dependensi sistem agar proses kompilasi berjalan lancar. Paket-paket ini penting untuk mendukung fitur seperti SSL, BZ2, dan SQLite pada Python.

```bash
sudo apt update && sudo apt install -y build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev \
xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

## 2. Instalasi Python dengan Pyenv

Gunakan `pyenv` untuk menginstall Python versi terbaru (misalnya 3.12.13) dan mengaturnya sebagai versi global.

```bash
# Install versi spesifik
pyenv install 3.12.13

# Atur sebagai versi utama di sistem
pyenv global 3.12.13
```

## 3. Inisialisasi Project dengan UV

`uv` adalah package manager modern yang sangat cepat. Kita akan menggunakan `uv` untuk mengelola project dan library.

```bash
# Inisialisasi folder project
uv init my-ai-project
cd my-ai-project
```

## 4. Instalasi Library (Dependencies)

Tambahkan library utama yang dibutuhkan. **Penting:** Kita membatasi versi `redis<6.5` agar kompatibel dengan Celery.

```bash
uv add fastapi uvicorn crewai celery "redis<6.5"
```

**Penjelasan Library:**
- **FastAPI**: Framework untuk membuat API yang cepat dan modern.
- **Uvicorn**: Server untuk menjalankan aplikasi FastAPI.
- **CrewAI**: Framework utama untuk mengelola AI Agents.
- **Celery**: Digunakan untuk memproses tugas-tugas berat di latar belakang (Background Tasks).
- **Redis**: Bertindak sebagai Broker atau perantara pesan untuk Celery.

## 5. Konfigurasi Redis Server

Penting: `uv add redis` hanya menginstall library Python. Kamu tetap wajib menginstall **Redis Server** di Ubuntu kamu agar sistem bisa berjalan.
```bash
uv add "redis<6.5"
```

### Instalasi di Ubuntu/WSL:
```bash
sudo apt update && sudo apt install redis-server -y
```

### Menjalankan Redis Service:
WSL seringkali membutuhkan perintah manual untuk menjalankan service:
```bash
# Menjalankan Redis
sudo service redis-server start
```

### Verifikasi:
Ketik perintah di bawah ini untuk memastikan Redis sudah aktif:
```bash
redis-cli ping
```
Jika muncul jawaban **`PONG`**, artinya setup kamu sudah berhasil 100%!

---
*Lanjutkan ke materi **Day 0 - Practice 1.md** untuk mulai membangun project AI pertama kamu.*
