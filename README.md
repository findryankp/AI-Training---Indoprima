# AI Agent Project (FastAPI + Celery + CrewAI)

Project ini menggunakan arsitektur modern yang memisahkan **API (Kasir)** untuk menerima request dan **Celery Worker (Dapur)** untuk menjalankan proses AI Agent secara asinkron.

## 🚀 Cara Menjalankan

### 1. Jalankan Redis Server
Pastikan Redis sudah berjalan di Ubuntu/WSL:
```bash
sudo service redis-server start
```

### 2. Jalankan Celery Worker
Proses ini bertanggung jawab menjalankan AI Agents di latar belakang.
```bash
uv run celery -A tasks.celery_tasks worker --loglevel=info
```

### 3. Jalankan FastAPI
Proses ini menyediakan endpoint untuk mengirim tugas dan mengecek status.
```bash
uv run uvicorn api.main:app --reload
```

## 🧪 Testing API

### Submit Task (POST)
```bash
curl -X POST http://localhost:8000/research \
     -H "Content-Type: application/json" \
     -d '{"topic": "Ikan Sapu-sapu"}'
```

### Check Status (GET)
```bash
curl http://localhost:8000/status/<task_id>
```

## 📂 Struktur Project
- `api/`: Endpoint FastAPI.
- `tasks/`: Konfigurasi Celery & Worker Tasks.
- `src/crews/`: Logika CrewAI (Agents & Tasks YAML).
- `.env`: Konfigurasi API Keys.
