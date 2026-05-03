# Day 0 - Practice 1: Membangun Sistem AI Agent

Setelah menginstal semua dependensi, sekarang kita akan mempraktikkan cara membangun sistem AI Agent yang lengkap menggunakan CrewAI, Celery, dan FastAPI.

## 💡 Tips Penting: Konsep Dasar CrewAI (Agents vs Tasks)

Dalam membangun sistem AI dengan CrewAI, terdapat aturan emas yang disebut **The 80/20 Rule**.

### 1. Apa itu Aturan 80/20?
*   **80% Tenaga & Waktu**: Fokuslah pada penulisan **Task** (Instruksi kerja) yang sangat detail.
*   **20% Sisanya**: Baru fokus pada profil **Agent** (Role, Goal, Backstory).

**Intinya:** AI akan bekerja jauh lebih baik jika diberi instruksi kerja yang sangat jelas daripada hanya diberi identitas yang hebat.

### 2. Perbedaan Agent vs Task
*   **Agent (Who)**: Identitas atau "Persona" sang AI. 
    * *Contoh:* Content Writer, Senior Developer, Market Researcher.
*   **Task (What)**: Tugas spesifik yang harus dikerjakan.
    * *Contoh:* "Buat outline blog tentang AI, minimal 5 bagian, sertakan statistik terbaru."

### 3. Elemen Task yang Efektif
Untuk mendapatkan hasil maksimal, setiap Task harus memiliki:
1.  **Description**: Instruksi langkah-demi-langkah yang jelas tentang apa yang harus dilakukan.
2.  **Expected Output**: Definisi hasil akhir yang diinginkan (Misal: "Tabel perbandingan dalam format Markdown").
3.  **Context**: Data atau hasil dari task sebelumnya yang bisa digunakan sebagai referensi.

---
*Selamat belajar! Fokuslah pada kejelasan instruksi (Task) untuk hasil AI yang luar biasa.*

---

## 🏛️ Konsep Arsitektur: Kasir (API) vs Dapur (Celery)

Untuk membangun aplikasi yang handal, kita menggunakan analogi restoran cepat saji:

*   **REST API (Kasir)**: Staf yang menerima pesanan dengan cepat. Dia tidak memasak, hanya mencatat pesanan dan memberimu nomor antrean (struk). Ini membuat antrean tetap berjalan lancar.
*   **Celery (Dapur)**: Staf di belakang layar yang perlahan dan cermat "memasak" pesanan berat (seperti proses LLM/CrewAI). Dia bekerja tanpa mengganggu kasir di depan.

### 1. Instalasi Celery & Library Tambahan
Masuk ke root folder project kamu di terminal, lalu jalankan:
```bash
uv add "fastapi[all]" "celery[redis]" "redis<6.5" crewai crewai-tools
```

> **Tips Warning VIRTUAL_ENV:** Jika muncul pesan `VIRTUAL_ENV ... does not match`, itu karena kamu punya virtualenv lain yang aktif. Kamu bisa mengabaikannya, `uv` akan tetap menginstal ke folder `.venv` di dalam project kamu.

### 2. Struktur Folder Project
Agar project rapi, buatlah struktur folder seperti berikut:

```text
INDOPRIMAFLOW/
├── .venv/            # Virtual environment (otomatis)
├── api/              # Konfigurasi FastAPI
│   ├── __init__.py   # File kosong (penanda package)
│   └── main.py       # Kode utama FastAPI
├── tasks/            # Worker Celery & Logic CrewAI
│   ├── __init__.py
│   ├── celery_app.py
│   └── celery_tasks.py
├── output/           # Folder untuk menyimpan hasil AI
├── src/              # Source code utama & Crews
│   └── crews/
│       └── content_crew/
│           ├── config/
│           │   ├── agents.yaml
│           │   └── tasks.yaml
│           └── content_crew.py
├── .env              # Tempat menyimpan API Key (OpenAI/Serper)
└── pyproject.toml    # File konfigurasi uv
```

