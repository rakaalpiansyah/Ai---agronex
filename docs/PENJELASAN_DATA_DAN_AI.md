# Panduan Lengkap: Sumber Data, Arsitektur AI, dan Algoritma Sistem Rekomendasi Tanaman Berbasis IoT

Dokumen ini disusun sebagai panduan teknis dan materi presentasi komprehensif mengenai latar belakang ilmiah, sumber data, arsitektur kecerdasan buatan (AI), serta formulasi algoritma yang diimplementasikan dalam sistem Agrosense IoT.

---

## 1. Ringkasan Eksekutif

Dalam pertanian modern, kegagalan panen sering terjadi akibat:
1. Pemilihan komoditas yang hanya didasarkan pada intuisi subjektif atau tren sesaat tanpa mempertimbangkan kesesuaian bio-fisik lahan.
2. Anomali agroklimat ekstrem (kekeringan, genangan, tekanan defisit uap air).
3. Degradasi kimia tanah (kemasaman tanah, defisit hara N-P-K, salinitas tinggi).
4. Asimetri informasi ekonomi antara potensi hasil panen dengan biaya operasional riil.

Sistem Agrosense memecahkan masalah ini dengan pendekatan **Hybrid AI & Precision Agronomy**:
- Menggabungkan **Machine Learning Tabular** (prediksi multi-variabel berbasis data historis),
- **Model Bio-Fisik Baku FAO** (aturan ilmiah tak terbantahkan yang menjaga batas biologi tanaman),
- Serta **Large Language Model (LLM)** yang dibatasi secara ketat (*grounded fact-bounding*) untuk menyajikan rekomendasi konsultatif tanpa halusinasi.

---

## 2. Dari Mana Sumber Datanya? (Data Provenance & Scientific Basis)

Data yang digunakan oleh sistem terbagi menjadi lima pilar utama yang saling terhubung:

### A. Basis Pengetahuan Ekologi Tanaman: FAO EcoCrop Database
- **Penerbit**: Food and Agriculture Organization of the United Nations (FAO).
- **Peran**: Menentukan batas adaptasi ekologis tanaman di seluruh dunia.
- **Parameter yang Diambil**:
  - Batas Suhu Udara: Minimum mutlak, minimum optimal, maksimum optimal, dan maksimum mutlak.
  - Batas Keasaman Tanah (pH): Rentang toleransi akar terhadap konsentrasi ion hidrogen.
  - Kebutuhan Air Musiman: Curah hujan minimal dan optimal per siklus tanam (mm).
  - Ambang Batas Salinitas ($EC_e$): Daya hantar listrik maksimal dalam deciSiemens per meter (dS/m) sebelum tanaman mengalami stres osmotik.
- **Validitas**: Standar internasional yang telah digunakan selama puluhan tahun oleh para peneliti agronomi dan perencana tata ruang pertanian (*Agro-Ecological Zoning*).

### B. Hidrologi & Kebutuhan Air: FAO Irrigation and Drainage Paper No. 56 (FAO-56)
- **Penerbit**: FAO Water Resources, Development and Management Service.
- **Peran**: Dasar perhitungan evapotranspirasi standar dan kebutuhan irigasi tanaman.
- **Parameter yang Diambil**:
  - Koefisien Tanaman ($K_c$) pada 3 fase pertumbuhan: fase awal ($K_{c,\text{ini}}$), fase vegetatif-reproduktif aktif ($K_{c,\text{mid}}$), dan fase pematangan akhir menjelang panen ($K_{c,\text{late}}$).
- **Validitas**: Metode acuan emas (*gold standard*) hidrologi pertanian internasional untuk menghitung kehilangan air akibat transpirasi daun dan evaporasi permukaan tanah.

