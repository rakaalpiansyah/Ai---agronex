# Panduan Teknis AI Engineer: Sistem Rekomendasi Tanaman Berbasis IoT

*Dokumen alur kerja end-to-end: dari data sensor, pengolahan data, indeks penentu, algoritma, hingga strategi keputusan dan operasional (MLOps).*

## 1. Tujuan dan Ruang Lingkup

**Masalah bisnis:** Berdasarkan data IoT dari lahan (tanah, cuaca mikro, air), sistem merekomendasikan tanaman yang paling cocok ditanam, lalu menyimpulkan strategi budidaya (kapan tanam, berapa air, pupuk, risiko).

**Output sistem (3 lapis):**

1. **Prediksi**: tanaman apa yang paling cocok (ranking top-k + skor kecocokan).
2. **Estimasi**: potensi hasil panen (yield) dan risiko per tanaman.
3. **Strategi**: rekomendasi tindakan (jadwal tanam, irigasi, pemupukan, mitigasi risiko) beserta alasan yang bisa dijelaskan.

**Prinsip profesional:** mulai dari baseline sederhana yang bisa dijelaskan (rule-based berbasis standar agronomi), baru naik ke ML, dan selalu validasi dengan data lapangan serta masukan agronom.

## 2. Arsitektur End-to-End

| Lapisan | Fungsi | Contoh teknologi |
| --- | --- | --- |
| Edge / Device | Sensor, mikrokontroler, gateway | ESP32, LoRaWAN, Raspberry Pi |
| Ingestion | Menerima data real-time | MQTT (Mosquitto/EMQX), Kafka |
| Storage | Raw, clean, feature | S3/MinIO (raw), TimescaleDB/InfluxDB (time series), PostgreSQL + PostGIS (lokasi) |
| Processing | Cleaning, agregasi, feature | Python (pandas, polars), Spark/Flink bila skala besar, Airflow/Prefect |
| Feature Store | Fitur konsisten training dan serving | Feast, atau tabel fitur terversi |
| Modeling | Training, evaluasi, registry | scikit-learn, XGBoost/LightGBM, PyTorch, MLflow |
| Serving | API prediksi | FastAPI, Docker, Kubernetes |
| Strategy Engine | Rule + optimisasi + penjelasan | Python, OR-Tools, SHAP, LLM untuk narasi |
| Monitoring | Kualitas data, drift, performa | Grafana, Prometheus, Evidently |
| Aplikasi | Dashboard dan notifikasi | Web/mobile, WhatsApp/Telegram bot |

**Alur ringkas:**

`Sensor -> MQTT -> Validasi -> Raw storage -> Cleaning -> Agregasi -> Feature engineering -> Model -> Skor kecocokan -> Strategy engine -> Dashboard / alert`

## 3. Data yang Dibutuhkan

### 3.1 Data dari IoT (real-time)

| Parameter | Sensor | Frekuensi umum | Catatan |
| --- | --- | --- | --- |
| Kelembapan tanah (VWC %) | Capacitive soil moisture | 5-15 menit | Wajib kalibrasi per jenis tanah |
| Suhu tanah | DS18B20 | 15 menit | Pasang di beberapa kedalaman |
| pH tanah | Probe pH | 1-6 jam | Probe murah cepat drift, kalibrasi berkala |
| EC / salinitas | Sensor EC | 1-6 jam | Penting untuk daerah pesisir |
| N, P, K | Sensor NPK | 6-24 jam | Akurasi terbatas, validasi dengan uji lab |
| Suhu dan kelembapan udara | SHT31/BME280 | 5-15 menit | Dasar perhitungan VPD |
| Curah hujan | Tipping bucket | Event-based |  |
| Radiasi/intensitas cahaya | Pyranometer/lux | 5-15 menit |  |
| Angin | Anemometer | 5-15 menit | Untuk evapotranspirasi |

### 3.2 Data pendukung (non-IoT, sangat menentukan kualitas model)

