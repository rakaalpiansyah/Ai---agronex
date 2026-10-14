# Ai---agronex: Sistem Rekomendasi Tanaman & Strategi Budidaya Berbasis IoT

Platform AI Engineering end-to-end untuk mengevaluasi kesesuaian lahan pertanian dan merumuskan strategi budidaya presisi (kalender tanam, irigasi adaptif, pemupukan NPK, dan mitigasi risiko) berdasarkan data telemetri sensor IoT, standar agronomi FAO EcoCrop, dan Machine Learning tabular.

---

## Arsitektur Sistem

Sistem dibangun dengan prinsip **Clean Architecture & MLOps** yang terbagi dalam lapisan modular:

1. **IoT Ingestion & Quality Control (`src/ingestion/`)**:
   - Skema payload Pydantic v2 untuk data telemetri multi-sensor (tanah, cuaca, air).
   - Validasi batas fisik (pH 3-10, VWC 0-100%, EC 0-20 dS/m).
   - Deteksi sensor macet (*stuck sensor*) berbasis deviasi standar jendela bergerak.
   - Filter lonjakan spike menggunakan Hampel filter (Median Absolute Deviation).
   - Kalibrasi kurva tekstur tanah dan normalisasi EC ke suhu referensi 25 C.

2. **Data Processing & Medallion Storage (`src/processing/`)**:
   - **Bronze Layer**: Penyimpanan append-only telemetri mentah tervalidasi.
   - **Silver Layer**: Data terkalibrasi dengan imputasi gap pendek (< 2 jam).
   - **Gold Layer**: Agregasi statistik harian dan matriks fitur jendela 30 hari.

3. **Agronomic Indices Engine (`src/agronomy/`)**:
   - Defisit Tekanan Uap (*Vapor Pressure Deficit* / VPD) via persamaan Tetens.
   - Akumulasi Derajat Hari Pertumbuhan (*Growing Degree Days* / GDD).
   - Evapotranspirasi acuan harian FAO-56 Penman-Monteith ($ET_0$) dan tanaman ($ET_c = K_c \times ET_0$).
   - Neraca Air Lahan (*Water Balance* $= P + I - ET_c$) dan Aridity Index.
   - Deteksi hari stres abiotik (kekeringan, genangan, suhu panas ekstrem).
   - Baseline Crop Suitability Index (CSI) dengan fungsi keanggotaan trapesium dan Hukum Minimum Liebig.

4. **Machine Learning & Explainability (`src/ml/`)**:
   - Partisi data spasial bebas kebocoran (*zero spatial leakage*) menggunakan `GroupKFold` per `site_id`.
   - Estimator Random Forest multi-kelas untuk klasifikasi kecocokan tanaman.
   - Estimator Random Forest regresi untuk estimasi hasil panen (yield dalam ton/ha).
   - Mesin atribusi fitur TreeSHAP untuk mengidentifikasi faktor pendukung dan faktor pembatas.

5. **Strategy Decision Engine (`src/strategy/`)**:
   - Pemeringkatan multi-kriteria: bobot kecocokan agronomi (50%) + profit ekonomi terealisasi (30%) - penalti risiko (20%).
   - Kalkulator profitabilitas 3 skenario pasar (pesimis, normal, optimis).
   - Penjadwal kalender tanam dinamis berbasis akumulasi GDD dan jendela kelembapan tanah.
   - Resep irigasi presisi berbasis defisit neraca air dan panduan pemupukan defisit NPK serta pengapuran dolomit.
   - Pintu keyakinan (*Confidence Gate*): status otomatis dialihkan ke `NEEDS_AGRONOMIST_REVIEW` jika kelengkapan data < 70% atau skor kecocokan marginal.
   - Generator narasi deterministik berbahasa Indonesia bebas halusinasi.

6. **Production Serving (`src/api/`)**:
   - Layanan REST API berbasis FastAPI siap integrasi ke dashboard web, aplikasi mobile, atau bot perpesanan.

---

## Struktur Direktori

```
d:\YOTA\AI-Engineer\
├── config/
│   ├── settings.py              # Konfigurasi via Pydantic BaseSettings
│   ├── crop_catalog.json        # Basis pengetahuan FAO EcoCrop
│   └── economic_catalog.json    # Parameter harga komoditas dan biaya input (IDR)
├── src/
│   ├── domain/                  # Entitas bisnis, enum, dan exception murni
│   ├── ingestion/               # Validasi schema, quality control, dan kalibrasi sensor
│   ├── processing/              # Pipeline Medallion (Bronze, Silver, Gold) dan agregasi
│   ├── agronomy/                # Formula ilmiah VPD, GDD, ET0, CSI, dan loader katalog
│   ├── ml/                      # Spatial splitter, baseline CSI, trainer, dan SHAP explainer
│   ├── strategy/                # Multi-criteria engine, ekonomi, resep budidaya, dan narasi
│   └── api/                     # FastAPI application factory, dependency injection, dan routes
├── tests/
│   ├── unit/                    # Uji unit agronomi, CSI, quality checker, dan strategy
│   └── integration/             # Uji integrasi endpoint API end-to-end
├── scripts/
│   ├── generate_synthetic_data.py # Generator 30 hari data telemetri 3 tipe lahan
│   └── run_training.py          # Script pelatihan model ML dan registrasi artifact
├── models/                      # Penyimpanan artifact model (.joblib)
├── pyproject.toml               # Spesifikasi dependensi dan konfigurasi pytest
└── Dockerfile                   # Kontainerisasi siap produksi
```