### C. Kebutuhan Hara & Rekomendasi Pemupukan: Balitbangtan / Kementan RI
- **Penerbit**: Badan Penelitian dan Pengembangan Pertanian (sekarang BRIN Pertanian) bersama Kementerian Pertanian Republik Indonesia.
- **Peran**: Menyesuaikan kebutuhan nutrisi spesifik komoditas di wilayah tropis Indonesia.
- **Parameter yang Diambil**:
  - Kebutuhan hara dasar per hektar: Nitrogen (N), Fosfat (P), dan Kalium (K).
  - Satuan Panas Kumulatif (*Growing Degree Days* / GDD) dengan suhu dasar biologis tropis ($T_{\text{base}}$).
  - Dosis pengapuran tanah masam: Kebutuhan kalsium karbonat / dolomit ($CaCO_3 / MgCO_3$) per 0.1 kenaikan pH tanah.

### D. Data Usahatani & Harga Pasar Riil: BPS & Pasar Komoditas Induk
- **Penerbit**: Badan Pusat Statistik (BPS) dan Pusat Informasi Harga Pangan Strategis (PIHPS).
- **Peran**: Dasar perhitungan proyeksi kelayakan ekonomi dalam mata uang Rupiah (IDR).
- **Parameter yang Diambil**:
  - Harga jual tingkat produsen/petani per ton dalam 3 skenario: pesimistis (harga anjlok saat panen raya), normal (harga acuan rata-rata), dan optimistis (harga puncak musim paceklik).
  - Biaya input produksi per hektar: Pembelian benih unggul bersertifikat, pupuk dasar dan susulan, pestisida/fungisida, sewa alat mesin pertanian, serta upah tenaga kerja olah tanah hingga panen.

### E. Telemetri Sensor Lapangan IoT & Kalibrasi Fisik
- **Hardware Sensor**:
  - Sensor Tanah Multi-Parameter (RS485 Modbus): Mengukur kadar air volumetrik (VWC %), konduktivitas listrik (EC dS/m), pH tanah, dan suhu tanah.
  - Stasiun Cuaca Mini (*Automatic Weather Station*): Termometer udara berpelindung radiasi, higrometer RH, pyranometer radiasi surya, anemometer kecepatan angin, dan penakar hujan *tipping bucket*.
- **Kalibrasi Matematis**:
  - Kalibrasi kurva tekstur tanah: Menyesuaikan pembacaan dielektrik sensor terhadap tipe tanah lempung (*clay*), geluh (*loam*), atau tanah pasir (*sandy loam*).
  - Kompensasi suhu probe EC: Normalisasi pembacaan konduktivitas ke suhu acuan 25 °C menggunakan koefisien standar FAO ($\alpha = 0.0191 / ^\circ\text{C}$).

---

## 3. Kecerdasan Buatan (AI) Apa yang Digunakan?

Sistem ini tidak hanya mengandalkan satu model, melainkan mengadopsi arsitektur **Hybrid AI** yang terdiri atas tiga lapis kecerdasan:

```
[ Sensor IoT Lahan ] 
         │
         ▼
[ Ingesti & Validasi Fisik (Hampel Filter + Stuck Detector) ]
         │
         ▼
[ Pipeline Medallion: Bronze -> Silver -> Gold Features ]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│                   HYBRID AI ENGINE                     │
│                                                        │
│  1. Machine Learning Tabular (Random Forest)           │
│     - Model Klasifikasi Kesesuaian Komoditas           │
│     - Model Regresi Estimasi Hasil Panen (ton/ha)      │
│                                                        │
│  2. Explainable AI (TreeSHAP)                          │
│     - Ekstraksi Nilai Kontribusi Fitur Lapangan        │
│     - Identifikasi Faktor Pembatas & Pendukung Lahan   │
│                                                        │
│  3. Model Agronomi Bio-Fisik (FAO EcoCrop & CSI)       │
│     - Fuzzy Trapezoid Membership & Hukum Liebig        │
│     - Penjaga Integritas Biologis (Biological Guard)   │
│                                                        │
│  4. Mesin Strategi Keputusan Multi-Kriteria (MCDA)    │
│     - Optimasi: 0.50 CSI + 0.30 Profit - 0.20 Risiko   │
│                                                        │
│  5. Large Language Model (Gemini AI Grounded)          │
│     - Sintesis Narasi Konsultatif Bebas Halusinasi     │
│     - Fallback Otomatis ke Engine Deterministik        │
└────────────────────────────────────────────────────────┘
         │
         ▼
[ Dashboard Frontend Interaktif & API Preskripsi ]
```

