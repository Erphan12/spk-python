from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import re

# =====================================================
# Inisialisasi aplikasi Flask
# =====================================================
app = Flask(__name__)

# =====================================================
# Fungsi untuk memuat data dari file Excel
# Data yang dimuat harus memiliki kolom-kolom tertentu agar aplikasi berjalan dengan baik
# =====================================================
def load_data():
    try:
        # Membaca file Excel bernama 'data_laptop.xlsx'
        df = pd.read_excel("data_laptop.xlsx")
        # Daftar kolom yang wajib ada di file Excel
        required_cols = [
            'Model', 'Harga (juta)', 'RAM (GB)', 'SSD (GB)', 'Ukuran Layar (inch)',
            'Prosesor', 'Generasi Prosesor', 'VGA', 'Kapasitas Baterai (Wh)'
        ]
        # Mengecek apakah semua kolom yang dibutuhkan ada di data
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Kolom '{col}' tidak ditemukan di data_laptop.xlsx")
        return df
    except Exception as e:
        # Jika gagal, tampilkan pesan error dan kembalikan DataFrame kosong
        print(f"Gagal load data: {e}")
        return pd.DataFrame()

# =====================================================
# Fungsi untuk mengambil merek dari nama model laptop
# Contoh: 'Asus Vivobook 14' -> 'Asus'
# =====================================================
def extract_brand(model):
    return str(model).split()[0] if isinstance(model, str) else 'Unknown'

# =====================================================
# Fungsi untuk menentukan jenis prosesor (Intel, AMD, atau Lainnya)
# Berdasarkan string pada kolom 'Prosesor'
# =====================================================
def extract_processor_type(proc):
    if 'Intel' in str(proc):
        return 'Intel'
    elif 'AMD' in str(proc) or 'Ryzen' in str(proc):
        return 'AMD'
    else:
        return 'Lainnya'

# =====================================================
# Fungsi untuk menghitung skor prosesor berdasarkan nama dan serinya
# Skor dasar diambil dari tipe prosesor, bonus diambil dari seri (misal: H, U, G, dsb)
# =====================================================
def extract_processor_score(text):
    # Skor dasar untuk tipe prosesor
    prosesor_base_score = {
        "Celeron": 1, "Pentium": 2, "Core i3": 3, "Core i5": 4, "Core i7": 5, "Core i9": 6,
        "Ryzen 3": 3, "Ryzen 5": 4, "Ryzen 7": 5, "Ryzen 9": 6
    }
    # Bonus skor berdasarkan seri prosesor
    seri_bonus = {"U": 0, "G": 0.2, "H": 0.8, "HQ": 1.0, "HX": 1.2, "T": -0.2, "P": 0.3, "HS": 0.5, "": 0}
    if pd.isna(text):
        return 4.0  # Nilai default jika data kosong
    base_score = 0
    text = str(text).lower()
    # Cari skor dasar
    for base in prosesor_base_score:
        if base.lower() in text:
            base_score = prosesor_base_score[base]
            break
    # Cari bonus berdasarkan seri
    pattern = r'\b([UGHP]|H[QX]?|HS|P)\b'
    seri_match = re.search(pattern, text.upper())
    seri = seri_match.group(1) if seri_match else ""
    bonus = seri_bonus.get(seri, 0)
    return base_score + bonus

# =====================================================
# Fungsi untuk menghitung skor VGA (kartu grafis)
# Skor didasarkan pada jenis VGA, semakin tinggi semakin baik
# =====================================================
def extract_vga_score(text):
    vga_scores = {
        "Intel UHD Graphics 600": 1,
        "Intel UHD Graphics 605": 2,
        "Intel UHD Graphics": 3,
        "Intel Iris Xe": 4,
        "AMD Radeon Vega 8": 5,
        "NVIDIA GeForce MX350": 6,
        "NVIDIA RTX 3050": 7,
        "NVIDIA GeForce RTX 3050": 7,
        "NVIDIA RTX 3060": 9,
        "NVIDIA GeForce RTX 3060": 9
    }
    # Cek apakah nama VGA ada di kamus skor
    for k, v in vga_scores.items():
        if k.lower() in str(text).lower():
            return v
    # Jika tidak ditemukan, gunakan aturan umum
    if 'NVIDIA' in str(text):
        return 6
    if 'AMD' in str(text):
        return 5
    if 'Iris' in str(text):
        return 4
    if 'UHD' in str(text):
        return 3
    return 3.0  # Default