- **Cuaca historis dan prakiraan**: BMKG, NASA POWER, ERA5, CHIRPS.
- **Tanah dan topografi**: SoilGrids, peta tanah lokal, DEM (elevasi, kemiringan).
- **Citra satelit**: Sentinel-2 / Landsat untuk NDVI, EVI, NDWI.
- **Basis pengetahuan tanaman**: FAO EcoCrop, standar kesesuaian lahan FAO, jurnal agronomi lokal.
- **Data historis panen**: jenis tanaman, tanggal tanam/panen, yield per hektare. Ini adalah **label** terpenting.
- **Data ekonomi**: harga komoditas, biaya input (benih, pupuk, tenaga kerja).

> **Catatan penting:** tanpa label historis (tanaman apa tumbuh baik di lokasi X dengan kondisi Y), model ML tidak bisa dilatih dengan benar. Jika belum ada, mulai dengan pendekatan rule-based (Bagian 6.1) sambil mengumpulkan data musim tanam.

## 4. Pipeline Ingestion

1. **Format payload standar (JSON):** `device_id`, `site_id`, `timestamp` (UTC, ISO 8601), `metric`, `value`, `unit`, `firmware_version`.
2. **Transport:** MQTT dengan TLS dan autentikasi per device. QoS 1 untuk data penting.
3. **Buffering:** Kafka atau queue agar tidak ada data hilang saat backend down.
4. **Penyimpanan berlapis (medallion):**
   - **Bronze**: data mentah apa adanya (immutable).
   - **Silver**: data tervalidasi dan dibersihkan.
   - **Gold**: fitur dan agregasi siap model.
5. **Orkestrasi:** Airflow/Prefect untuk job batch (agregasi harian, tarik data satelit dan cuaca).
6. **Offline buffering di edge:** gateway menyimpan data lokal saat koneksi terputus, lalu mengirim ulang (penting di lahan dengan sinyal lemah).

## 5. Pengolahan Data (Data Processing) Secara Rinci

### 5.1 Validasi dan Quality Check

| Pemeriksaan | Metode | Tindakan |
| --- | --- | --- |
| Schema | Pydantic / Great Expectations | Tolak atau karantina data invalid |
| Rentang fisik | Misal VWC 0-100%, pH 3-10, suhu udara -5 sampai 60 C | Tandai sebagai anomali |
| Duplikat | Kunci (device\_id, timestamp, metric) | Hapus |
| Timestamp tidak urut atau di masa depan | Cek dan koreksi zona waktu | Koreksi atau buang |
| Sensor stuck | Nilai konstan terlalu lama (rolling std mendekati 0) | Flag sensor rusak |
| Lonjakan tidak wajar | Rolling z-score atau Hampel filter | Flag lalu imputasi |
| Completeness | Persentase data hadir per jam/hari | Tolak agregasi jika di bawah ambang (misal 70%) |

### 5.2 Kalibrasi dan Koreksi

- Kalibrasi sensor kelembapan tanah per jenis tanah (kurva sensor vs metode gravimetri).
- Kompensasi suhu untuk pH dan EC (EC dinormalisasi ke 25 C).
- Validasi silang: bandingkan sensor dengan uji lab tanah minimal tiap musim.
- Catat **metadata kalibrasi** dan versi sensor sebagai fitur kualitas.

### 5.3 Missing Value dan Outlier

- Gap pendek (kurang dari 1-2 jam): interpolasi linear atau time-based.
- Gap menengah: imputasi berbasis model (misal KNN, atau regresi dari sensor tetangga/cuaca).
- Gap panjang: **jangan diisi paksa**; tandai sebagai missing dan biarkan model/aturan menangani (misal fitur `is_missing`).
- Outlier: jangan langsung dibuang. Bedakan antara kesalahan sensor dan kejadian nyata (hujan deras memang menaikkan kelembapan drastis).

### 5.4 Resampling dan Agregasi

Model kecocokan tanaman bekerja pada skala **musim/periode**, bukan per menit. Agregasi bertingkat:

- Per jam, harian: mean, min, max, std, jumlah (hujan).
- Per minggu dan per fase: rolling window 7, 14, 30 hari.
- Per musim tanam: statistik ringkasan (rata-rata, persentil 10/90, jumlah hari stres).

