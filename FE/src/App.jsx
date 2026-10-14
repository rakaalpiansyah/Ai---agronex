import React, { useState, useEffect } from 'react';
import {
  Sprout,
  Sun,
  Moon,
  CloudRain,
  Thermometer,
  Droplets,
  Wind,
  Layers,
  FlaskConical,
  Coins,
  Calendar,
  AlertTriangle,
  BookOpen,
  Sparkles,
  ChevronRight,
  RefreshCw,
  CheckCircle2,
  X,
  TrendingUp,
  BarChart3,
  Sliders,
  Gauge,
  FileText,
  Search,
  Check,
  Zap
} from 'lucide-react';

const API_BASE_URL = typeof window !== 'undefined' && window.location.port === '5173' ? '' : 'http://localhost:8000';

const PRESETS = [
  {
    id: 'padi',
    name: 'Lahan Basah (Padi Sawah)',
    desc: 'Aluvial dataran rendah, air melimpah',
    values: {
      site_id: 'LAHAN-BASAH-SUBANG-01',
      mean_air_temp: 28.0,
      min_air_temp: 23.0,
      max_air_temp: 32.0,
      mean_rh: 82.0,
      mean_soil_vwc: 72.0,
      mean_soil_temp: 27.0,
      mean_soil_ph: 6.3,
      mean_soil_ec: 1.0,
      total_rainfall: 500.0,
      mean_solar_radiation: 450.0,
      mean_wind_speed: 1.5,
      mean_soil_n: 120.0,
      mean_soil_p: 45.0,
      mean_soil_k: 60.0,
      observation_days: 30,
      use_llm: false
    }
  },
  {
    id: 'jagung',
    name: 'Lahan Kering (Jagung Hibrida)',
    desc: 'Tanah lempung berpasir, drainase baik',
    values: {
      site_id: 'LAHAN-KERING-GROBOGAN-02',
      mean_air_temp: 27.0,
      min_air_temp: 21.0,
      max_air_temp: 32.0,
      mean_rh: 70.0,
      mean_soil_vwc: 46.0,
      mean_soil_temp: 26.0,
      mean_soil_ph: 6.5,
      mean_soil_ec: 0.8,
      total_rainfall: 380.0,
      mean_solar_radiation: 500.0,
      mean_wind_speed: 1.8,
      mean_soil_n: 135.0,
      mean_soil_p: 50.0,
      mean_soil_k: 70.0,
      observation_days: 30,
      use_llm: false
    }
  },
  {
    id: 'hortikultura',
    name: 'Dataran Tinggi (Cabai / Tomat)',
    desc: 'Andosol pegunungan sejuk',
    values: {
      site_id: 'LAHAN-TINGGI-LEMBANG-03',
      mean_air_temp: 22.0,
      min_air_temp: 16.0,
      max_air_temp: 27.0,
      mean_rh: 82.0,
      mean_soil_vwc: 54.0,
      mean_soil_temp: 20.0,
      mean_soil_ph: 6.2,
      mean_soil_ec: 1.1,
      total_rainfall: 420.0,
      mean_solar_radiation: 420.0,
      mean_wind_speed: 1.4,
      mean_soil_n: 160.0,
      mean_soil_p: 95.0,
      mean_soil_k: 140.0,
      observation_days: 30,
      use_llm: false
    }
  },
  {
    id: 'sawi',
    name: 'Kebun Sayuran (Sawi Hijau)',
    desc: 'Dataran menengah, siklus genjah',
    values: {
      site_id: 'LAHAN-SAYUR-MALANG-04',
      mean_air_temp: 23.5,
      min_air_temp: 18.0,
      max_air_temp: 28.0,
      mean_rh: 78.0,
      mean_soil_vwc: 62.0,
      mean_soil_temp: 22.0,
      mean_soil_ph: 6.4,
      mean_soil_ec: 0.9,
      total_rainfall: 320.0,
      mean_solar_radiation: 430.0,
      mean_wind_speed: 1.2,
      mean_soil_n: 95.0,
      mean_soil_p: 45.0,
      mean_soil_k: 80.0,
      observation_days: 30,
      use_llm: false
    }
  },
  {
    id: 'kemarau',
    name: 'Lahan Kemarau / MK (Kacang Hijau / Semangka)',
    desc: 'Curah hujan rendah, tanah porous berpasir',
    values: {
      site_id: 'LAHAN-KEMARAU-INDRAMAYU-05',
      mean_air_temp: 29.5,
      min_air_temp: 23.0,
      max_air_temp: 34.5,
      mean_rh: 64.0,
      mean_soil_vwc: 32.0,
      mean_soil_temp: 28.5,
      mean_soil_ph: 6.5,
      mean_soil_ec: 0.9,
      total_rainfall: 180.0,
      mean_solar_radiation: 520.0,
      mean_wind_speed: 2.1,
      mean_soil_n: 110.0,
      mean_soil_p: 40.0,
      mean_soil_k: 90.0,
      observation_days: 30,
      use_llm: false
    }
  }
];

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('agrosense_theme') || 'light');
  const [serverOnline, setServerOnline] = useState(false);
  const [activePreset, setActivePreset] = useState('padi');
  const [formData, setFormData] = useState(PRESETS[0].values);
  const [loading, setLoading] = useState(false);
  const [isAutoSyncing, setIsAutoSyncing] = useState(false);
  const [autoEvaluate, setAutoEvaluate] = useState(true);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'leaderboard' | 'indices'
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [catalogData, setCatalogData] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState('');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('agrosense_theme', theme);
  }, [theme]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'healthy') setServerOnline(true);
      })
      .catch(() => setServerOnline(false));

    handleEvaluate(PRESETS[0].values, false);
  }, []);

  // Real-time Auto-Evaluation debounced when non-LLM mode is active
  useEffect(() => {
    if (autoEvaluate && !formData.use_llm) {
      const timer = setTimeout(() => {
        handleEvaluate(formData, true);
      }, 250);
      return () => clearTimeout(timer);
    }
  }, [formData, autoEvaluate]);

  useEffect(() => {
    const handleKeyDown = e => {
      if (e.key === 'Escape' && catalogOpen) {
        setCatalogOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [catalogOpen]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const handlePresetSelect = preset => {
    setActivePreset(preset.id);
    setFormData(preset.values);
    handleEvaluate(preset.values, false);
  };

  const handleInputChange = (field, value) => {
    const parsed = typeof value === 'boolean' ? value : (isNaN(parseFloat(value)) ? value : parseFloat(value));
    setFormData(prev => {
      const next = { ...prev, [field]: parsed };
      if (field === 'mean_air_temp' && typeof parsed === 'number') {
        next.min_air_temp = parseFloat((parsed - 4.5).toFixed(1));
        next.max_air_temp = parseFloat((parsed + 4.5).toFixed(1));
        next.mean_soil_temp = parseFloat((parsed - 1.0).toFixed(1));
      }
      return next;
    });
  };

  const handleEvaluate = async (dataToSubmit = formData, isBackground = false) => {
    if (isBackground) {
      setIsAutoSyncing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/recommendations/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSubmit)
      });
      if (!response.ok) {
        throw new Error(`Server returned error HTTP ${response.status}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Gagal menghubungi server rekomendasi.');
    } finally {
      if (isBackground) {
        setIsAutoSyncing(false);
      } else {
        setLoading(false);
      }
    }
  };

  const openCatalog = async () => {
    setCatalogOpen(true);
    if (catalogData.length === 0) {
      setCatalogLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/catalog`);
        const data = await res.json();
        setCatalogData(data);
      } catch (err) {
        console.error('Failed to load crop catalog', err);
      } finally {
        setCatalogLoading(false);
      }
    }
  };

  const formatCurrency = val => {
    if (val === undefined || val === null) return 'Rp 0';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const primary = result?.primary_recommendation;
  const indices = result?.agronomic_indices;
  const allEvaluations = result?.all_evaluations || [];

  const filteredCatalog = catalogData.filter(crop =>
    crop.name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
    crop.category.toLowerCase().includes(catalogSearch.toLowerCase()) ||
    crop.crop_id.toLowerCase().includes(catalogSearch.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* Top Application Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">
            <Sprout size={22} />
          </div>
          <div>
            <div className="brand-title">
              <span>Agrosense</span>
              <span className="brand-version-tag">AI Engineer v1.0</span>
            </div>
            <p className="brand-subtitle">IoT Telemetry & Precision Crop Cultivation Strategy Engine</p>
          </div>
        </div>

        <div className="header-actions">
          <div className={`badge ${serverOnline ? 'badge-green' : 'badge-amber'}`}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: serverOnline ? '#059669' : '#d97706'
              }}
            />
            {serverOnline ? 'Backend Online (Port 8000)' : 'Mode Mandiri'}
          </div>

          <button className="btn btn-secondary" onClick={openCatalog}>
            <BookOpen size={15} />
            <span>Katalog Komoditas ({catalogData.length > 0 ? catalogData.length : 17})</span>
          </button>

          <button
            className="btn btn-secondary btn-icon"
            onClick={toggleTheme}
            aria-label="Toggle tema gelap/terang"
            title="Ganti Tema"
          >
            {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
          </button>
        </div>
      </header>

      {/* Quick Agronomic Computed Indices Strip */}
      {indices && (
        <section className="metric-strip" aria-label="Ringkasan Indeks Agronomi">
          <div className="metric-strip-card">
            <div className="metric-strip-label">
              <span>Vapor Pressure Deficit</span>
              <Gauge size={14} color="var(--color-primary)" />
            </div>
            <div className="metric-strip-val font-mono">{indices.vpd_kpa} <span style={{ fontSize: 13, fontWeight: 500 }}>kPa</span></div>
            <div className="metric-strip-note">Formula Tetens (Transpirasi)</div>
          </div>

          <div className="metric-strip-card">
            <div className="metric-strip-label">
              <span>Satuan Panas Kumulatif</span>
              <Thermometer size={14} color="var(--color-amber)" />
            </div>
            <div className="metric-strip-val font-mono">{indices.cumulative_gdd} <span style={{ fontSize: 13, fontWeight: 500 }}>°C-hari</span></div>
            <div className="metric-strip-note">Growing Degree Days ({formData.observation_days} hari)</div>
          </div>

          <div className="metric-strip-card">
            <div className="metric-strip-label">
              <span>Evapotranspirasi Acuan</span>
              <Sun size={14} color="var(--color-sky)" />
            </div>
            <div className="metric-strip-val font-mono">{indices.reference_et0_mm} <span style={{ fontSize: 13, fontWeight: 500 }}>mm</span></div>
            <div className="metric-strip-note">FAO-56 Penman-Monteith (ET0)</div>
          </div>

          <div className="metric-strip-card">
            <div className="metric-strip-label">
              <span>Neraca Air Lahan</span>
              <CloudRain size={14} color={indices.water_balance_mm >= 0 ? "var(--color-sky)" : "var(--color-rose)"} />
            </div>
            <div className="metric-strip-val font-mono" style={{ color: indices.water_balance_mm >= 0 ? "var(--color-sky)" : "var(--color-rose)" }}>
              {indices.water_balance_mm >= 0 ? `+${indices.water_balance_mm}` : indices.water_balance_mm} <span style={{ fontSize: 13, fontWeight: 500 }}>mm</span>
            </div>
            <div className="metric-strip-note">Curah Hujan dikurangi Evapotranspirasi</div>
          </div>
        </section>
      )}

      {/* Main Grid: Controls on Left, Results on Right */}
      <div className="dashboard-grid">
        {/* Left Column: Ergonomic Telemetry Inputs */}
        <section className="card" aria-label="Panel Input Sensor">
          <div className="card-header">
            <h2 className="card-title">
              <Sliders size={17} />
              <span>Parameter Telemetri Lahan</span>
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {autoEvaluate && !formData.use_llm && (
                <div className="pulse-live" title="Auto-evaluasi real-time aktif untuk mode kalkulasi non-AI">
                  <span className="pulse-dot" style={{ background: isAutoSyncing ? 'var(--color-amber)' : 'var(--color-primary)' }} />
                  <span>{isAutoSyncing ? 'Menghitung...' : 'Auto-Sync Aktif'}</span>
                </div>
              )}
              <button
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: '4px 8px' }}
                onClick={() => handlePresetSelect(PRESETS.find(p => p.id === activePreset) || PRESETS[0])}
                title="Reset ke nilai awal preset"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Quick Presets */}
          <div style={{ marginBottom: 16 }}>
            <div className="category-title">
              <Layers size={13} />
              <span>Profil Lahan Cepat</span>
            </div>
            <div className="presets-grid">
              {PRESETS.map(preset => (
                <button
                  key={preset.id}
                  className={`preset-chip ${activePreset === preset.id ? 'active' : ''}`}
                  onClick={() => handlePresetSelect(preset)}
                >
                  <div style={{ fontWeight: activePreset === preset.id ? 700 : 600 }}>{preset.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{preset.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Category 1: Climate & Atmosphere */}
          <div className="telemetry-category">
            <div className="category-title">
              <Thermometer size={13} />
              <span>1. Mikroklimat & Udara</span>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Suhu Udara Rata-rata</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--color-primary)' }}>Normal: 24 - 30 °C</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="14"
                  max="38"
                  step="0.5"
                  value={formData.mean_air_temp}
                  onChange={e => handleInputChange('mean_air_temp', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_air_temp}
                    step="0.5"
                    onChange={e => handleInputChange('mean_air_temp', e.target.value)}
                  />
                  <span className="num-unit">°C</span>
                </div>
              </div>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Kelembapan Udara (RH)</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>60 - 90 %</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="40"
                  max="95"
                  step="1"
                  value={formData.mean_rh}
                  onChange={e => handleInputChange('mean_rh', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_rh}
                    step="1"
                    onChange={e => handleInputChange('mean_rh', e.target.value)}
                  />
                  <span className="num-unit">%</span>
                </div>
              </div>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Radiasi Matahari Rata-rata</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>300 - 600 W/m²</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="200"
                  max="700"
                  step="10"
                  value={formData.mean_solar_radiation}
                  onChange={e => handleInputChange('mean_solar_radiation', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_solar_radiation}
                    step="10"
                    onChange={e => handleInputChange('mean_solar_radiation', e.target.value)}
                  />
                  <span className="num-unit">W/m²</span>
                </div>
              </div>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Kecepatan Angin Rata-rata</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>0.5 - 5.0 m/s</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="0.5"
                  max="6.0"
                  step="0.1"
                  value={formData.mean_wind_speed}
                  onChange={e => handleInputChange('mean_wind_speed', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_wind_speed}
                    step="0.1"
                    onChange={e => handleInputChange('mean_wind_speed', e.target.value)}
                  />
                  <span className="num-unit">m/s</span>
                </div>
              </div>
            </div>
          </div>

          {/* Category 2: Hydrology & Water */}
          <div className="telemetry-category">
            <div className="category-title">
              <Droplets size={13} />
              <span>2. Hidrologi & Air Tanah</span>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Kelembapan Air Tanah (VWC)</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--color-sky)' }}>Kapasitas Lapang</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="20"
                  max="90"
                  step="1"
                  value={formData.mean_soil_vwc}
                  onChange={e => handleInputChange('mean_soil_vwc', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_soil_vwc}
                    step="1"
                    onChange={e => handleInputChange('mean_soil_vwc', e.target.value)}
                  />
                  <span className="num-unit">%</span>
                </div>
              </div>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Curah Hujan Kumulatif (30 Hari)</span>
                <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>100 - 600 mm</span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="50"
                  max="800"
                  step="10"
                  value={formData.total_rainfall}
                  onChange={e => handleInputChange('total_rainfall', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.total_rainfall}
                    step="10"
                    onChange={e => handleInputChange('total_rainfall', e.target.value)}
                  />
                  <span className="num-unit">mm</span>
                </div>
              </div>
            </div>
          </div>

          {/* Category 3: Soil Chemistry & Nutrients */}
          <div className="telemetry-category">
            <div className="category-title">
              <FlaskConical size={13} />
              <span>3. Kimia & Hara Tanah</span>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Derajat Keasaman Tanah (pH)</span>
                <span className="font-mono" style={{ fontSize: 12, color: formData.mean_soil_ph < 5.5 ? 'var(--color-rose)' : 'var(--color-primary)' }}>
                  {formData.mean_soil_ph < 5.5 ? 'Masam (Perlu Kapur)' : 'Netral/Ideal'}
                </span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="4.0"
                  max="8.5"
                  step="0.1"
                  value={formData.mean_soil_ph}
                  onChange={e => handleInputChange('mean_soil_ph', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_soil_ph}
                    step="0.1"
                    onChange={e => handleInputChange('mean_soil_ph', e.target.value)}
                  />
                  <span className="num-unit">pH</span>
                </div>
              </div>
            </div>

            <div className="dual-control-row">
              <div className="dual-control-header">
                <span className="param-name">Salinitas Tanah (EC)</span>
                <span className="font-mono" style={{ fontSize: 12, color: formData.mean_soil_ec > 2.0 ? 'var(--color-amber)' : 'var(--text-muted)' }}>
                  Maks 2.0 dS/m
                </span>
              </div>
              <div className="dual-control-inputs">
                <input
                  type="range"
                  className="slider-input"
                  min="0.2"
                  max="4.0"
                  step="0.1"
                  value={formData.mean_soil_ec}
                  onChange={e => handleInputChange('mean_soil_ec', e.target.value)}
                />
                <div className="num-input-wrap">
                  <input
                    type="number"
                    className="num-input font-mono"
                    value={formData.mean_soil_ec}
                    step="0.1"
                    onChange={e => handleInputChange('mean_soil_ec', e.target.value)}
                  />
                  <span className="num-unit">dS/m</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 10 }}>
              <div>
                <label className="param-name" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Hara N (kg/ha)</label>
                <input
                  type="number"
                  className="num-input font-mono"
                  style={{ width: '100%', textAlign: 'left', padding: '6px 8px' }}
                  value={formData.mean_soil_n}
                  onChange={e => handleInputChange('mean_soil_n', e.target.value)}
                />
              </div>
              <div>
                <label className="param-name" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Hara P (kg/ha)</label>
                <input
                  type="number"
                  className="num-input font-mono"
                  style={{ width: '100%', textAlign: 'left', padding: '6px 8px' }}
                  value={formData.mean_soil_p}
                  onChange={e => handleInputChange('mean_soil_p', e.target.value)}
                />
              </div>
              <div>
                <label className="param-name" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Hara K (kg/ha)</label>
                <input
                  type="number"
                  className="num-input font-mono"
                  style={{ width: '100%', textAlign: 'left', padding: '6px 8px' }}
                  value={formData.mean_soil_k}
                  onChange={e => handleInputChange('mean_soil_k', e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Auto-Evaluation Toggle Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginTop: 14, marginBottom: 8 }}>
            <label htmlFor="autoEvalToggle" style={{ fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 500 }}>
              <Zap size={15} color={autoEvaluate ? "var(--color-primary)" : "var(--text-muted)"} />
              <span>Auto-Evaluasi Real-time (Non-AI)</span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {autoEvaluate && !formData.use_llm && (
                <span className="pulse-live" style={{ fontSize: 10, padding: '2px 6px' }}>
                  <span className="pulse-dot" style={{ background: isAutoSyncing ? 'var(--color-amber)' : 'var(--color-primary)' }} />
                  {isAutoSyncing ? 'Menghitung...' : 'Live'}
                </span>
              )}
              <input
                type="checkbox"
                id="autoEvalToggle"
                checked={autoEvaluate}
                onChange={e => setAutoEvaluate(e.target.checked)}
                style={{ width: 16, height: 16, accentColor: 'var(--color-primary)', cursor: 'pointer' }}
              />
            </div>
          </div>

          {/* Mode LLM Switch */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14, padding: '10px 12px', background: formData.use_llm ? 'var(--color-amber-subtle)' : 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid', borderColor: formData.use_llm ? 'var(--color-amber-border)' : 'var(--border-color)', transition: 'all 0.15s ease' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input
                type="checkbox"
                id="llmToggle"
                checked={formData.use_llm}
                onChange={e => handleInputChange('use_llm', e.target.checked)}
                style={{ width: 16, height: 16, accentColor: 'var(--color-amber)', cursor: 'pointer' }}
              />
              <label htmlFor="llmToggle" style={{ fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, flex: 1, fontWeight: 600 }}>
                <Sparkles size={15} color="var(--color-amber)" />
                <span>Sintesis Narasi Agronomi Berbasis LLM (AI)</span>
              </label>
            </div>
            {formData.use_llm && (
              <p style={{ fontSize: 11, color: 'var(--color-amber)', paddingLeft: 26, lineHeight: 1.4 }}>
                Mode LLM aktif. Auto-evaluasi real-time dijeda untuk menghemat token API. Klik tombol di bawah untuk meminta konsultasi AI.
              </p>
            )}
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: 14, fontWeight: 700 }}
            onClick={() => handleEvaluate(formData, false)}
            disabled={loading}
          >
            {loading ? (
              <>
                <div className="spinner" />
                <span>Menganalisis Agronomi...</span>
              </>
            ) : formData.use_llm ? (
              <>
                <Sparkles size={16} />
                <span>Jalankan Konsultasi Narasi AI</span>
              </>
            ) : autoEvaluate ? (
              <>
                <RefreshCw size={16} />
                <span>Evaluasi Ulang Manual</span>
              </>
            ) : (
              <>
                <Zap size={16} />
                <span>Evaluasi Kesesuaian Lahan</span>
              </>
            )}
          </button>
        </section>

        {/* Right Column: Multi-Tab Intelligence Results */}
        <main>
          {error && (
            <div className="card" style={{ borderColor: 'var(--color-rose)', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--color-rose)' }}>
                <AlertTriangle size={20} />
                <span style={{ fontWeight: 600 }}>{error}</span>
              </div>
            </div>
          )}

          {primary ? (
            <>
              {/* Header Status Bar */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className={`badge ${result.recommendation_status === 'APPROVED' ? 'badge-green' : 'badge-amber'}`}>
                    <CheckCircle2 size={13} />
                    Status: {result.recommendation_status}
                  </span>
                  <span className="badge badge-sky">Keyakinan: {result.confidence_level}</span>
                  <span className="badge badge-neutral font-mono">Kelengkapan Data: {Math.round(result.data_completeness_ratio * 100)}%</span>
                </div>

                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  ID Lahan: <strong className="font-mono" style={{ color: 'var(--text-primary)' }}>{result.site_id}</strong>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="results-tabs" role="tablist">
                <button
                  className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  <Sprout size={16} />
                  <span>Rekomendasi Utama & Resep</span>
                </button>
                <button
                  className={`tab-btn ${activeTab === 'leaderboard' ? 'active' : ''}`}
                  onClick={() => setActiveTab('leaderboard')}
                >
                  <BarChart3 size={16} />
                  <span>Papan Peringkat ({allEvaluations.length} Komoditas)</span>
                </button>
                <button
                  className={`tab-btn ${activeTab === 'indices' ? 'active' : ''}`}
                  onClick={() => setActiveTab('indices')}
                >
                  <Gauge size={16} />
                  <span>Indeks Ilmiah & Neraca Air</span>
                </button>
              </div>

              {/* Tab 1: Overview & Prescriptions */}
              {activeTab === 'overview' && (
                <>
                  <div className="hero-result-card">
                    <div className="hero-crop-header">
                      <div className="hero-crop-meta">
                        <div className="hero-rank-tag">
                          <Check size={14} />
                          <span>Pilihan Peringkat #1 Teratas</span>
                        </div>
                        <h2 className="crop-name">{primary.crop_name}</h2>
                        <p className="crop-scientific">
                          Kesesuaian Biologis: <strong className="font-mono" style={{ color: 'var(--color-primary)' }}>{(primary.suitability_score * 100).toFixed(1)}%</strong>
                          {' | '}Faktor Pembatas: <strong style={{ color: 'var(--color-amber)' }}>{primary.limiting_factor}</strong>
                        </p>
                      </div>

                      <div className="score-badge-group">
                        <div className="composite-score-box">
                          <div className="composite-score-num font-mono">{primary.composite_score}</div>
                          <div className="composite-score-label">Skor Multi-Kriteria</div>
                        </div>
                        <span className={`badge ${primary.fao_class === 'S1' ? 'badge-green' : primary.fao_class === 'S2' ? 'badge-amber' : 'badge-rose'}`} style={{ fontSize: 13, padding: '5px 10px' }}>
                          Kelas {primary.fao_class}: {primary.fao_label}
                        </span>
                      </div>
                    </div>

                    {/* 5 Liebig Factors */}
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', marginBottom: 8 }}>
                        Kesesuaian 5 Variabel Lingkungan (Hukum Minimum Liebig)
                      </div>
                      <div className="factor-grid">
                        {Object.entries(primary.factor_scores || {}).map(([key, score]) => {
                          const percent = Math.round(score * 100);
                          let color = 'var(--color-primary)';
                          if (percent < 50) color = 'var(--color-rose)';
                          else if (percent < 80) color = 'var(--color-amber)';

                          const labelMap = {
                            temperature: 'Suhu Udara',
                            ph: 'pH Tanah',
                            soil_moisture: 'Air Tanah (VWC)',
                            rainfall: 'Curah Hujan',
                            salinity: 'Salinitas (EC)'
                          };

                          return (
                            <div key={key} className="factor-item">
                              <div className="factor-name">{labelMap[key] || key}</div>
                              <div className="factor-score-num font-mono">{percent}%</div>
                              <div className="progress-bar-bg">
                                <div
                                  className="progress-bar-fill"
                                  style={{ width: `${percent}%`, backgroundColor: color }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* 3-Scenario Economics */}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                          Proyeksi Panen & Estimasi Laba Bersih (Per Hektare)
                        </span>
                        <span className="font-mono" style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                          Estimasi Yield Rata-rata: <strong>{primary.yield_estimate_ton_ha} ton/ha</strong>
                        </span>
                      </div>

                      <div className="economics-grid">
                        <div className="econ-card">
                          <div className="econ-scenario">Skenario Pesimis</div>
                          <div className="econ-val font-mono" style={{ color: 'var(--text-secondary)' }}>
                            {formatCurrency(primary.projected_profit_range_idr[0])}
                          </div>
                          <div className="econ-sub font-mono">
                            Hasil Panen: {primary.yield_range_ton_ha[0]} ton/ha
                          </div>
                        </div>

                        <div className="econ-card highlight">
                          <div className="econ-scenario" style={{ color: 'var(--color-primary)' }}>Skenario Normal</div>
                          <div className="econ-val font-mono" style={{ color: 'var(--color-primary)' }}>
                            {formatCurrency(primary.projected_profit_normal_idr)}
                          </div>
                          <div className="econ-sub" style={{ color: 'var(--color-primary)' }}>
                            Kondisi agroklimat acuan
                          </div>
                        </div>

                        <div className="econ-card">
                          <div className="econ-scenario" style={{ color: 'var(--color-amber)' }}>Skenario Optimis</div>
                          <div className="econ-val font-mono" style={{ color: 'var(--color-amber)' }}>
                            {formatCurrency(primary.projected_profit_range_idr[1])}
                          </div>
                          <div className="econ-sub font-mono">
                            Hasil Panen: {primary.yield_range_ton_ha[1]} ton/ha
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Cultivation Prescriptions Grid */}
                    <div className="prescriptions-container">
                      <div className="presc-card">
                        <div className="presc-card-title">
                          <Calendar size={16} color="var(--color-primary)" />
                          <span>Jadwal Jendela Tanam</span>
                        </div>
                        <p className="presc-card-text">{primary.prescriptions.sowing_window}</p>
                      </div>

                      <div className="presc-card">
                        <div className="presc-card-title">
                          <Droplets size={16} color="var(--color-sky)" />
                          <span>Rekomendasi Irigasi & Air</span>
                        </div>
                        <p className="presc-card-text">{primary.prescriptions.irrigation_advice}</p>
                      </div>

                      <div className="presc-card">
                        <div className="presc-card-title">
                          <FlaskConical size={16} color="var(--color-amber)" />
                          <span>Dosis Pemupukan Berimbang Defisit</span>
                        </div>
                        <div className="fert-pills font-mono">
                          <span className="fert-pill">Urea (N): {primary.prescriptions.fertilizer_prescription_kg_ha.urea_n} kg/ha</span>
                          <span className="fert-pill">SP-36 (P): {primary.prescriptions.fertilizer_prescription_kg_ha.sp36_p} kg/ha</span>
                          <span className="fert-pill">KCl (K): {primary.prescriptions.fertilizer_prescription_kg_ha.kcl_k} kg/ha</span>
                        </div>
                        {primary.prescriptions.soil_amendment_advice && (
                          <p style={{ fontSize: 12, color: 'var(--color-amber)', marginTop: 8 }}>
                            {primary.prescriptions.soil_amendment_advice}
                          </p>
                        )}
                      </div>

                      <div className="presc-card">
                        <div className="presc-card-title">
                          <AlertTriangle size={16} color="var(--color-rose)" />
                          <span>Mitigasi Risiko Lapangan</span>
                        </div>
                        <ul style={{ paddingLeft: 16, fontSize: 12, color: 'var(--text-secondary)' }}>
                          {primary.prescriptions.identified_risks.map((risk, idx) => (
                            <li key={idx} style={{ marginBottom: 4 }}>{risk}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Grounded Narrative Explanation */}
                    <div className="narrative-box">
                      <div className="narrative-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Sparkles size={15} color="var(--color-primary)" />
                          <span>Sintesis Laporan & Pertimbangan Agronomi</span>
                        </div>
                        <span className="badge badge-neutral" style={{ fontSize: 10 }}>Terikat Fakta Agronomi</span>
                      </div>
                      <div style={{ whiteSpace: 'pre-line' }}>{primary.narrative_explanation}</div>
                    </div>
                  </div>

                  {/* Quick Alternative Choices */}
                  {result.alternatives && result.alternatives.length > 0 && (
                    <div>
                      <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, color: 'var(--text-secondary)' }}>
                        Pilihan Rotasi / Alternatif Pendukung
                      </h3>
                      <div className="alt-crops-grid">
                        {result.alternatives.map(alt => (
                          <div key={alt.crop_id} className="alt-crop-card">
                            <div>
                              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)' }}>Peringkat #{alt.rank}</div>
                              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{alt.crop_name}</div>
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                                Estimasi Laba: <span className="font-mono" style={{ fontWeight: 600 }}>{formatCurrency(alt.projected_profit_normal_idr)}</span>
                              </div>
                            </div>
                            <span className="badge badge-sky">Kelas {alt.fao_class}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Tab 2: Complete Crop Leaderboard (All 10 Crops) */}
              {activeTab === 'leaderboard' && (
                <div className="card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 700 }}>Peringkat Komparasi 10 Komoditas Terdaftar</h3>
                      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                        Urutan komputasi multi-kriteria (0.50 CSI + 0.30 Laba Riil - 0.20 Risiko)
                      </p>
                    </div>
                  </div>

                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Komoditas</th>
                          <th>Skor Gabungan</th>
                          <th>Kesesuaian FAO</th>
                          <th>Faktor Pembatas</th>
                          <th>Hasil Panen</th>
                          <th>Proyeksi Laba Bersih</th>
                        </tr>
                      </thead>
                      <tbody>
                        {allEvaluations.map(crop => (
                          <tr key={crop.crop_id} style={{ backgroundColor: crop.rank === 1 ? 'var(--color-primary-subtle)' : 'transparent' }}>
                            <td className="font-mono" style={{ fontWeight: 700 }}>
                              {crop.rank === 1 ? <span className="badge badge-green">#1</span> : `#${crop.rank}`}
                            </td>
                            <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{crop.crop_name}</td>
                            <td className="font-mono" style={{ fontWeight: 700, color: crop.composite_score > 0.7 ? 'var(--color-primary)' : 'var(--text-primary)' }}>
                              {crop.composite_score}
                            </td>
                            <td>
                              <span className={`badge ${crop.fao_class === 'S1' ? 'badge-green' : crop.fao_class === 'S2' ? 'badge-amber' : 'badge-rose'}`}>
                                {crop.fao_class} : {crop.fao_label}
                              </span>
                            </td>
                            <td style={{ color: 'var(--text-muted)' }}>{crop.limiting_factor}</td>
                            <td className="font-mono">{crop.yield_estimate_ton_ha} ton/ha</td>
                            <td className="font-mono" style={{ fontWeight: 600, color: crop.projected_profit_normal_idr > 0 ? 'var(--color-primary)' : 'var(--color-rose)' }}>
                              {formatCurrency(crop.projected_profit_normal_idr)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Tab 3: Detailed Agronomic Indices & Hydrology */}
              {activeTab === 'indices' && indices && (
                <div className="card">
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Indeks Bio-Fisik Lahan & Neraca Air</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
                    <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Gauge size={16} color="var(--color-primary)" />
                        <span>Vapor Pressure Deficit (VPD)</span>
                      </div>
                      <div className="font-mono" style={{ fontSize: 24, fontWeight: 800, color: 'var(--color-primary)' }}>
                        {indices.vpd_kpa} kPa
                      </div>
                      <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.5 }}>
                        Dihitung menggunakan persamaan Tetens berdasarkan suhu udara rata-rata ({formData.mean_air_temp} °C) dan kelembapan relatif ({formData.mean_rh}%). Ambang batas optimal tanaman hortikultura dan palawija tropis berada pada rentang 0.45 hingga 1.25 kPa.
                      </p>
                    </div>

                    <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <CloudRain size={16} color="var(--color-sky)" />
                        <span>Neraca Air Lahan Kumulatif</span>
                      </div>
                      <div className="font-mono" style={{ fontSize: 24, fontWeight: 800, color: indices.water_balance_mm >= 0 ? 'var(--color-sky)' : 'var(--color-rose)' }}>
                        {indices.water_balance_mm >= 0 ? `+${indices.water_balance_mm}` : indices.water_balance_mm} mm
                      </div>
                      <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.5 }}>
                        Selisih antara total curah hujan 30 hari ({formData.total_rainfall} mm) dengan evapotranspirasi acuan FAO-56 Penman-Monteith ({indices.reference_et0_mm} mm).
                        {indices.water_balance_mm >= 0 ? ' Lahan berada dalam status surplus air, cocok untuk tanaman yang membutuhkan hidrologi basah.' : ' Lahan mengalami defisit air, diperlukan irigasi tambahan.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card state-box">
              <Sprout className="state-icon" />
              <h3 style={{ fontSize: 16, fontWeight: 700 }}>Belum ada hasil evaluasi</h3>
              <p style={{ marginTop: 6, fontSize: 13, color: 'var(--text-muted)' }}>
                Pilih profil lahan di panel sebelah kiri atau sesuaikan slider telemetri, lalu klik tombol Evaluasi.
              </p>
            </div>
          )}
        </main>
      </div>

      {/* Catalog Knowledge Base Modal */}
      {catalogOpen && (
        <div className="modal-overlay" onClick={() => setCatalogOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <BookOpen size={18} color="var(--color-primary)" />
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>Basis Pengetahuan 17 Komoditas Pertanian Tropis (FAO EcoCrop)</h3>
              </div>
              <button
                className="btn btn-secondary btn-icon"
                onClick={() => setCatalogOpen(false)}
                aria-label="Tutup jendela katalog"
              >
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              {/* Search Bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                <Search size={16} color="var(--text-muted)" />
                <input
                  type="text"
                  placeholder="Cari komoditas atau kategori (misal: padi, sayuran, palawija)..."
                  value={catalogSearch}
                  onChange={e => setCatalogSearch(e.target.value)}
                  style={{ width: '100%', background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: 13 }}
                />
              </div>

              {catalogLoading ? (
                <div style={{ padding: 40, textAlign: 'center' }}>
                  <div className="spinner" style={{ margin: '0 auto 10px', borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
                  <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Memuat basis pengetahuan tanaman...</span>
                </div>
              ) : (
                <div className="table-wrapper">
                  <table className="data-table font-mono">
                    <thead>
                      <tr>
                        <th>Komoditas</th>
                        <th>Kategori</th>
                        <th>Suhu Optimal</th>
                        <th>pH Optimal</th>
                        <th>Air VWC Optimal</th>
                        <th>Siklus Panen</th>
                        <th>Yield Acuan</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCatalog.map(crop => (
                        <tr key={crop.crop_id}>
                          <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{crop.name}</td>
                          <td>
                            <span className="badge badge-neutral">{crop.category}</span>
                          </td>
                          <td>{crop.optimal_temp_c[0]} - {crop.optimal_temp_c[1]} °C</td>
                          <td>{crop.optimal_ph[0]} - {crop.optimal_ph[1]}</td>
                          <td>{crop.optimal_moisture_vwc[0]} - {crop.optimal_moisture_vwc[1]} %</td>
                          <td>{crop.growth_duration_days} hari</td>
                          <td>{crop.yield_normal_ton_ha} ton/ha</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