# =====================================================
# Fungsi untuk pra-pemrosesan data
# Menambah kolom baru (Merek, Jenis Prosesor, Skor Prosesor, Skor VGA)
# dan mengubah tipe data kolom numerik
# =====================================================
def preprocess(df):
    if df.empty:
        return df
    df = df.copy()
    # Tambahkan kolom merek
    df['Merek'] = df['Model'].apply(extract_brand)
    # Tambahkan kolom jenis prosesor
    df['Jenis Prosesor'] = df['Prosesor'].apply(extract_processor_type)
    # Tambahkan kolom skor prosesor
    df['Skor Prosesor'] = df['Prosesor'].apply(extract_processor_score)
    # Tambahkan kolom skor VGA
    df['Skor VGA'] = df['VGA'].apply(extract_vga_score)
    # Konversi kolom numerik ke float, isi NaN dengan 0
    for col in ['Harga (juta)', 'RAM (GB)', 'SSD (GB)', 'Ukuran Layar (inch)', 'Generasi Prosesor', 'Kapasitas Baterai (Wh)']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# =====================================================
# Kriteria penilaian dan jenisnya (cost/benefit)
# 'cost' artinya semakin kecil nilainya semakin baik (misal harga)
# 'benefit' artinya semakin besar nilainya semakin baik (misal RAM)
# =====================================================
criteria = {
    "Harga (juta)": "cost",
    "RAM (GB)": "benefit",
    "SSD (GB)": "benefit",
    "Ukuran Layar (inch)": "benefit",
    "Generasi Prosesor": "benefit",
    "Kapasitas Baterai (Wh)": "benefit",
    "Skor VGA": "benefit",
    "Skor Prosesor": "benefit"
}

# =====================================================
# Bobot untuk setiap kriteria (total harus 1.0)
# Bobot menunjukkan seberapa penting kriteria tersebut
# =====================================================
weights = {
    "Harga (juta)": 0.18,           # Harga lebih murah lebih baik
    "RAM (GB)": 0.2,                # RAM lebih besar lebih baik
    "SSD (GB)": 0.15,               # SSD lebih besar lebih baik
    "Ukuran Layar (inch)": 0.08,    # Layar lebih besar lebih baik
    "Generasi Prosesor": 0.1,       # Generasi prosesor lebih baru lebih baik
    "Kapasitas Baterai (Wh)": 0.1,  # Baterai lebih besar lebih baik
    "Skor VGA": 0.1,                # VGA lebih tinggi lebih baik
    "Skor Prosesor": 0.09           # Prosesor lebih tinggi lebih baik
}

# =====================================================
# Fungsi utama metode SAW (Simple Additive Weighting)
# Melakukan normalisasi data dan menghitung skor akhir setiap laptop
# =====================================================
def saw_method(df, criteria, weights):
    if df.empty:
        # Jika data kosong, kembalikan DataFrame kosong
        return pd.DataFrame(columns=['Model', 'Skor Akhir'])
    df_work = df.copy()
    df_normalized = df_work.copy()
    # Normalisasi setiap kriteria
    for col, ctype in criteria.items():
        if df_work[col].max() == 0 and df_work[col].min() == 0:
            df_normalized[col] = 0
            continue
        min_val = max(df_work[col].min(), 0.001)
        max_val = max(df_work[col].max(), 0.001)
        if ctype == 'benefit':
            # Untuk benefit: nilai / nilai maksimum
            df_normalized[col] = df_work[col] / max_val
        else:
            # Untuk cost: nilai minimum / nilai
            df_normalized[col] = min_val / df_work[col]
            df_normalized[col] = df_normalized[col].replace([np.inf, -np.inf], 0)
    # Hitung skor akhir dengan menjumlahkan hasil normalisasi dikali bobot
    df_normalized['Skor Akhir'] = sum(df_normalized[col] * weights[col] for col in criteria)
    # Urutkan dari skor tertinggi ke terendah
    return df_normalized[['Model', 'Skor Akhir']].sort_values(by='Skor Akhir', ascending=False)