#### **Perintah Cepat Pembuatan Struktur:**
Jalankan perintah ini di terminal untuk membuat semua folder dan file dasar sekaligus:
```bash
mkdir -p api tasks output src/crews/content_crew/config
touch api/__init__.py api/main.py \
      tasks/__init__.py tasks/celery_app.py tasks/celery_tasks.py \
      src/crews/content_crew/config/agents.yaml \
      src/crews/content_crew/config/tasks.yaml \
      src/crews/content_crew/content_crew.py \
      .env
```

**Catatan Folder `api/`:**
- `__init__.py`: Wajib dibuat (kosong saja) agar Python mengenali folder ini sebagai modul.
- `main.py`: Berisi konfigurasi endpoint FastAPI kamu.
- `__pycache__`: Akan muncul otomatis saat program dijalankan (bisa diabaikan).

---

## ⚙️ Implementasi Worker & CrewAI Logic

Pada bagian ini, kita akan mengatur bagaimana Celery bekerja dan bagaimana CrewAI menjalankan agen-agennya.

### 1. Konfigurasi Celery (`tasks/celery_app.py`)
Buat file `tasks/celery_app.py` dan masukkan kode berikut untuk mengatur koneksi ke Redis:

```python
import os
from celery import Celery

# Mengambil URL Redis dari environment variable atau default ke localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Inisialisasi Celery App
celery_app = Celery(
    "crewai_flow",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.celery_tasks"]  # Memasukkan file task yang akan dibuat
)

# Konfigurasi tambahan Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,       # Maksimal 30 menit
    task_soft_time_limit=25 * 60,  # Warning di 25 menit
    worker_prefetch_multiplier=1,  # Distribusi tugas yang adil
)
```

### 2. Struktur Agent & Task (CrewAI YAML)
Untuk memudahkan pengelolaan, kita memisahkan konfigurasi Agent dan Task ke dalam file YAML di folder `src/crews/content_crew/config/`.

#### **agents.yaml** (Definisi Persona)
```yaml
planner:
  role: >
    Content Planner
  goal: >
    Plan a detailed and engaging blog post outline on {topic}
  backstory: >
    You're an experienced content strategist who excels at creating structured outlines for blog posts.

writer:
  role: >
    Content Writer
  goal: >
    Write a compelling blog post on {topic} based on the outline
  backstory: >
    You're a skilled writer with a talent for turning outlines into engaging blog posts.

editor:
  role: >
    Content Editor
  goal: >
    Review and polish the blog post on {topic}
  backstory: >
    You're a meticulous editor with an eye for clarity, grammar, and consistency.
```

#### **tasks.yaml** (Definisi Pekerjaan)
```yaml
planning_task:
  description: >
    Create a detailed outline for a blog post about {topic}.
  expected_output: >
    A structured blog post outline with title and section breakdowns.
  agent: planner

writing_task:
  description: >
    Using the outline provided, write a full blog post about {topic}.
  expected_output: >
    A complete blog post in markdown format.
  agent: writer

editing_task:
  description: >
    Review and edit the blog post about {topic}.
  expected_output: >
    The final, polished blog post in markdown format.
  agent: editor
  output_file: output/post.md
```

---

## 🚀 Integrasi Akhir: Menyatukan Semua Komponen

Sekarang kita akan membuat kode program untuk masing-masing file yang sudah kita siapkan strukturnya.

### 1. Class Crew Logic (`src/crews/content_crew/content_crew.py`)
File ini menggunakan decorator `@CrewBase` untuk memetakan Agent dan Task dari file YAML secara otomatis.

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class ContentCrew:
    """Content Crew untuk pembuatan konten blog"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(config=self.agents_config["planner"])

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"])

    @agent
    def editor(self) -> Agent:
        return Agent(config=self.agents_config["editor"])

    @task
    def planning_task(self) -> Task:
        return Task(config=self.tasks_config["planning_task"])

    @task
    def writing_task(self) -> Task:
        return Task(config=self.tasks_config["writing_task"])

    @task
    def editing_task(self) -> Task:
        return Task(config=self.tasks_config["editing_task"])

    @crew
    def crew(self) -> Crew:
        """Membuat instance Crew dengan proses sekuensial"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### 2. Celery Worker Task (`tasks/celery_tasks.py`)