### A. Machine Learning Tabular: Random Forest (Ensemble Learning)
- **Alasan Pemilihan**:
  Data telemetri lingkungan pertanian bersifat tabular, non-linear, dan memiliki interaksi kompleks antar variabel (misal: suhu tinggi bersamaan dengan kelembapan rendah memicu defisit air yang jauh lebih parah daripada jika kelembapan tinggi). Random Forest terbukti paling tangguh (*robust*) terhadap noise sensor dan tidak rentan terhadap pencilan (*outliers*).
- **Dua Model yang Dilatih**:
  1. **Random Forest Classifier**: Memprediksi peluang kesesuaian relatif untuk ke-17 komoditas terdaftar.
  2. **Random Forest Yield Regressor**: Memprediksi potensi hasil panen aktual (ton/ha) berdasarkan kombinasi iklim dan profil kesuburan tanah dengan akurasi $R^2 \approx 0.842$.

### B. Validasi Spasial: GroupKFold Cross-Validation
- **Alasan Pemilihan**:
  Dalam data pertanian, pengukuran sensor dari lahan yang sama pada hari yang berbeda memiliki korelasi spasial yang sangat kuat. Jika menggunakan partisi data acak biasa (*random train-test split*), model akan mengalami kebocoran data spasial (*spatial data leakage*), di mana model tampak memiliki akurasi 99% di laboratorium namun gagal total saat dipasang di lahan baru.
- **Implementasi**:
  Partisi data pelatihan dilakukan berdasarkan `site_id` (petak lahan). Data dari petak uji tidak pernah dilihat oleh model selama proses pelatihan, menjamin kemampuan generalisasi model saat diterapkan ke lahan petani mana pun.

### C. Explainable AI: TreeSHAP (Shapley Additive Explanations)
- **Alasan Pemilihan**:
  Sistem AI untuk pertanian tidak boleh menjadi kotak hitam (*black box*). Petani dan agronom lapangan berhak mengetahui **mengapa** tanaman tertentu direkomendasikan dan tanaman lain tidak disarankan.
- **Implementasi**:
  Algoritma TreeSHAP menghitung nilai atribusi Shapley untuk setiap fitur telemetri. Fitur dengan nilai SHAP positif dikategorikan sebagai **Faktor Pendukung** (misal: ketersediaan nitrogen melimpah, pH ideal), sedangkan fitur dengan nilai SHAP negatif diklasifikasikan sebagai **Faktor Pembatas** (misal: suhu malam terlalu dingin, salinitas mendekati batas bahaya).

### D. Large Language Model (LLM): Google Gemini dengan Grounded Fact-Bounding
- **Alasan Pemilihan**:
  Petani dan penyuluh lapangan membutuhkan penjelasan dalam bahasa manusia yang ramah, santun, dan mudah dipahami, bukan sekadar tabel matriks probabilitas.
- **Pencegahan Halusinasi (Anti-Hallucination Guard)**:
  LLM tidak diizinkan menebak angka atau membuat rekomendasi sendiri. Sistem menggunakan teknik *Strict Fact-Bounding*: seluruh angka skor kesesuaian, estimasi panen, proyeksi laba, dosis pupuk, dan risiko agroklimat dihitung terlebih dahulu oleh mesin matematika agronomi. LLM hanya menerima data matang tersebut untuk disintesis menjadi narasi konsultatif Bahasa Indonesia.
- **Zero-Downtime Offline Fallback**:
  Jika perangkat berada di pedalaman tanpa koneksi internet atau kuota API habis, sistem secara otomatis beralih ke mesin narasi deterministik berbasis aturan ilmiah tanpa jeda atau kegagalan sistem.

---