# =====================================================
# Fungsi untuk memfilter data sesuai input/filter dari user
# Setiap filter akan mempersempit hasil pencarian laptop
# =====================================================
def apply_filters(data, filters):
    filtered = data.copy()
    # Filter berdasarkan merek laptop
    if filters.get('brand') and filters['brand'] != 'Semua':
        filtered = filtered[filtered['Merek'] == filters['brand']]
    # Filter berdasarkan rentang harga
    min_price = float(filters.get('min_price', 0))
    max_price = float(filters.get('max_price', 100))
    filtered = filtered[(filtered['Harga (juta)'] >= min_price) & (filtered['Harga (juta)'] <= max_price)]
    # Filter berdasarkan RAM
    if filters.get('ram') != 'Semua' and filters.get('ram'):
        filtered = filtered[filtered['RAM (GB)'] == int(filters['ram'])]
    # Filter berdasarkan SSD
    if filters.get('ssd') and filters['ssd'] != 'Semua':
        if filters['ssd'] == '512+':
            filtered = filtered[filtered['SSD (GB)'] >= 512]
        else:
            filtered = filtered[filtered['SSD (GB)'] == int(filters['ssd'])]
    # Filter berdasarkan ukuran layar
    if filters.get('screen_size') and filters['screen_size'] != 'Semua':
        filtered = filtered[filtered['Ukuran Layar (inch)'] == float(filters['screen_size'])]
    # Filter berdasarkan jenis prosesor
    if filters.get('processor_type') and filters['processor_type'] != 'Semua':
        filtered = filtered[filtered['Jenis Prosesor'] == filters['processor_type']]
    # Filter berdasarkan kapasitas baterai
    if filters.get('battery') and filters['battery'] != 'Semua':
        if filters['battery'] == '50+':
            filtered = filtered[filtered['Kapasitas Baterai (Wh)'] >= 50]
        else:
            filtered = filtered[filtered['Kapasitas Baterai (Wh)'] == int(filters['battery'])]
    # Filter berdasarkan generasi prosesor
    if filters.get('processor_gen') and filters['processor_gen'] != 'Semua':
        filtered = filtered[filtered['Generasi Prosesor'] == int(filters['processor_gen'])]
    return filtered

# =====================================================
# Route halaman utama (index)
# Menampilkan form filter dan pilihan laptop
# =====================================================
@app.route('/')
def index():
    df = preprocess(load_data())
    if df.empty:
        return "Data gagal dimuat. Cek file Excel."
    # Nilai default untuk filter
    filters = {
        'brand': 'Semua',
        'min_price': '0',
        'max_price': '100',
        'ram': 'Semua',
        'ssd': 'Semua',
        'screen_size': 'Semua',
        'processor_type': 'Semua',
        'battery': 'Semua',
        'processor_gen': 'Semua'
    }
    # Kirim data ke template index.html untuk ditampilkan
    return render_template("index.html",
                           filters=filters,
                           brands=['Semua'] + sorted(df['Merek'].unique().tolist()),
                           ram_sizes=['Semua'] + sorted(df['RAM (GB)'].unique().tolist()),
                           ssd_sizes=['Semua', '256', '512', '512+', '1024'],
                           screen_sizes=['Semua'] + sorted(df['Ukuran Layar (inch)'].unique().tolist()),
                           processor_types=['Semua'] + sorted(df['Jenis Prosesor'].unique().tolist()),
                           battery_capacities=['Semua', '30', '40', '50', '50+', '60', '70'],
                           processor_gens=['Semua'] + sorted(df['Generasi Prosesor'].unique().tolist())
                           )

# =====================================================
# Route untuk rekomendasi laptop berdasarkan filter dan perankingan SAW
# Proses:
# 1. Data difilter sesuai input user
# 2. Data di-ranking dengan metode SAW
# 3. Hasil 10 teratas ditampilkan di halaman hasil
# =====================================================
@app.route('/recommend', methods=['POST'])
def recommend():
    df = preprocess(load_data())
    if df.empty:
        return "Data kosong"
    # Ambil filter dari form yang dikirim user
    filters = {key: request.form.get(key) for key in [
        'brand', 'min_price', 'max_price', 'ram', 'ssd',
        'screen_size', 'processor_type', 'battery', 'processor_gen']}
    # Filter data
    filtered = apply_filters(df, filters)
    # Ranking dengan metode SAW
    ranking = saw_method(filtered, criteria, weights)
    # Gabungkan hasil ranking dengan data asli untuk menampilkan detail
    result = pd.merge(ranking, df, on='Model', how='left')
    # Format harga agar lebih mudah dibaca
    result['Harga (juta)'] = result['Harga (juta)'].apply(lambda x: f"Rp {x:.1f} juta" if x > 0 else "N/A")
    # Kirim hasil ke template results.html
    return render_template("results.html", recommendations=result.head(10).to_dict('records'))

# =====================================================
# Menjalankan aplikasi Flask jika file ini dijalankan langsung
# =====================================================
if __name__ == '__main__':
    app.run(debug=True)