### 5.5 Feature Engineering

- **Statistik:** mean, median, std, min, max, persentil, tren (slope regresi).
- **Temporal:** hari dalam tahun, musim (hujan/kemarau), lag, rolling.
- **Domain agronomi:** indeks pada Bagian 6.
- **Spasial:** elevasi, kemiringan, jarak ke sumber air, fitur satelit (NDVI mean dan tren).
- **Encoding:** one-hot atau target encoding untuk jenis tanah; label encoding untuk target tanaman.
- **Scaling:** StandardScaler/RobustScaler untuk model berbasis jarak dan jaringan saraf (tree-based tidak wajib).

### 5.6 Pencegahan Data Leakage

- Split data **berdasarkan lokasi dan musim**, bukan acak per baris. Baris dari lahan yang sama tidak boleh ada di train dan test sekaligus.
- Hitung scaler, imputer, dan encoder hanya dari data train.
- Jangan memakai fitur yang baru diketahui setelah panen untuk memprediksi sebelum tanam.

## 6. Indeks Penentu dan Algoritma Kesesuaian

### 6.1 Indeks Agronomi (Fitur Penentu)

| Indeks | Rumus / Definisi | Fungsi |
| --- | --- | --- |
| **VPD** (Vapor Pressure Deficit) | VPD = es x (1 - RH/100); es = 0.6108 x exp(17.27 x T / (T + 237.3)) kPa | Stres transpirasi, risiko penyakit jamur |
| **GDD** (Growing Degree Days) | GDD = sum dari max(0, (Tmax + Tmin)/2 - Tbase) | Prediksi fase tumbuh, kecocokan panas |
| **Water Balance** | WB = Curah hujan + Irigasi - ETc | Kekurangan atau kelebihan air |
| **ETc** | ETc = Kc x ET0 (ET0 via FAO Penman-Monteith) | Kebutuhan air tanaman |
| **Aridity Index** | AI = P / ET0 | Klasifikasi kekeringan wilayah |
| **Soil Moisture Stress Days** | Jumlah hari VWC di bawah ambang kritis | Risiko kekeringan |
| **Waterlogging Days** | Jumlah hari VWC di atas kapasitas lapang | Risiko busuk akar |
| **Heat Stress Days** | Jumlah hari suhu melebihi ambang toleransi | Risiko gagal berbunga/berbuah |
| **NDVI** | (NIR - Red) / (NIR + Red) | Vigor vegetasi, validasi lapangan |
| **Salinity Stress** | EC dibanding ambang toleransi tanaman | Kesesuaian di lahan pesisir |
| **Nutrient Sufficiency** | Rasio N, P, K terhadap kebutuhan tanaman | Perlu pupuk atau tidak |

### 6.2 Crop Suitability Index (CSI): Baseline Berbasis Aturan

Untuk setiap tanaman *c*, setiap faktor *i* (suhu, pH, curah hujan, kelembapan tanah, NPK, EC, kemiringan) diberi skor kesesuaian **S\_i dalam rentang 0-1** memakai fungsi trapesium dari rentang optimal tanaman (sumber: FAO EcoCrop):

- S\_i = 1 jika nilai berada di rentang optimal.
- S\_i turun linear menuju 0 antara batas optimal dan batas absolut (minimum/maksimum yang masih ditoleransi).
- S\_i = 0 jika di luar batas absolut.

Gabungkan skor dengan dua pendekatan, lalu bandingkan:

1. **Hukum minimum (Liebig/FAO):** CSI = min(S\_1, S\_2, ..., S\_n). Konservatif; satu faktor buruk menggagalkan tanaman.
2. **Rata-rata geometrik berbobot:** CSI = produk dari (S\_i pangkat w\_i), dengan jumlah bobot w\_i = 1. Bobot ditentukan lewat AHP atau konsultasi agronom.

**Kategori hasil (mengacu FAO):**

| CSI | Kelas | Arti |
| --- | --- | --- |
| 0.80 - 1.00 | S1 | Sangat sesuai |
| 0.60 - 0.79 | S2 | Cukup sesuai |
| 0.40 - 0.59 | S3 | Sesuai marginal |
| di bawah 0.40 | N | Tidak sesuai |

