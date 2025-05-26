# Internal Web Search Engine

Mesin pencari internal dengan algoritma BFS/DFS untuk organisasi internal. Sistem ini dapat melakukan crawling halaman web secara otomatis dan menyediakan fitur pencarian yang cepat dengan caching.

## 🚀 Fitur Utama

- **Web Crawling**: Algoritma BFS dan DFS untuk crawling halaman web
- **Full-Text Search**: Pencarian menggunakan TF-IDF dan cosine similarity
- **Route Tracking**: Pelacakan jalur navigasi antar halaman
- **Caching System**: Sistem cache untuk meningkatkan performa pencarian
- **Real-time Status**: Monitoring status crawling secara real-time
- **Search History**: Riwayat pencarian dengan statistik performa
- **Configurable**: Konfigurasi yang dapat disesuaikan melalui UI
- **Export Data**: Export hasil crawling ke format JSON

## 📁 Struktur Proyek

\`\`\`
machine/
├── app/                    # Frontend Next.js
│   ├── page.tsx           # Halaman utama aplikasi
│   └── components/        # Komponen UI
├── crawler/               # Mesin crawler Python
│   ├── web_crawler.py     # Implementasi web crawler
│   └── search_engine.py   # Mesin pencari
├── tests/                 # Unit tests
│   ├── test_crawler.py    # Test untuk crawler
│   └── test_search.py     # Test untuk search engine
├── database/              # Database SQLite
│   └── search_index.db    # File database utama
├── logs/                  # Log files
├── deliverables/          # Deliverables proyek
├── config.py              # Konfigurasi global
├── main.py                # FastAPI server
├── requirements.txt       # Dependencies Python
└── README.md              # Dokumentasi ini
\`\`\`

## 🛠️ Instalasi dan Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm atau yarn

### Backend Setup

1. **Clone repository dan masuk ke direktori:**
\`\`\`bash
git clone <repository-url>
cd machine
\`\`\`

2. **Buat virtual environment:**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
\`\`\`

3. **Install dependencies:**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Jalankan backend server:**
\`\`\`bash
python main.py
\`\`\`

Backend akan berjalan di `http://localhost:8000`

### Frontend Setup

1. **Masuk ke direktori frontend:**
\`\`\`bash
cd app
\`\`\`

2. **Install dependencies:**
\`\`\`bash
npm install
# atau
yarn install
\`\`\`

3. **Set environment variable (optional):**
\`\`\`bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
\`\`\`

4. **Jalankan frontend:**
\`\`\`bash
npm run dev
# atau
yarn dev
\`\`\`

Frontend akan berjalan di `http://localhost:3000`

## ⚙️ Konfigurasi

### File config.json

Sistem akan otomatis membuat file `config.json` dengan pengaturan default. Anda dapat mengubah konfigurasi melalui UI atau edit file langsung:

\`\`\`json
{
  "seed_urls": [
    "https://www.upi.edu",
    "https://fpmipa.upi.edu"
  ],
  "max_pages": 100,
  "max_depth": 3,
  "crawl_delay": 1.0,
  "crawl_algorithm": "BFS",
  "user_agent": "InternalSearchBot/1.0 (Educational Purpose)",
  "allowed_domains": [
    "upi.edu",
    "fpmipa.upi.edu"
  ],
  "cache_enabled": true,
  "cache_ttl": 3600
}
\`\`\`

### Parameter Konfigurasi

- **seed_urls**: URL awal untuk memulai crawling
- **max_pages**: Maksimal halaman yang akan di-crawl
- **max_depth**: Kedalaman maksimal crawling
- **crawl_delay**: Jeda antar request (detik)
- **crawl_algorithm**: Algoritma crawling (BFS/DFS)
- **allowed_domains**: Domain yang diizinkan untuk di-crawl
- **cache_enabled**: Aktifkan/nonaktifkan cache
- **cache_ttl**: Waktu hidup cache (detik)

## 📖 Cara Penggunaan

### 1. Konfigurasi System

1. Buka aplikasi di browser (`http://localhost:3000`)
2. Masuk ke tab **"Pengaturan"**
3. Atur seed URLs, domain yang diizinkan, dan parameter lainnya
4. Klik **"Simpan Konfigurasi"**

### 2. Memulai Crawling

1. Masuk ke tab **"Crawling"**
2. Klik **"Mulai Crawling"**
3. Monitor progress crawling secara real-time
4. Crawling akan berhenti otomatis setelah mencapai batas yang ditentukan

### 3. Melakukan Pencarian

1. Masuk ke tab **"Pencarian"**
2. Masukkan kata kunci di search box
3. Tekan Enter atau klik tombol **"Cari"**
4. Lihat hasil pencarian dengan skor relevansi
5. Klik **"Lihat Rute Link"** untuk melihat jalur navigasi

### 4. Melihat Statistik

1. Masuk ke tab **"Statistik"**
2. Lihat informasi seperti:
   - Total halaman ter-index
   - Total pencarian
   - Status cache
   - Ukuran database

## 🧪 Testing

