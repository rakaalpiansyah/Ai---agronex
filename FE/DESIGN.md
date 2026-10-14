# Design Direction: Agrosense IoT Precision Agronomy Dashboard

Dokumen spesifikasi desain antarmuka pengguna sesuai standar anti-slop, taste, dan impeccable untuk sistem pendukung keputusan rekomendasi tanaman dan strategi budidaya presisi berbasis IoT.

---

## 1. Design Read & Karakter Produk

- **Design Read**: Precision Agronomy & IoT Decision Support Dashboard for agronomy engineers, agricultural extension workers, and farm managers, with an ergonomic scientific language, leaning toward a crisp, bespoke design system with tabular data density, clear visual hierarchy, and restrained micro-motion.
- **Surface Mode**: **Operate** (Fokus pada penyelesaian tugas: pemantauan telemetri, kalibrasi variabel tanah/cuaca, evaluasi kesesuaian biologis, analisis ekonomi skenario, dan penentuan resep budidaya).
- **Karakter Visual**: Bersih, presisi, berbasis sains agronomi, fungsional, dan bebas dari ornamen generik AI (tidak ada gradien ungu neon, tidak ada kartu melayang tanpa tujuan, tidak ada klaim palsu, tidak ada tanda pisah em dash).

---

## 2. Dial Konfigurasi

- **DESIGN_VARIANCE: 6** (Terstruktur, logis, simetris fungsional dengan pengelompokan modular yang tegas).
- **MOTION_INTENSITY: 2** (Transisi mikro 150ms pada hover, perubahan tab, dan pembaruan metrik, tanpa animasi bouncing atau gerakan yang mengganggu konsentrasi analisis).
- **VISUAL_DENSITY: 6** (Kepadatan data operasional tinggi namun tetap memiliki ruang bernapas yang bersih, angka telemetri berformat tabular monospace untuk perbandingan presisi).

---

## 3. Sistem Warna (Color Tokens)

Mematuhi aturan R-29 (maksimal 2-3 warna inti + aksen semantik fungsional terkalibrasi):

### Tema Terang (Light Mode - Default)
- **Background Utama (Canvas)**: `#f8fafc` (Slate 50)
- **Permukaan Kartu (Surface)**: `#ffffff` (Pure White)
- **Permukaan Elevasi (Elevated)**: `#f1f5f9` (Slate 100)
- **Batas Elemen (Border)**: `#e2e8f0` (Slate 200)
- **Batas Interaktif / Focus**: `#059669` (Emerald 600)
- **Teks Utama**: `#0f172a` (Slate 900 - kontras 15:1 memenuhi WCAG AAA)
- **Teks Sekunder**: `#475569` (Slate 600 - kontras 7:1)
- **Teks Muted**: `#64748b` (Slate 500 - kontras 4.6:1)

### Tema Gelap (Dark Mode)
- **Background Utama (Canvas)**: `#090e17` (Deep Obsidian Navy)
- **Permukaan Kartu (Surface)**: `#111a2e` (Elevated Slate Navy)
- **Permukaan Elevasi (Elevated)**: `#1b2640` (Focused Navy)
- **Batas Elemen (Border)**: `#22314e` (Slate Border Dark)
- **Batas Interaktif / Focus**: `#10b981` (Emerald 500)
- **Teks Utama**: `#f8fafc` (Slate 50 - kontras 14:1)
- **Teks Sekunder**: `#94a3b8` (Slate 400 - kontras 7:1)
- **Teks Muted**: `#64748b` (Slate 500)

### Aksen Semantik Agronomi
- **Primer (Agronomi / Subur / S1)**: `#059669` (Emerald 600) | Dark: `#10b981`
- **Peringatan / Pembatas (Marginal / S2)**: `#d97706` (Amber 600) | Dark: `#f59e0b`
- **Hidrologi / Neraca Air**: `#0284c7` (Sky 600) | Dark: `#38bdf8`
- **Kritis / Bahaya (Tidak Sesuai / N)**: `#e11d48` (Rose 600) | Dark: `#fb7185`

---

## 4. Tipografi & Data Representation

- **Font Antarmuka**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Font Angka Telemetri & Metrik**: `JetBrains Mono, ui-monospace, Menlo, Consolas, monospace` dengan `font-variant-numeric: tabular-nums` agar angka tidak bergeser saat nilai berubah.
- **Skala Ukuran**:
  - H1 (Header Brand): 20px, font-weight 700
  - H2 (Judul Kartu / Hero Crop): 18px, font-weight 700
  - H3 (Subseksi / Papan Peringkat): 15px, font-weight 600
  - Metrik Hero (Angka Besar): 28px, font-weight 700
  - Body Text: 14px, line-height 1.5
  - Label / Caption: 12px, font-weight 500, letter-spacing 0.02em

---

## 5. Fitur Ergonomi & Craftsmanship Antarmuka ("Enak Digunakan")

1. **Dual-Control Sensor Inputs**: Setiap parameter sensor memiliki slider responsif PLUS input numerik langsung dengan tombol stepper, memungkinkan pengguna menggeser cepat atau mengetik nilai desimal akurat.
2. **Kategori Input Terstruktur**: Mengelompokkan 14 variabel telemetri ke dalam 3 grup logis:
   - *Klimatologi & Udara* (Suhu rata-rata, min, max, RH, radiasi matahari, angin)
   - *Hidrologi & Air* (Kelembapan VWC tanah, curah hujan 30 hari, hari observasi)
   - *Kimia & Hara Tanah* (pH tanah, salinitas EC, hara N, P, K)
3. **Pita Metrik Indeks Cepat (Quick Agronomic Metrics Strip)**: Menampilkan VPD Tetens, GDD kumulatif, reference $ET_0$ Penman-Monteith, dan Neraca Air seketika setelah evaluasi.
4. **Tampilan Hasil Multi-Tab Terpadu**:
   - *Tab 1: Rekomendasi Utama & Resep Presisi* (Hero Card #1, 5 faktor pembatas Liebig, 3 skenario laba IDR, jadwal jendela tanam, irigasi, dosis pemupukan defisit, mitigasi risiko, narasi terverifikasi).
   - *Tab 2: Papan Peringkat 10 Komoditas* (Tabel komparasi lengkap seluruh 10 komoditas terdaftar yang diurutkan berdasarkan skor gabungan, kelas FAO, faktor pembatas, estimasi panen, dan laba bersih).
   - *Tab 3: Neraca Air & Indeks FAO-56* (Analisis detail evapotranspirasi, defisit air tanaman, dan akumulasi panas).
5. **Modal Katalog Komoditas Interaktif**: Dilengkapi pencarian instan dan filter kategori pangan, palawija, hortikultura sayuran, dan sayuran umbi.
6. **Aksesibilitas & Keyboard Navigation**: Indikator fokus cincin ganda (`focus-visible`), penutupan modal via tombol Escape, dan dukungan navigasi tombol Tab penuh.
7. **Kepatuhan Anti-Slop Mutlak**: Tidak ada karakter em dash (`—`), tidak ada testimonial fiktif, tidak ada animasi loncat, dan semua teks menggunakan istilah agronomi baku dalam Bahasa Indonesia.