Baseline ini bernilai tinggi: bisa langsung dipakai saat data historis belum ada, dan menjadi pembanding wajib bagi model ML.

### 6.3 Model Machine Learning

**Formulasi masalah:**

- **Klasifikasi multi-class:** input fitur lahan, output tanaman paling cocok (dengan probabilitas).
- **Ranking:** urutkan tanaman berdasarkan skor; evaluasi dengan top-k.
- **Regresi yield:** prediksi hasil panen (ton/ha) per kandidat tanaman, lalu urutkan berdasarkan yield atau keuntungan.

| Tahap | Algoritma | Alasan |
| --- | --- | --- |
| Baseline | Rule-based CSI, Logistic Regression | Pembanding dan interpretabilitas |
| **Utama (data tabular)** | **Random Forest, XGBoost, LightGBM, CatBoost** | Terbaik untuk data tabular, tahan outlier, ada feature importance |
| Prediksi deret waktu | LSTM, GRU, Temporal Fusion Transformer, atau Prophet/ARIMA | Forecast kelembapan, suhu, curah hujan ke depan |
| Data sedikit | Gaussian Process, model Bayesian | Memberi ketidakpastian |
| Hibrida | Fitur CSI dimasukkan sebagai input ML | Menggabungkan pengetahuan domain dan data |

**Rekomendasi praktis:** mulai dari LightGBM/XGBoost dengan fitur indeks agronomi; tambah model deret waktu hanya jika ada kebutuhan forecasting.

### 6.4 Evaluasi Model

| Metrik | Kegunaan |
| --- | --- |
| Top-1 / Top-3 accuracy | Apakah tanaman terbaik ada di 3 rekomendasi teratas |
| F1 macro, precision/recall per kelas | Penting jika kelas tanaman tidak seimbang |
| Confusion matrix | Melihat tanaman yang sering tertukar |
| Calibration (Brier score, reliability curve) | Apakah probabilitas 80% benar-benar benar 80% |
| MAE, RMSE, R2 | Untuk regresi yield |
| Agreement dengan agronom | Validasi ahli (human-in-the-loop) |

**Validasi:** gunakan **GroupKFold / spatial cross-validation** (kelompokkan per lokasi) dan **time-based split** (latih musim lama, uji musim terbaru). Cross-validation acak akan menghasilkan angka yang terlalu optimistis.

**Penanganan ketidakseimbangan kelas:** class weights, SMOTE (hati-hati, hanya pada data train), atau pengumpulan data tambahan.

### 6.5 Explainability dan Ketidakpastian

- **SHAP / feature importance:** jelaskan mengapa padi direkomendasikan (misal "pH 6.2 optimal, kelembapan stabil, tidak ada hari stres panas").
- **Prediction interval** (quantile regression atau conformal prediction) untuk yield.
- **Confidence gate:** jika probabilitas tertinggi di bawah ambang atau data sensor tidak lengkap, sistem menyatakan "tidak cukup yakin" dan meminta data tambahan atau uji lab.

## 7. Strategy Engine (Dari Prediksi ke Kesimpulan Strategi)

Model hanya menjawab "tanaman apa yang cocok". Strategi menjawab "apa yang sebaiknya dilakukan". Susun sebagai lapisan keputusan terpisah:

### 7.1 Komponen Strategi