### Menjalankan Unit Tests

\`\`\`bash
# Install pytest jika belum ada
pip install pytest pytest-asyncio

# Jalankan semua tests
pytest tests/

# Jalankan test spesifik
pytest tests/test_crawler.py
pytest tests/test_search.py

# Jalankan dengan coverage
pip install pytest-cov
pytest --cov=crawler tests/
\`\`\`

### Test Coverage

Tests mencakup:
- Validasi URL dan domain
- Ekstraksi konten dan link
- Algoritma crawling (BFS/DFS)
- Fungsi pencarian dan indexing
- Sistem caching
- Database operations

## 🔧 API Endpoints

### Crawling
- `POST /crawl/start` - Mulai crawling
- `POST /crawl/stop` - Hentikan crawling
- `GET /crawl/status` - Status crawling

### Search
- `POST /search` - Lakukan pencarian
- `GET /history` - Riwayat pencarian
- `GET /stats` - Statistik sistem

### Configuration
- `GET /config` - Ambil konfigurasi
- `PUT /config` - Update konfigurasi

### Cache
- `POST /cache/clear` - Bersihkan cache

### Export
- `GET /export/pages` - Export data halaman

## 📊 Kompleksitas Algoritma

### Web Crawling
- **BFS**: O(V + E) dimana V = jumlah halaman, E = jumlah link
- **DFS**: O(V + E) dengan space complexity O(h) dimana h = kedalaman maksimal

### Search Engine
- **Indexing**: O(n × m) dimana n = jumlah dokumen, m = rata-rata kata per dokumen
- **Query**: O(k × m) dimana k = jumlah query terms, m = ukuran vocabulary
- **Ranking**: O(n log n) untuk sorting hasil

### Caching
- **Cache Hit**: O(1)
- **Cache Miss**: O(search_complexity)

## 🚨 Troubleshooting

### Backend Issues

**Error: "ModuleNotFoundError"**
\`\`\`bash
# Pastikan virtual environment aktif dan dependencies ter-install
pip install -r requirements.txt
\`\`\`

**Error: "Database locked"**
\`\`\`bash
# Tutup semua koneksi database dan restart server
rm database/search_index.db  # Hapus database jika perlu
python main.py
\`\`\`

### Frontend Issues

**Error: "Cannot connect to API"**
- Pastikan backend berjalan di port 8000
- Check CORS settings di FastAPI
- Verify `NEXT_PUBLIC_API_URL` environment variable

### Crawling Issues

**Crawling tidak menemukan halaman**
- Check konfigurasi `allowed_domains`
- Verify seed URLs dapat diakses
- Pastikan tidak ada firewall yang memblokir

**Crawling lambat**
- Increase `crawl_delay` untuk menghormati server
- Decrease `max_concurrent_requests`
- Check network connection

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## 📝 License

Project ini menggunakan MIT License. Lihat file `LICENSE` untuk detail.

## 👥 Tim Pengembang

- **Developer 1**: Backend & Crawler Engine
- **Developer 2**: Frontend & UI/UX
- **Developer 3**: Database & Search Algorithm
- **Developer 4**: Testing & Documentation

## 📞 Support

Jika ada pertanyaan atau issue:
1. Buka GitHub Issues
2. Email: support@internalsearch.com
3. Documentation: [Wiki Page]

## 🗓️ Roadmap

### Version 1.1
- [ ] Advanced search filters
- [ ] Real-time notifications
- [ ] Multi-language support
- [ ] Performance optimizations

### Version 1.2
- [ ] Machine learning untuk ranking
- [ ] Advanced analytics dashboard
- [ ] API rate limiting
- [ ] Docker containerization

### Version 2.0
- [ ] Distributed crawling
- [ ] Elasticsearch integration
- [ ] Advanced NLP features
- [ ] Mobile application
\`\`\`

```plaintext file="deliverables/list_anggota.txt"
DAFTAR ANGGOTA TIM PROYEK INTERNAL WEB SEARCH ENGINE

======================================================

Proyek: Internal Web Search Engine dengan Algoritma BFS/DFS
Mata Kuliah: Struktur Data dan Algoritma
Semester: Ganjil 2024/2025

======================================================

ANGGOTA TIM:

1. Nama: [Nama Anggota 1]
   NIM: [NIM Anggota 1]
   Peran: Lead Developer & Backend Engineer
   Tanggung Jawab:
   - Implementasi web crawler dengan algoritma BFS/DFS
   - Pengembangan REST API menggunakan FastAPI
   - Integrasi database dan sistem caching
   - Koordinasi tim dan project management

2. Nama: [Nama Anggota 2]
   NIM: [NIM Anggota 2]
   Peran: Frontend Developer & UI/UX Designer
   Tanggung Jawab:
   - Pengembangan antarmuka pengguna dengan Next.js
   - Desain dan implementasi komponen UI
   - Integrasi frontend dengan backend API
   - User experience optimization