## 4. Algoritma-Algoritma yang Diterapkan (Mathematical Formulations)

Berikut adalah rincian matematis seluruh algoritma yang bekerja di dalam sistem:

### 1. Deteksi Lonjakan Anomali Sensor: Hampel Filter (Median Absolute Deviation)
Mendeteksi lonjakan data instan (*spike*) akibat gangguan listrik atau induksi elektromagnetik pada probe sensor.

$$\text{Median Window} = \tilde{x} = \text{median}(x_{i-k}, \dots, x_{i+k})$$

$$\text{MAD} = 1.4826 \times \text{median}(|x_j - \tilde{x}|)$$

Jika $|x_i - \tilde{x}| > 3 \times \text{MAD}$, maka data $x_i$ dinyatakan sebagai anomali (*outlier*) dan digantikan oleh nilai median jendela.

### 2. Deteksi Sensor Macet (Stuck Sensor Detector)
Mendeteksi sensor yang rusak atau membeku dengan menghitung deviasi standar bergerak (*rolling standard deviation*):

$$\sigma_{\text{window}} = \sqrt{\frac{1}{N-1} \sum_{j=1}^{N} (x_j - \bar{x})^2}$$

Jika $\sigma_{\text{window}} < 0.001$ selama periode observasi lebih dari 12 jam, sensor ditandai sebagai `STUCK_SENSOR` dan memicu peringatan perawatan hardware.

### 3. Vapor Pressure Deficit (VPD Persamaan Tetens)
Mengukur defisit tekanan uap air antara bagian dalam daun dengan udara bebas, yang mengatur laju transpirasi dan pembukaan stomata tanaman.

Tekanan uap jenuh udara pada suhu $T$ (°C):
$$e_s(T) = 0.61078 \times \exp\left(\frac{17.27 \times T}{T + 237.3}\right) \quad (\text{satuan: kPa})$$

Tekanan uap aktual berdasarkan Kelembapan Relatif ($RH$ %):
$$e_a = e_s(T) \times \frac{RH}{100}$$

Tekanan Defisit Uap:
$$\text{VPD} = e_s(T) - e_a = e_s(T) \times \left(1 - \frac{RH}{100}\right)$$

*Ambang Batas Agronomi Tropis*: Rentang optimal berada pada 0.45 hingga 1.25 kPa. Jika VPD < 0.3 kPa, transpirasi terhambat dan risiko jamur meningkat; jika VPD > 1.6 kPa, tanaman menutup stomata dan pertumbuhannya terhenti.

### 4. Satuan Derajat Hari Kumulatif: Growing Degree Days (GDD)
Mengukur akumulasi energi panas harian yang diperlukan tanaman untuk bertransisi dari satu fase fenologis ke fase berikutnya (vegetatif ke generatif hingga panen).

$$\text{GDD}_{\text{harian}} = \max\left(0, \frac{T_{\max} + T_{\min}}{2} - T_{\text{base}}\right)$$

$$\text{GDD}_{\text{kumulatif}} = \sum_{t=1}^{D} \text{GDD}_t$$

Suhu dasar biologis ($T_{\text{base}}$) disesuaikan menurut komoditas (misal: Padi 10 °C, Jagung 10 °C, Sawi 8 °C, Kentang 7 °C).

### 5. Evapotranspirasi Acuan Standar: FAO-56 Penman-Monteith ($ET_0$)
Menghitung laju penguapan acuan harian tanaman rumput standar setinggi 0.12 meter dengan resistensi permukaan $70\text{ s/m}$ dan albedo $0.23$:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

Di mana:
- $R_n$: Radiasi surya netto pada permukaan tanaman ($MJ/m^2/\text{hari}$).
- $G$: Kerapatan fluks panas tanah ($MJ/m^2/\text{hari}$, bernilai mendekati 0 untuk periode harian).
- $T$: Suhu udara rata-rata pada ketinggian 2 meter (°C).
- $u_2$: Kecepatan angin pada ketinggian 2 meter ($m/s$).
- $e_s - e_a$: Defisit tekanan uap jenuh (kPa).
- $\Delta$: Kemiringan kurva tekanan uap jenuh ($kPa/^\circ\text{C}$).
- $\gamma$: Konstanta psikrometrik ($kPa/^\circ\text{C}$).