1. **Ranking multi-kriteria.** Skor akhir = bobot kecocokan agronomi + bobot ekspektasi keuntungan - bobot risiko. Contoh: Skor = 0.5 x CSI/prob. model + 0.3 x profit ternormalisasi - 0.2 x risiko.
2. **Ekspektasi keuntungan.** Profit = (yield x harga) - biaya input. Gunakan prakiraan harga dan skenario (pesimis/normal/optimis).
3. **Penilaian risiko.** Risiko kekeringan, banjir, hama/penyakit (berbasis VPD dan kelembapan), fluktuasi harga, dan ketidakpastian model.
4. **Kalender tanam.** Pilih jendela tanam dengan mencocokkan GDD, prakiraan hujan, dan fase kritis tanaman.
5. **Irigasi.** Jadwal berbasis water balance dan ambang kelembapan tanah, bukan jadwal tetap.
6. **Pemupukan.** Selisih antara kebutuhan tanaman dan ketersediaan N, P, K dan pH; sertakan koreksi (kapur, bahan organik).
7. **Rotasi dan diversifikasi.** Hindari monokultur berulang, pertimbangkan tanaman penambat nitrogen.
8. **Optimisasi (opsional).** Untuk banyak petak dan sumber daya terbatas (air, modal), gunakan linear/integer programming (OR-Tools).

### 7.2 Contoh Aturan Keputusan

- Jika CSI tanaman utama kurang dari 0.4 pada faktor pH: rekomendasikan pengapuran dulu atau pilih alternatif toleran asam.
- Jika hari stres kekeringan diprediksi lebih dari N hari pada fase kritis: sarankan irigasi tambahan atau geser tanggal tanam.
- Jika EC melebihi ambang toleransi: rekomendasikan tanaman toleran salin dan pencucian lahan.

### 7.3 Narasi Kesimpulan

Keluaran terstruktur (JSON) dari mesin strategi dapat diubah menjadi kalimat natural dengan LLM. **Aturan:** LLM hanya menarasikan hasil yang sudah dihitung (angka, skor, aturan); jangan membiarkan LLM mengarang angka atau rekomendasi agronomi sendiri. Sertakan batas keyakinan dalam narasi.

## 8. MLOps dan Operasional

| Aspek | Praktik |
| --- | --- |
| Versioning | Git (kode), DVC (data), MLflow (eksperimen dan model registry) |
| CI/CD | Test otomatis data dan model, deploy via Docker/Kubernetes |
| Serving | FastAPI untuk online inference; batch inference harian untuk rekomendasi musiman |
| Monitoring data | Drift fitur (PSI, KS test), sensor mati, kualitas data (Evidently, Grafana) |
| Monitoring model | Akurasi terhadap hasil panen aktual, calibration drift |
| Retraining | Terjadwal per musim dan dipicu drift; champion/challenger sebelum promosi |
| Keamanan | TLS, secret management, autentikasi device, kontrol akses data petani |
| Audit | Catat input, versi model, dan output setiap rekomendasi |

**Feedback loop:** setelah panen, catat hasil aktual dan bandingkan dengan prediksi. Data ini menjadi label berkualitas tinggi untuk iterasi berikutnya.

## 9. Stack Teknologi yang Disarankan

- **Bahasa:** Python (pandas/polars, scikit-learn, XGBoost/LightGBM, PyTorch, SHAP).
- **Data:** TimescaleDB atau InfluxDB, PostgreSQL + PostGIS, S3/MinIO, Parquet.
- **Stream dan orkestrasi:** MQTT, Kafka (jika skala besar), Airflow/Prefect.
- **Geospasial:** GeoPandas, rasterio, Google Earth Engine atau Sentinel Hub.
- **MLOps:** MLflow, DVC, Docker, Kubernetes, Evidently, Grafana.
- **API dan UI:** FastAPI, React/Next.js atau Streamlit untuk prototipe.

## 10. Roadmap Implementasi

| Fase | Durasi indikatif | Hasil |
| --- | --- | --- |
| 1. Discovery | 2-3 minggu | Definisi masalah, pemetaan komoditas target, daftar sensor dan sumber data, wawancara agronom |
| 2. Data foundation | 4-6 minggu | Pipeline ingestion, storage bronze/silver/gold, dashboard kualitas data |
| 3. Baseline | 2-4 minggu | Basis pengetahuan tanaman, perhitungan indeks, CSI rule-based, demo awal |
| 4. Modeling | 4-8 minggu | Dataset berlabel, model ML, validasi spasial dan temporal, explainability |
| 5. Strategy engine | 3-5 minggu | Ranking multi-kriteria, jadwal irigasi/pupuk/tanam, narasi |
| 6. Productionization | 3-4 minggu | API, monitoring, CI/CD, retraining otomatis |
| 7. Pilot lapangan | 1 musim tanam | Uji di beberapa lahan, kumpulkan feedback dan hasil panen |

