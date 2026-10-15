# 📱 Panduan Presentasi: Cara Kerja & Algoritma (Bahasa Basic IT)

> **Catatan Baca di HP:** Dokumen ini disusun ringkas dengan poin-poin to-the-point, bahasa programmer/IT dasar, dan format yang nyaman di-scroll lewat smartphone saat persiapan presentasi.

---

## ⚡ 1. Konsep Dasar (Elevator Pitch 30 Detik)

* **Apa sistem ini?**
  Aplikasi backend & frontend berbasis **FastAPI + React** yang merekomendasikan tanaman terbaik untuk suatu lahan pertanian, lengkap dengan jadwal tanam, takaran pupuk, dan hitungan potensi cuannya.
* **Analogi IT Sederhana:**
  Sistem ini bekerja persis seperti **Recommendation Engine** di Netflix atau Spotify:
  * Di Spotify: Data riwayat dengar lagu $\rightarrow$ dihitung kemiripannya $\rightarrow$ keluar rekomendasi playlist.
  * Di Sistem Kita: Data sensor tanah & cuaca $\rightarrow$ dicocokkan dengan database tanaman $\rightarrow$ keluar rekomendasi komoditas yang paling optimal dan minim risiko gagal panen.

---

## 🏗️ 2. Arsitektur Input - Process - Output

Sistem bekerja dalam 5 tahapan pipeline yang sangat terstruktur:

```
[Hardware Sensor] 
       │ (JSON Payload via HTTP/MQTT)
       ▼
[1. Ingestion & Quality Control] ──> Data kotor disaring (filter spike, cek sensor mati)
       │
       ▼
[2. Medallion Storage Pipeline]  ──> Simpan bertingkat: Bronze (mentah) -> Silver (bersih) -> Gold (fitur)
       │
       ▼
[3. Rule-Based Scoring (CSI)]    ──> Cek batas toleransi biologi tanaman (Hukum Bottleneck Liebig)
       │
       ▼
[4. Machine Learning (AI Model)] ──> Random Forest voting tanaman terbaik + Prediksi tonase panen
       │
       ▼
[5. Strategy Decision Engine]    ──> Hitung formula: (50% Cocok) + (30% Profit) - (20% Risiko)
       │
       ▼
[Output: REST API & Web UI]      ──> Response JSON rapi + Dashboard interaktif untuk user
```

---

## 🧩 3. Bedah Algoritma dengan Bahasa Basic IT

Sistem ini tidak hanya mengandalkan "AI abu-abu", tapi memakai kombinasi **Logika Matematis + Machine Learning + Safety Fallback**.

---

### Algoritma 1: Data Sanitization & Hampel Filter (Pembersih Spike)
* **Masalah:** Sensor di kebun sering kaget karena gangguan listrik/kabel goyang. Tiba-tiba suhu membaca $99^\circ\text{C}$ padahal aslinya $28^\circ\text{C}$.
* **Logika IT:**
  1. **Boundary Check (Validasi Rentang):** Pakai validasi `if value < min or value > max: drop()`. Contoh: pH tanah di luar 3 s.d 10 otomatis dibuang.
  2. **Stuck Sensor Detection:** Menghitung *Rolling Standard Deviation*. Jika deviasi $= 0$ selama 48 jam (angkanya konstan mati), sistem menandai sensor sedang offline/rusak.
  3. **Hampel Filter (Median Filter):** Mengambil jendela data bergerak (misal 5 data terakhir), hitung nilai tengah (median). Jika ada 1 data yang melonjak jauh di atas toleransi deviasi median, data itu diganti dengan nilai mediannya.

---

### Algoritma 2: CSI (Crop Suitability Index) & Liebig's Bottleneck
* **Tujuan:** Menghitung seberapa cocok kondisi lahan dengan kebutuhan dasar tanaman (database standar PBB / FAO EcoCrop).
* **Logika IT:**
  1. **Normalisasi Skor Trapesium (0.0 s.d 1.0):**
     * Nilai di rentang optimal $\rightarrow$ return `1.0` (Sangat Sesuai).
     * Nilai di luar batas mutlak $\rightarrow$ return `0.0` (Tanaman Pasti Mati).
     * Nilai di antaranya $\rightarrow$ interpolasi linear gradual ($0.0 \rightarrow 1.0$).
  2. **Hukum Minimum Liebig (Bottleneck Principle):**
     * Di dunia IT, performa aplikasi dibatasi oleh komponen terlambat (misal query database lelet).
     * Di biologi tanaman juga sama: Jika suhu optimal (`1.0`), air cukup (`1.0`), tapi tanah terlalu asam (`0.1`), maka tanaman tetap gagal tumbuh!
     * Rumus Liebig: `liebig_score = min(factor_scores.values())`.
  3. **Composite Baseline Score:**
     $$\text{Skor CSI} = (0.60 \times \text{Rata-rata Geometrik}) + (0.40 \times \text{Skor Minimum/Bottleneck})$$
     *Hasilnya:* Tanaman yang punya 1 titik fatal otomatis langsung gugur dari peringkat atas.

---

### Algoritma 3: Machine Learning (Random Forest) + TreeSHAP (Explainability)
* **Kenapa Random Forest?**
  Untuk data berupa tabel angka (data tabular), Random Forest terbukti lebih stabil, anti-overfitting, dan tidak butuh jutaan baris data dibanding Deep Learning/Neural Network.