3. Nama: [Nama Anggota 3]
   NIM: [NIM Anggota 3]
   Peran: Search Engine Developer & Database Administrator
   Tanggung Jawab:
   - Implementasi algoritma pencarian TF-IDF
   - Desain dan optimasi database SQLite
   - Pengembangan sistem indexing dan ranking
   - Performance tuning untuk search queries

4. Nama: [Nama Anggota 4]
   NIM: [NIM Anggota 4]
   Peran: Quality Assurance & Documentation Specialist
   Tanggung Jawab:
   - Pengembangan unit tests dan integration tests
   - Dokumentasi teknis dan user manual
   - Testing dan debugging aplikasi
   - Analisis kompleksitas algoritma

======================================================

KONTRIBUSI SETIAP ANGGOTA:

Anggota 1 (Backend):
- Implementasi WebCrawler class dengan algoritma BFS dan DFS
- Pengembangan FastAPI endpoints untuk crawling dan search
- Konfigurasi database SQLite dan tabel-tabelnya
- Implementasi sistem caching untuk optimasi performa

Anggota 2 (Frontend):
- Pengembangan komponen React untuk interface pengguna
- Implementasi real-time status monitoring untuk crawling
- Desain responsive untuk berbagai ukuran layar
- Integrasi dengan backend API menggunakan fetch

Anggota 3 (Search Engine):
- Implementasi TF-IDF vectorization untuk indexing
- Pengembangan algoritma cosine similarity untuk ranking
- Optimasi query performance dan database indexing
- Implementasi route tracking untuk link analysis

Anggota 4 (QA & Documentation):
- Pengembangan test suite dengan pytest
- Dokumentasi README.md dan panduan penggunaan
- Analisis kompleksitas waktu dan ruang algoritma
- Testing berbagai skenario crawling dan pencarian

======================================================

PEMBAGIAN TUGAS BERDASARKAN TIMELINE:

Week 1-2: Perencanaan dan Desain Sistem
- Semua anggota: Diskusi requirement dan arsitektur
- Anggota 1: Setup project structure dan environment
- Anggota 2: Wireframe dan mockup UI
- Anggota 3: Desain database schema
- Anggota 4: Perencanaan testing strategy

Week 3-4: Implementasi Core Features
- Anggota 1: Implementasi web crawler
- Anggota 2: Pengembangan frontend components
- Anggota 3: Implementasi search engine
- Anggota 4: Setup testing framework

Week 5-6: Integrasi dan Testing
- Anggota 1: API development dan integrasi
- Anggota 2: Frontend-backend integration
- Anggota 3: Database optimization
- Anggota 4: Comprehensive testing

Week 7-8: Finalisasi dan Dokumentasi
- Semua anggota: Bug fixing dan polishing
- Anggota 4: Finalisasi dokumentasi
- Semua anggota: Persiapan presentasi

======================================================

TOOLS DAN TEKNOLOGI YANG DIGUNAKAN:

Backend:
- Python 3.8+
- FastAPI framework
- aiohttp untuk async HTTP requests
- SQLite untuk database
- scikit-learn untuk TF-IDF

Frontend:
- Next.js 14+ dengan App Router
- TypeScript untuk type safety
- Tailwind CSS untuk styling
- shadcn/ui untuk komponen UI

Testing:
- pytest untuk Python testing
- pytest-asyncio untuk async testing
- Coverage.py untuk test coverage

Development Tools:
- Git untuk version control
- VS Code sebagai IDE
- Postman untuk API testing

======================================================

METRIK KEBERHASILAN PROYEK:

1. Fungsionalitas:
   ✅ Web crawler dapat berjalan dengan algoritma BFS/DFS
   ✅ Search engine dapat menemukan dan ranking halaman
   ✅ Interface pengguna yang responsif dan user-friendly
   ✅ Real-time monitoring status crawling

2. Performance:
   ✅ Crawling speed optimal dengan delay konfigurasi
   ✅ Search response time &lt; 500ms untuk database &lt; 1000 halaman
   ✅ Cache hit ratio > 70% untuk query berulang
   ✅ Memory usage efficient untuk operasi concurrent

3. Quality:
   ✅ Test coverage > 80% untuk core functionalities
   ✅ Zero critical bugs dalam testing environment
   ✅ Dokumentasi lengkap dan mudah dipahami
   ✅ Code yang clean dan maintainable

======================================================

LESSONS LEARNED:

1. Pentingnya perencanaan arsitektur yang matang
2. Koordinasi tim yang efektif melalui regular meetings
3. Testing yang comprehensive sejak awal development
4. Documentation yang real-time dan up-to-date
5. Optimasi performance yang berkelanjutan

======================================================

ACKNOWLEDGMENTS:

Tim mengucapkan terima kasih kepada:
- Dosen pengampu mata kuliah Struktur Data dan Algoritma
- Asisten laboratorium yang telah membantu
- Teman-teman yang memberikan feedback dan testing
- Online resources dan open source communities

======================================================

Tanggal: [Tanggal Pengumpulan]
Tempat: [Nama Universitas/Institusi]

Dibuat oleh Tim [Nama Tim/Kelas]