File ini mendefinisikan fungsi yang akan dijalankan oleh Worker di latar belakang.

```python
from tasks.celery_app import celery_app
from src.crews.content_crew.content_crew import ContentCrew
import logging
import traceback

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="research")
def research(self, topic: str):
    # Update status ke RUNNING
    self.update_state(state='RUNNING', meta={'current': f'Memulai riset tentang {topic}'})
    try:
        # Menjalankan CrewAI secara sinkron di dalam worker
        result = ContentCrew().crew().kickoff(inputs={"topic": topic})
        return str(result)
    except Exception as e:
        logger.error(f"Task gagal: {e}\n{traceback.format_exc()}")
        raise
```

### 3. FastAPI Entry Point (`api/main.py`)
Endpoint untuk menerima request dari user dan mengecek status tugas.

```python
from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask

app = FastAPI(title="CrewAI Celery API")

class ResearchInput(BaseModel):
    topic: str

@app.post("/research")
async def start_research(input_data: ResearchInput):
    # Mengirim tugas ke Celery
    task = celeryTask.research.delay(input_data.topic)
    return {"task_id": task.id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.state,
        "result": None,
        "error": None
    }
    
    if task_result.state == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.state == 'FAILURE':
        response["error"] = str(task_result.info)
        
    return response
```

---

## 🏃 Cara Menjalankan Aplikasi (Step-by-Step)

Ikuti urutan ini dengan teliti. Pastikan setiap komponen berjalan sebelum lanjut ke langkah berikutnya.

### 1. Jalankan Redis (Message Broker)
Redis berfungsi sebagai perantara antara FastAPI (Kasir) dan Celery (Dapur).

*   **Cara Cepat (WSL Service):**
    ```bash
    sudo service redis-server start
    ```
*   **Verifikasi:**
    ```bash
    redis-cli ping
    ```
    *(Harus muncul jawaban **PONG**)*

---

### 2. Jalankan Celery Worker (Dapur)
Worker adalah proses yang akan melakukan pekerjaan berat (menjalankan AI Agents).

*   Buka **Terminal Baru** di WSL.
*   Masuk ke folder project: `cd INDOPRIMAFLOW` (atau folder project kamu).
*   Jalankan command:
    ```bash
    uv run celery -A tasks.celery_tasks worker --loglevel=info
    ```
    *(Tunggu sampai muncul log "celery@hostname ready".)*

---

### 3. Jalankan FastAPI Server (Kasir)
Server ini yang akan menerima request dari luar.

*   Buka **Terminal Baru** lagi di WSL.
*   Jalankan command:
    ```bash
    uv run uvicorn api.main:app --reload
    ```
    *(Aplikasi akan berjalan di `http://localhost:8000`)*

---

### 4. Cara Testing (Menggunakan CURL / Postman)

#### **A. Mengirim Tugas (Submit Task)**
Kirim request POST untuk memulai proses AI:
```bash
curl -X POST http://localhost:8000/research \
     -H "Content-Type: application/json" \
     -d '{"topic": "Artificial Intelligence in Manufacturing"}'
```
**Respon:** Kamu akan mendapatkan `task_id` (contoh: `{"task_id": "550e8400-e29b..."}`).

#### **B. Cek Status & Hasil**
Gunakan `task_id` di atas untuk melihat apakah AI sudah selesai bekerja:
```bash
curl http://localhost:8000/status/<MASUKKAN_TASK_ID_DISINI>
```

---

## 🛠️ Troubleshooting (Jika Error)

1.  **Error "Connection Refused" (Redis):** Pastikan `redis-server` sudah running (`sudo service redis-server status`).
2.  **Error "Module Not Found":** Pastikan kamu menjalankan command dengan `uv run` agar virtualenv terbaca otomatis.
3.  **Task Selalu "PENDING":** Pastikan Celery Worker sudah berjalan dan terhubung ke Redis yang sama.
4.  **API Key Error:** Pastikan file `.env` sudah berisi API Key yang valid (OpenAI/Serper/dll).

---
*Selamat! Anda sekarang memiliki sistem AI Agent yang scalable dan modern.*