* **Cara Kerjanya:**
  1. **Classifier (Klasifikasi):** Terdiri dari $100$ Pohon Keputusan (*Decision Trees*). Masing-masing pohon menguji kombinasi variabel tanah dan cuaca, lalu melakukan **voting terbanyak** untuk menentukan tanaman mana yang paling tepat.
  2. **Regressor (Prediksi Hasil Panen):** Memprediksi angka estimasi panen dalam satuan ton per hektar.
  3. **TreeSHAP (Fitur Penjelas / Debugger Model):**
     * Sering kali AI dituduh sebagai *Black Box* (tahu hasil tapi gak tahu alasannya).
     * TreeSHAP membongkar bobot kontribusi setiap variabel:
       * *Faktor Pendukung:* `"Kelembapan tanah 70% (+0.25 ke probabilitas Padi)"`.
       * *Faktor Penghambat:* `"Kadar Fosfor rendah (-0.10 ke probabilitas Padi)"`.

---

### Algoritma 4: Multi-Criteria Strategy Engine & Confidence Gate
* **Masalah:** Tanaman yang subur belum tentu menguntungkan secara bisnis, dan tanaman yang mahal belum tentu aman dari risiko iklim.
* **Logika IT (Weighted Ranking):**
  $$\text{Composite Score} = (0.50 \times \text{Kecocokan}) + (0.30 \times \text{Profit Ternormalisasi}) - (0.20 \times \text{Penalti Risiko})$$
  * **Catatan Pintar:** Profit hanya bernilai tinggi jika dikalikan skor kecocokan biologis. Jika tanaman tidak bisa tumbuh di lahan tersebut, potensi cuan setinggi apa pun di pasar nilainya tetap 0.
* **Confidence Gate (Safety Fallback / Exception Handling):**
  ```python
  if data_completeness < 0.70:
      status = "NEEDS_AGRONOMIST_REVIEW"
      notes = "Data sensor kurang dari 70%, sistem tidak boleh ambil keputusan otomatis."
  elif primary_score >= 0.70:
      status = "APPROVED"  # Rekomendasi Valid & Aman
  ```

---

## 📊 4. Cheat-Sheet Slide Presentasi (7 Slide Siap Pakai)

Gunakan contekan ini saat Anda berdiri di depan layar presentasi:

| Slide | Topik Slide | Poin Utama yang Diucapkan |
| :--- | :--- | :--- |
| **Slide 1** | **Masalah** | Petani sering gagal panen karena sistem "tebak-tebakan" & ikut-ikutan tren pasar tanpa tahu kondisi riil tanahnya. |
| **Slide 2** | **Solusi Kita** | Membangun platform terpadu: IoT mengumpulkan data fisik lahan $\rightarrow$ AI memproses $\rightarrow$ keluar rekomendasi tanaman + resep pupuk + kalkulasi cuan. |
| **Slide 3** | **Data Ingestion** | Data sensor disaring dengan validasi batas, deteksi sensor macet, dan *Hampel Filter* agar AI tidak belajar dari data sampah (*garbage in, garbage out*). |
| **Slide 4** | **Algoritma Agronomi (CSI)** | Menggunakan formula standar FAO EcoCrop dan Hukum Bottleneck Liebig: jika ada satu variabel tanah yang fatal, tanaman langsung dievaluasi ulang. |
| **Slide 5** | **Machine Learning (AI)** | Menggunakan ensemble *Random Forest* (100 pohon keputusan) + *TreeSHAP* untuk memberikan alasan transparan mengapa tanaman itu dipilih. |
| **Slide 6** | **Decision Strategy** | Menggabungkan $50\%$ kecocokan alam, $30\%$ proyeksi laba, dan $20\%$ kontrol risiko, dilengkapi pengaman *Confidence Gate*. |
| **Slide 7** | **Demo & Dampak** | Menampilkan UI dashboard interaktif yang menghemat pemupukan $10-15\%$ dan menekan risiko gagal panen petani. |

---

## 🎯 5. Jawaban Sakti untuk Tanya Jawab (Q&A)

* **Tanya: *"Kenapa tidak pakai Deep Learning (Jaringan Syaraf Tiruan)?"***
  * **Jawab:** *"Untuk data tabular/angka sensor berdimensi puluhan fitur, algoritma Ensemble Tree (Random Forest / LightGBM) terbukti secara benchmark ilmiah jauh lebih akurat, tidak overfit, cepat dieksekusi, dan memiliki nilai Explainability (SHAP) yang jelas untuk faktor keselamatan panen petani."*

* **Tanya: *"Bagaimana jika koneksi internet di kebun putus atau sensor rusak?"***
  * **Jawab:** *"Sistem memiliki arsitektur Medallion dan validasi data. Jika sensor mengirim nilai stuck atau data hilang $>30\%$, sistem mengaktifkan Confidence Gate berstatus `NEEDS_AGRONOMIST_REVIEW` sehingga tidak akan mengeluarkan rekomendasi sembrono."*

* **Tanya: *"Apakah rekomendasi pemupukannya bisa dipercaya?"***
  * **Jawab:** *"Bisa, karena menggunakan pendekatan Neraca Defisit Hara: sistem menghitung selisih antara nutrisi yang dibutuhkan tanaman dengan ketersediaan unsur N-P-K yang terbaca di tanah, jadi tidak ada over-fertilization."*