## 11. Risiko dan Kesalahan Umum

- **Label tidak ada atau bias:** hanya merekomendasikan tanaman yang sudah biasa ditanam di data historis.
- **Sensor murah tidak akurat:** terutama NPK dan pH; selalu validasi dengan uji lab.
- **Leakage dan validasi acak:** menghasilkan akurasi palsu yang runtuh di lahan baru.
- **Data satu musim saja:** model tidak mengenal variasi iklim antar tahun.
- **Mengabaikan faktor non-teknis:** harga pasar, ketersediaan benih, tenaga kerja, preferensi petani.
- **Overengineering di awal:** deep learning dan streaming kompleks sebelum baseline dan data benar.
- **Menghilangkan manusia dari proses:** rekomendasi berisiko tinggi sebaiknya ditinjau agronom.

## 12. Checklist Singkat

1. Tentukan komoditas target dan wilayah.
2. Pasang dan kalibrasi sensor; pastikan data historis dan data satelit tersedia.
3. Bangun pipeline ingestion dan validasi kualitas data.
4. Hitung indeks agronomi (VPD, GDD, water balance, stress days).
5. Bangun baseline CSI berbasis FAO EcoCrop.
6. Kumpulkan label historis, lalu latih LightGBM/XGBoost dengan split berbasis lokasi dan waktu.
7. Evaluasi (top-k, F1 macro, calibration) dan jelaskan dengan SHAP.
8. Bangun strategy engine (profit, risiko, kalender, irigasi, pupuk).
9. Deploy, monitor drift, dan retrain tiap musim.
10. Validasi dengan agronom dan hasil panen aktual.

## 13. Proses Bisnis Sistem Rekomendasi Tanaman

Bagian ini menjelaskan sistem dari sudut pandang **proses bisnis**: siapa yang terlibat, apa yang dikerjakan di setiap tahap, apa keluarannya, dan bagaimana keputusan akhir (nama tanaman beserta penjelasannya) sampai ke pengguna.

### 13.1 Pernyataan Nilai Bisnis

**Sistem menjawab tiga pertanyaan pengguna (petani, koperasi, atau perusahaan agribisnis):**

1. *Tanaman apa yang paling cocok ditanam di lahan ini sekarang?*
2. *Mengapa tanaman itu cocok, dan apa risikonya?*
3. *Apa yang harus saya lakukan agar hasilnya optimal?*

**Manfaat terukur:** keputusan tanam berbasis data (bukan kebiasaan atau tebakan), pengurangan gagal panen, efisiensi air dan pupuk, serta peningkatan pendapatan per hektare.

### 13.2 Aktor dan Peran

| Aktor | Peran dalam proses |
| --- | --- |
| Petani / pemilik lahan | Pengguna akhir; menerima rekomendasi dan memberi umpan balik hasil panen |
| Penyuluh / agronom | Memvalidasi rekomendasi berisiko tinggi, menjaga basis pengetahuan tanaman |
| Teknisi lapangan | Memasang, merawat, dan mengkalibrasi sensor IoT |
| AI / Data Engineer | Membangun pipeline, model, strategy engine, dan monitoring |
| Product / Business Owner | Menentukan komoditas target, KPI, dan model layanan |
| Sistem (otomatis) | Ingestion, scoring, notifikasi, dan pemantauan kualitas data |

### 13.3 Alur Proses Bisnis End-to-End