Evapotranspirasi aktual tanaman ($ET_c$) dihitung dengan mengalikan $ET_0$ terhadap koefisien tanaman:
$$ET_c = K_c \times ET_0$$

Neraca air lahan kumulatif ($W_b$):
$$W_b = \text{Curah Hujan} - ET_c$$

### 6. Crop Suitability Index (CSI) dengan Fungsi Keanggotaan Trapesium
Menilai kecocokan suatu variabel lingkungan $x$ (suhu, pH, VWC tanah, curah hujan, salinitas EC) terhadap kurva toleransi biologis tanaman $(x_{\min,\text{abs}}, x_{\min,\text{opt}}, x_{\max,\text{opt}}, x_{\max,\text{abs}})$:

$$S(x) = \begin{cases} 
0.0, & x \le x_{\min,\text{abs}} \text{ atau } x \ge x_{\max,\text{abs}} \\
\frac{x - x_{\min,\text{abs}}}{x_{\min,\text{opt}} - x_{\min,\text{abs}}}, & x_{\min,\text{abs}} < x < x_{\min,\text{opt}} \\
1.0, & x_{\min,\text{opt}} \le x \le x_{\max,\text{opt}} \\
\frac{x_{\max,\text{abs}} - x}{x_{\max,\text{abs}} - x_{\max,\text{opt}}}, & x_{\max,\text{opt}} < x < x_{\max,\text{abs}}
\end{cases}$$

