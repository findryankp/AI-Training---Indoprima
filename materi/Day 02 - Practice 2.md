# Day 02 - Practice 2: Pengenalan Tools dan Custom Tools pada CrewAI

Pada CrewAI, kita diberikan berbagai macam tools untuk menunjang pekerjaan dari Agent. Secara detail dapat dilihat pada link berikut: [CrewAI Tools Documentation](https://docs.crewai.com/en/concepts/tools)

## 📋 Contoh Kasus: Document Analyzer (RAG Sederhana)

Misal kita ingin membuat agent yang dapat membaca sebuah dokumen teks (`.txt`) karena ringan, dan memberikan report-report penting. Kita dapat awali dengan membuat sebuah crew baru.

### 1. Menambahkan Crew Baru
Gunakan perintah berikut di terminal untuk menambahkan crew dengan nama `crew_rag`:
```bash
crewai flow add-crew crew_rag
```
Maka akan secara otomatis menambahkan sebuah folder baru di dalam folder `crews` dengan nama `crew_rag`.

### 2. Konfigurasi YAML (`agents.yaml` & `tasks.yaml`)

Setelah folder dibuat, ganti isi file konfigurasi di `src/crews/crew_rag/config/` menjadi seperti berikut:

#### **agents.yaml**
```yaml
doc_analyzer:
  role: >
    document extractor for {file}
  goal: >
    extract from {file}
  backstory: >
    You are meticulous when reading documents, so you can report your extraction result
```

#### **tasks.yaml**
```yaml
documen_analyzer_task:
  description: >
    Conduct a thorough extract of an existing {file}, and make sure you identify
    every part from the report, particularly those related to sales figures.
  expected_output: >
    A list with 5 insight about the document
  agent: doc_analyzer
```

---

### 3. Implementasi Logic Crew (`crew_rag.py`)

Terlihat pada bagian agent, kita perlu menambahkan parameter bernama `tools`. Parameter tersebut berfungsi untuk membaca file input. Kita akan menggunakan `FileReadTool` yang merupakan tool bawaan CrewAI.

#### **Import Tools**
Buka file `src/crews/crew_rag/crew_rag.py` dan tambahkan import berikut:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import RagTool, PDFSearchTool, FileReadTool
```

*Note: Pada tutorial ini, kita hanya fokus pada `FileReadTool` karena paling ringan untuk pemrosesan komputasi.*

#### **Definisi Class Crew**
Setting agent dan task dengan memasukkan tool ke dalam parameter `tools`:

```python
@CrewBase
class CrewRag():
    """CrewRag crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Inisialisasi Tool
    fileRead = FileReadTool()

    @agent
    def doc_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['doc_analyzer'], # type: ignore[index]
            verbose=True,
            tools=[self.fileRead] # Menambahkan tool ke agent
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['documen_analyzer_task'], # type: ignore[index]
        )
```

---

### 4. Membuat Celery Task (`tasks/celery_tasks.py`)

Karena pada YAML kita sudah mendefinisikan variabel `{file}`, maka pada task Celery kita perlu mengirimkan input tersebut.

```python
@celery_app.task(bind=True, name="doc_analyzer")
def doc_analyzer(self, file: str):
    self.update_state(state='RUNNING', meta={'current': f'start job for {file}'})
    try:
        # Menjalankan crew dengan input variable 'file'
        result = CrewRag().crew().kickoff(inputs={"file": file})
        return str(result)
    except Exception as e:
        logger.error(f"Task failed with error: {e}\n{traceback.format_exc()}")
        raise
```

---

### 5. Membuat Endpoint FastAPI (`api/main.py`)

Kita buat endpoint `/rag` yang menerima upload file. Kita lakukan pengecekan agar file yang diupload adalah `text/plain` (txt) saja untuk demonstrasi yang ringan.

```python
@app.post("/rag")
async def rag(file: UploadFile = File(...)):
    # Validasi tipe file
    if file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="File must be a .txt file")

    # Simpan file ke lokasi temporary
    file_extension = os.path.splitext(file.filename)[1] or ".txt"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(FILE_FOLDER, unique_filename)

    # Simpan konten file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Kirim ke Celery task secara background
    task = celeryTask.doc_analyzer.delay(file_path)
    
    return {
        "task_id": task.id, 
        "file_path": file_path
    }
```

---

### 6. Testing Menggunakan Postman

Untuk mengirim file, kita bisa gunakan Postman dengan cara:
1.  Pilih method **POST**.
2.  Masukkan URL: `http://127.0.0.1:8000/rag`.
3.  Pada tab **Body**, pilih **form-data**.
4.  Tambahkan key `file`, ubah tipe inputnya menjadi **File**, lalu pilih file `.txt` yang ingin dianalisis.
5.  Klik **Send**.

Jika berhasil, Anda akan mendapatkan `task_id` yang bisa digunakan untuk mengecek status pengerjaan oleh agent di endpoint `/status/{task_id}`.

---
### 7. Kolaborasi Multi-Agent: Menambahkan Agent Penyederhana (Resumer)

Hasil dari agent sebelumnya (`doc_analyzer`) seringkali masih terlalu panjang dan detail sehingga sulit dipahami dengan cepat. Untuk itu, kita perlu menambahkan satu agent lagi yang fokus pada penyampaian data yang lebih simpel.

Kita akan membuat agent baru bernama **doc_resumer** yang berfungsi untuk melakukan resume (ringkasan) terhadap hasil analisa dari agent `doc_analyzer`.

#### **Update agents.yaml**
Tambahkan agent `doc_resumer` pada file `src/crews/crew_rag/config/agents.yaml`:

```yaml
doc_resumer:
  role: >
    Senior Report Simplification Specialist
  goal: >
    Transform complex and lengthy reports into exactly 5 clear, easy-to-understand, and actionable insight points
  backstory: >
    You are a data communication expert with 15 years of experience simplifying complex business reports. You have a unique ability to cut through information noise and extract the core essence from any report. Your clients praise your ability to make complicated data understandable for all management levels. Your principle: "If you can't explain it in 5 simple points, you haven't truly understood it yet."
```

#### **Update tasks.yaml**
Tambahkan task untuk `doc_resumer` dan perhatikan penggunaan **context**:

```yaml
doc_resumer_task:
  description: >
    INPUT ANALYSIS:
    The original report to be simplified is as follows:

    SPECIFIC INSTRUCTIONS:
    Your task is to analyze the above report and generate exactly
    5 (FIVE) insight points that are:

    1. **CLEAR**: Use everyday language that is easy to understand
    2. **CONCISE**: Maximum 2 sentences per point
    3. **IMPACTFUL**: Highlight the most important/interesting findings
    4. **STRUCTURED**: Each point contains one main idea
    5. **ACTIONABLE**: Provides clear direction or recommendations

    EXPECTED OUTPUT FORMAT:
    # 5 KEY INSIGHTS: [Brief Report Title]
    ## Insight 1: [Insight Title]
    [1-2 sentence clear and concise explanation]
    ... (sampai Insight 5)

    IMPORTANT RULES:
    - DO NOT generate more than 5 points
    - DO NOT use technical jargon without explanation
    - DO NOT copy sentences directly from the original report
    - MUST use proper English grammar
    - MUST include a title for each insight

  expected_output: >
    5 structured insight points in the specified format, each with a title and 1-2 sentence explanation. Total output no more than 15 lines for explanations.
  agent: doc_resumer
  context:
    - documen_analyzer_task
```

> [!IMPORTANT]
> Fungsi dari **context** adalah membuat task yang dijalankan agent akan berfokus kepada hasil yang dihasilkan oleh task sebelumnya, dalam kasus ini adalah `documen_analyzer_task`.

#### **Update crew_rag.py**
Lengkapi class `CrewRag` dengan menambahkan method `@agent` dan `@task` baru:

```python
    @agent
    def doc_resumer(self) -> Agent:
        return Agent(
            config=self.agents_config['doc_resumer'],
            verbose=True,
        )

    @task
    def doc_resumer_task(self) -> Task:
        return Task(
            config=self.tasks_config['doc_resumer_task'],
        )
```

---

### 8. Hasil Akhir (Multi-Agent Cooperation)

Dengan menggunakan 2 agent yang saling bekerja sama, kita telah membuat sebuah crew yang mampu mengerjakan tugas kompleks dengan output yang jauh lebih terarah.

**Hasil Output:**
Output sekarang tidak lagi berupa data mentah yang panjang, melainkan ringkasan **5 Key Insights** yang terstruktur, lengkap dengan judul, penjelasan singkat, dan rekomendasi yang bisa langsung dipahami oleh manajemen.

---
### 9. 🏃 Cara Menjalankan Aplikasi

Ikuti urutan berikut untuk menjalankan seluruh sistem:

#### **A. Jalankan Redis**
Redis harus aktif sebagai perantara data (Message Broker).
```bash
sudo service redis-server start
```

#### **B. Jalankan Celery Worker**
Buka terminal baru di folder root project, lalu jalankan:
```bash
uv run celery -A tasks.celery_tasks worker --loglevel=info
```
*Pastikan log menunjukkan worker sudah "ready".*

#### **C. Jalankan FastAPI Server**
Buka terminal baru lagi, lalu jalankan:
```bash
uv run uvicorn api.main:app --reload
```

---

### 10. ⚡ Otomatisasi Postman (Tips & Trick)

Agar Anda tidak perlu menyalin `task_id` secara manual setiap kali melakukan request, kita bisa menggunakan fitur **Tests** pada Postman.

1.  **Impor Koleksi Terbaru**: Pastikan Anda menggunakan file `materi/CrewAI_API.postman_collection.json` yang sudah diperbarui.
2.  **Script Otomatis**: Pada request **Start Research** dan **Start RAG**, saya sudah menambahkan script berikut di tab **Tests**:
    ```javascript
    var jsonData = pm.response.json();
    if (jsonData.task_id) {
        pm.collectionVariables.set("task_id", jsonData.task_id);
    }
    ```
3.  **Cara Pakai**:
    *   Klik **Send** pada request `/research` atau `/rag`.
    *   Postman akan otomatis menyimpan `task_id` ke dalam variabel koleksi.
    *   Buka request **Check Status**, lalu langsung klik **Send**. URL akan otomatis menggunakan variabel `{{task_id}}` yang baru.

---
*Selamat! Sekarang proses pengembangan dan testing Anda menjadi jauh lebih cepat dan efisien.*