| No | Tahap | Aktivitas utama | Input | Output | Penanggung jawab |
| --- | --- | --- | --- | --- | --- |
| 1 | Registrasi lahan | Daftarkan lahan, koordinat (polygon), luas, riwayat tanam, sumber air | Data petani dan lahan | Profil lahan (site\_id) | Petani, teknisi |
| 2 | Instalasi sensor | Pasang dan kalibrasi sensor tanah dan cuaca mikro | Perangkat IoT | Sensor aktif dan terkalibrasi | Teknisi |
| 3 | Pengumpulan data | Sensor mengirim data via MQTT; tarik data cuaca dan satelit | Data sensor, cuaca, citra | Data mentah (bronze) | Sistem |
| 4 | Validasi dan pembersihan | Cek kualitas, deteksi anomali, imputasi | Data mentah | Data bersih (silver) | Sistem |
| 5 | Pembentukan fitur | Agregasi periode, hitung indeks (VPD, GDD, water balance, stress days) | Data bersih | Fitur lahan (gold) | Sistem |
| 6 | Penilaian kecocokan | Hitung CSI per tanaman dan jalankan model ML | Fitur lahan, basis pengetahuan tanaman | Skor kecocokan per kandidat tanaman | Sistem (model) |
| 7 | Estimasi hasil dan ekonomi | Prediksi yield, hitung profit dan risiko | Skor, harga pasar, biaya input | Ranking tanaman multi-kriteria | Sistem (strategy engine) |
| 8 | Quality gate | Cek tingkat keyakinan dan kelengkapan data | Ranking dan metrik keyakinan | Lolos otomatis, atau diteruskan ke agronom | Sistem, agronom |
| 9 | Penyusunan rekomendasi | Susun nama tanaman, alasan, strategi, dan peringatan | Hasil tahap 7-8 | Laporan rekomendasi | Sistem, agronom |
| 10 | Penyampaian | Tampilkan di dashboard/aplikasi dan kirim notifikasi | Laporan rekomendasi | Rekomendasi diterima pengguna | Sistem |
| 11 | Eksekusi di lapangan | Petani menanam dan menjalankan jadwal irigasi/pupuk | Rekomendasi | Aktivitas budidaya tercatat | Petani |
| 12 | Monitoring musim tanam | Pantau sensor dan NDVI; beri alert dini (kekeringan, hama, stres panas) | Data sensor berjalan | Alert dan penyesuaian strategi | Sistem |
| 13 | Panen dan feedback | Catat hasil panen aktual dan kendala | Data panen | Label baru untuk model | Petani, penyuluh |
| 14 | Evaluasi dan perbaikan | Bandingkan prediksi dengan hasil aktual, retrain model | Data panen, log prediksi | Model dan aturan yang diperbarui | AI Engineer |

**Alur ringkas:** `Registrasi lahan -> Sensor -> Data -> Fitur -> Skor kecocokan -> Ranking dan strategi -> Quality gate -> Rekomendasi -> Eksekusi -> Panen -> Feedback -> Retraining`

### 13.4 Bentuk Keluaran: Nama Tanaman dan Penjelasannya

Setiap rekomendasi harus berisi komponen berikut agar profesional dan dapat dipertanggungjawabkan:

| Komponen | Isi |
| --- | --- |
| Tanaman rekomendasi utama | Nama tanaman (dan varietas bila ada), peringkat 1 dari top-3 |
| Skor kecocokan | CSI atau probabilitas model, kelas S1/S2/S3/N |
| Alasan (explainability) | Faktor pendukung dan faktor penghambat, berbasis SHAP dan indeks agronomi |
| Estimasi hasil | Yield dengan rentang (misal 4.5-6.0 ton/ha) |
| Estimasi ekonomi | Profit per hektare pada skenario pesimis/normal/optimis |
| Risiko | Kekeringan, genangan, hama/penyakit, harga, ketidakpastian model |
| Strategi budidaya | Waktu tanam, irigasi, pemupukan, koreksi tanah, rotasi |
| Alternatif | Tanaman peringkat 2 dan 3 beserta alasan singkat |
| Tingkat keyakinan | Tinggi/sedang/rendah dan data yang masih kurang |
| Catatan validasi | Apakah sudah ditinjau agronom, kapan, dan versi model yang dipakai |

**Contoh keluaran (ilustrasi):**