Skor masing-masing variabel digabungkan menggunakan **Hukum Minimum Liebig** (*Liebig's Law of the Minimum*) dan rata-rata geometrik:

$$\text{CSI}_{\text{Liebig}} = \min(S_{\text{suhu}}, S_{\text{pH}}, S_{\text{VWC}}, S_{\text{hujan}}, S_{\text{EC}})$$

$$\text{CSI}_{\text{Geometrik}} = \left( \prod_{j=1}^{5} S_j^{w_j} \right)^{\frac{1}{\sum w_j}}$$

$$\text{CSI}_{\text{Gabungan}} = 0.60 \times \text{CSI}_{\text{Liebig}} + 0.40 \times \text{CSI}_{\text{Geometrik}}$$

Prinsip ini menjamin bahwa jika ada satu variabel yang sangat mematikan bagi tanaman (misal: tanah tergenang air pada tanaman semangka sehingga $S_{\text{VWC}} = 0$), maka skor kesesuaian keseluruhan akan langsung anjlok meskipun suhu udara dan pH tanah sangat ideal.

### 7. Formulasi Keputusan Strategi Multi-Kriteria (Multi-Criteria Decision Analysis)
Sistem meranking kandidat komoditas dengan formula berbobot yang menyeimbangkan antara kecocokan biologi, keuntungan finansial yang dapat direalisasikan, dan penalti risiko lapangan:

$$\text{Skor Akhir} = 0.50 \times \text{CSI} + 0.30 \times (\text{CSI} \times \text{NormProfit}) - 0.20 \times \text{PenaltiRisiko}$$

Di mana:
- $\text{NormProfit}$: Laba bersih normal yang dinormalisasi dengan skala min-max (0.0 sampai 1.0).
- $\text{CSI} \times \text{NormProfit}$: Keuntungan finansial yang dapat direalisasikan. Jika tanaman memiliki harga pasar tinggi (misal cabai) namun ditanam di sawah rawa yang tergenang ($\text{CSI} = 0.1$), maka faktor keuntungan ini otomatis diredam menjadi mendekati nol, sehingga sistem tidak merekomendasikan komoditas yang mustahil tumbuh.
- $\text{PenaltiRisiko}$: Pengurangan skor sebesar 0.15 per faktor risiko agroklimat yang terdeteksi (salinitas tinggi, defisit air parah, potensi serangan jamur karena kelembapan berlebih).

### 8. Dosis Pemupukan Berimbang Defisit
Menghitung kebutuhan pupuk kimia murni per hektar untuk menutup kekurangan hara antara kebutuhan tanaman dengan ketersediaan hara di dalam tanah:

$$\text{Defisit N} = \max(0, N_{\text{kebutuhan}} - N_{\text{tersedia}})$$
$$\text{Dosis Urea} = \frac{\text{Defisit N}}{0.46} \quad (\text{kandungan N pada Urea adalah 46\%})$$

$$\text{Defisit P} = \max(0, P_{\text{kebutuhan}} - P_{\text{tersedia}})$$
$$\text{Dosis SP-36} = \frac{\text{Defisit P}}{0.36} \quad (\text{kandungan } P_2O_5 \text{ pada SP-36 adalah 36\%})$$

$$\text{Defisit K} = \max(0, K_{\text{kebutuhan}} - K_{\text{tersedia}})$$
$$\text{Dosis KCl} = \frac{\text{Defisit K}}{0.60} \quad (\text{kandungan } K_2O \text{ pada KCl adalah 60\%})$$

Jika $pH < 5.5$ (tanah masam), sistem menambahkan rekomendasi kapur pertanian (Dolomit):
$$\text{Dosis Dolomit} = \max\left(500, \frac{6.0 - pH}{0.1} \times 250\right) \text{ kg/ha}$$

---

## 5. Ringkasan Singkat untuk Bahan Presentasi / Ujian (Cheat Sheet)

| Pertanyaan Penguji | Jawaban Singkat & Tepat |
| :--- | :--- |
| **Dari mana sumber data tanaman?** | Menggabungkan 4 standar resmi: **FAO EcoCrop** (ambang batas bio-fisik), **FAO-56** (koefisien air $K_c$), **Balitbangtan/Kementan RI** (kebutuhan N-P-K spesifik tropis), dan **BPS/Pasar Induk** (harga jual IDR & biaya produksi). |
| **Berapa komoditas yang didukung?** | **17 komoditas strategis Indonesia**, mencakup tanaman pangan (Padi, Jagung, Singkong), palawija (Kedelai, Kacang Tanah, Kacang Hijau), hortikultura bumbu & buah (Cabai Merah, Cabai Rawit, Tomat, Terung, Bawang Merah), sayuran daun (Sawi Hijau, Kangkung, Kubis), sayuran umbi (Kentang, Wortel), dan buah semusim (Semangka). |
| **AI apa yang dipakai?** | **Hybrid AI**: Menggabungkan **Machine Learning Tabular (Random Forest)** untuk klasifikasi probabilitas dan regresi panen, **TreeSHAP** untuk transparansi faktor pembatas/pendukung lahan, serta **LLM (Gemini)** untuk sintesis laporan konsultatif yang terikat data (*grounded*). |
| **Bagaimana jika sensor IoT error atau loncat?** | Dilengkapi lapisan pembersihan data: **Hampel Filter (Median Absolute Deviation)** untuk membuang lonjakan palsu (*spike*), detektor deviasi standar untuk sensor macet (*stuck sensor*), dan kalibrasi kurva tekstur tanah. |
| **Bagaimana cara sistem meranking tanaman?** | Menggunakan formula **Multi-Criteria Optimization**: 50% Kesesuaian Agronomi CSI + 30% Laba Riil yang Dapat Dipanen - 20% Penalti Risiko Agroklimat. Memastikan tanaman berharga mahal tidak dipilih jika kondisi tanah membunuh tanaman tersebut. |
| **Apakah LLM bisa berhalusinasi?** | **Tidak**, karena arsitektur sistem membatasi LLM hanya pada peran penyusun narasi (*Synthesizer*). Seluruh angka skor, tonase, laba, dan kilogram pupuk dihitung terlebih dahulu oleh mesin matematika agronomi. Jika koneksi offline, sistem otomatis memakai fallback deterministik tanpa error. |