---

## Panduan Pengoperasian

### 1. Persiapan Dependensi

Pastikan Python 3.11+ telah terpasang, lalu instal dependensi:

```powershell
pip install -e .
```

Atau instal dependensi langsung:
```powershell
pip install fastapi uvicorn pydantic pydantic-settings pandas numpy scipy scikit-learn shap pyarrow joblib httpx pytest
```

### 2. Menjalankan Uji Otomatis (Automated Tests)

Jalankan seluruh pengujian unit dan integrasi menggunakan pytest:

```powershell
python -m pytest tests -v
```

### 3. Generate Data Simulasi & Latih Model ML

Untuk menghasilkan data telemetri realistis 30 hari untuk 3 tipe lahan (lahan basah, lahan kering, hortikultura dataran tinggi) serta melatih model:

```powershell
$env:PYTHONPATH="."
python scripts/generate_synthetic_data.py
python scripts/run_training.py
```

### 4. Menjalankan Aplikasi & Frontend Dashboard

#### Cara 1: Menjalankan Server Terpadu (Backend + Frontend)
Jalankan server backend (otomatis menyajikan dashboard UI di root URL):

```powershell
python run_server.py
```

Buka browser Anda:
- **Dashboard Antarmuka Agrosense**: `http://localhost:8000`
- **Dokumentasi OpenAPI / Swagger UI**: `http://localhost:8000/docs`

#### Cara 2: Menjalankan Frontend Development Mode (Hot-Reload)
Jika Anda ingin mengembangkan antarmuka React secara aktif:

```powershell
cd FE
npm run dev
```
Akses server pengembang frontend di `http://localhost:5173`. Setiap panggilan API akan diteruskan secara otomatis ke backend `http://localhost:8000`.

---

## Endpoint API Utama

| Metode | Endpoint | Deskripsi |
| --- | --- | --- |
| `GET` | `/health` | Memeriksa status kesehatan service dan kesiapan data lake |
| `GET` | `/api/v1/recommendations/catalog` | Melihat daftar komoditas dan parameter optimal FAO EcoCrop |
| `POST` | `/api/v1/telemetry/ingest` | Ingesti batch telemetri IoT ke Bronze dan transformasi Silver |
| `POST` | `/api/v1/recommendations/evaluate` | Evaluasi langsung rekomendasi tanaman dari parameter lahan |
| `POST` | `/api/v1/recommendations/evaluate-site/{site_id}` | Evaluasi rekomendasi berbasis riwayat data sensor tersimpan di Gold lake |

### Contoh Request Evaluasi Langsung (`POST /api/v1/recommendations/evaluate`)

```json
{
  "site_id": "LAHAN-LAMPUNG-A07",
  "mean_air_temp": 28.0,
  "min_air_temp": 23.0,
  "max_air_temp": 32.0,
  "mean_rh": 80.0,
  "mean_soil_vwc": 70.0,
  "mean_soil_temp": 27.0,
  "mean_soil_ph": 6.3,
  "mean_soil_ec": 1.0,
  "total_rainfall": 500.0,
  "mean_solar_radiation": 450.0,
  "mean_wind_speed": 1.5,
  "mean_soil_n": 120.0,
  "mean_soil_p": 45.0,
  "mean_soil_k": 60.0,
  "observation_days": 30
}
```

### Contoh Response Rekomendasi

```json
{
  "site_id": "LAHAN-LAMPUNG-A07",
  "evaluated_at": "2026-10-14T20:15:00.000Z",
  "data_completeness_ratio": 1.0,
  "confidence_level": "HIGH",
  "recommendation_status": "APPROVED",
  "model_version": "1.0.0",
  "primary_recommendation": {
    "rank": 1,
    "crop_id": "padi_sawah",
    "crop_name": "Padi Sawah",
    "composite_score": 0.519,
    "suitability_score": 1.0,
    "fao_class": "S1",
    "fao_label": "Sangat Sesuai",
    "limiting_factor": "temperature",
    "yield_estimate_ton_ha": 12.7,
    "yield_range_ton_ha": [9.6, 15.9],
    "projected_profit_normal_idr": 64810000.0,
    "prescriptions": {
      "sowing_window": "Minggu ke-3 October 2026 (Target: 21 Oct s.d. 04 Nov)",
      "irrigation_advice": "Ketersediaan air tanah memadai. Lakukan monitoring kelembapan rutin.",
      "fertilizer_prescription_kg_ha": {
        "urea_n": 0.0,
        "sp36_p": 0.0,
        "kcl_k": 0.0
      },
      "soil_amendment_advice": null,
      "identified_risks": [
        "Profil risiko agroklimat terpantau rendah dan aman."
      ]
    },
    "narrative_explanation": "Rekomendasi Utama untuk Lahan LAHAN-LAMPUNG-A07: Padi Sawah, skor kecocokan 1.00 (S1 - Sangat Sesuai)..."
  },
  "alternatives": [
    {
      "rank": 2,
      "crop_id": "jagung_hibrida",
      "crop_name": "Jagung Hibrida",
      "composite_score": 0.395,
      "suitability_score": 0.789,
      "fao_class": "S2",
      "limiting_factor": "rainfall",
      "projected_profit_normal_idr": 29800000.0
    }
  ],
  "system_notes": []
}
```