> **Rekomendasi untuk Lahan A-07 (musim tanam Okt-Jan):** Jagung hibrida, skor kecocokan 0.82 (S1), keyakinan tinggi.
>
> **Alasan:** pH tanah 6.3 dan suhu rata-rata 27 C berada di rentang optimal; kelembapan tanah stabil di atas 55% selama 30 hari terakhir; tidak ada hari stres panas. Faktor penghambat: kadar fosfor rendah.
>
> **Estimasi:** hasil 6.2-7.4 ton/ha; profit normal sekitar 12-15 juta rupiah/ha.
>
> **Strategi:** tanam minggu ke-2 Oktober mengikuti prakiraan hujan; irigasi tambahan jika kelembapan tanah di bawah 40% saat fase pembungaan; tambahkan pupuk P sebelum tanam.
>
> **Alternatif:** (2) Kacang tanah, skor 0.74; (3) Kedelai, skor 0.69.

*Angka pada contoh bersifat ilustratif dan akan ditentukan oleh data serta basis pengetahuan tanaman yang sebenarnya.*

### 13.5 Aturan Bisnis (Business Rules)

1. **Confidence gate:** rekomendasi dengan keyakinan rendah atau kelengkapan data di bawah ambang (misal 70%) tidak dikirim otomatis, tetapi diteruskan ke agronom atau diminta uji tanah lab.
2. **Human-in-the-loop:** rekomendasi berisiko tinggi (investasi besar, tanaman tahunan, lahan luas) wajib ditinjau agronom.
3. **Batas tanggung jawab:** rekomendasi adalah alat bantu keputusan, bukan jaminan hasil; sertakan pernyataan ini di laporan.
4. **Hanya tanaman dalam katalog:** sistem hanya merekomendasikan komoditas yang parameternya tersedia dan tervalidasi di basis pengetahuan.
5. **Kualitas sensor:** data dari sensor yang gagal kalibrasi atau stuck tidak boleh dipakai untuk rekomendasi.
6. **Audit:** setiap rekomendasi menyimpan input, versi model, versi basis pengetahuan, dan waktu pembuatan.
7. **Privasi data:** data lahan dan hasil panen milik petani; akses dan berbagi data mengikuti persetujuan (consent).
8. **Pembaruan rekomendasi:** rekomendasi dihitung ulang saat ada perubahan signifikan (hujan ekstrem, perubahan harga, data sensor baru) atau tiap awal musim.

### 13.6 KPI dan Indikator Keberhasilan

| Kategori | KPI | Contoh target |
| --- | --- | --- |
| Model | Top-3 accuracy, F1 macro, calibration | Top-3 di atas 85% pada data uji spasial |
| Data | Uptime sensor, kelengkapan data | Di atas 90% data valid per hari |
| Bisnis | Kenaikan yield per hektare, penurunan gagal panen | Peningkatan yield 10-20% dibanding praktik sebelumnya |
| Efisiensi | Penghematan air dan pupuk | Penurunan penggunaan input 10-15% |
| Adopsi | Persentase rekomendasi yang dijalankan petani | Di atas 60% |
| Kepercayaan | Tingkat kesepakatan agronom, kepuasan pengguna | Kesepakatan di atas 80% |
| Operasional | Latensi rekomendasi, waktu penanganan alert | Rekomendasi di bawah 5 menit; alert di bawah 1 jam |

*Target di atas hanya contoh awal; tetapkan target nyata setelah pilot lapangan.*

### 13.7 Model Layanan dan Monetisasi (Opsional)

- **Langganan per lahan/hektare** (rekomendasi musiman dan monitoring).
- **Paket enterprise** untuk koperasi, perkebunan, atau agribisnis (dashboard multi-lahan, API).
- **Bundling hardware dan layanan** (sensor, pemasangan, dan langganan analitik).
- **Kemitraan** dengan penyedia benih, pupuk, asuransi pertanian, atau offtaker (dengan persetujuan data petani).

### 13.8 Tata Kelola Perubahan

- Basis pengetahuan tanaman dikelola agronom dengan versi dan riwayat perubahan.
- Perubahan model dan aturan melalui proses uji, persetujuan, lalu rilis bertahap (champion/challenger).
- Insiden (rekomendasi salah, sensor error massal) dicatat, dianalisis akar masalahnya, dan menjadi bahan perbaikan.
