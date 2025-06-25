# SPK Rekomendasi Laptop

Aplikasi web Sistem Pendukung Keputusan (SPK) untuk memberikan rekomendasi laptop terbaik berdasarkan kriteria dan filter yang diinginkan. Dibangun dengan Python Flask dan menggunakan metode SAW (Simple Additive Weighting) untuk perankingan.

## Fitur Utama
- Filter laptop berdasarkan merek, harga, RAM, SSD, layar, prosesor, baterai, dan tahun rilis.
- Rekomendasi laptop terbaik dengan perhitungan skor otomatis.
- Tampilan responsif dan modern, nyaman di desktop maupun mobile.
- Download file (misal: template data, manual, dsb) melalui tombol unduh.

## Instalasi & Menjalankan
1. **Clone repository atau salin source code ke komputer Anda.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Pastikan file data_laptop.xlsx sudah ada di folder utama.**
4. **Jalankan aplikasi:**
   ```bash
   python app.py
   ```
5. **Buka browser dan akses:**
   ```
   http://localhost:5000
   ```

## Struktur File Penting
- `app.py` : Backend utama Flask
- `templates/index.html` : Halaman filter & form
- `templates/results.html` : Halaman hasil rekomendasi
- `data_laptop.xlsx` : Data laptop (format kolom sesuai contoh di aplikasi)
- `static/` : Tempat file yang bisa diunduh user (misal: template Excel, manual, dsb)

## Menambah File Unduhan
1. Letakkan file yang ingin diunduh ke folder `static/`.
2. Edit `templates/index.html` dan ubah nama file pada tombol unduh:
   ```html
   <a href="{{ url_for('static', filename='nama_file.ext') }}" class="download-btn" download>Unduh File</a>
   ```

## Lisensi
Aplikasi ini bebas digunakan untuk pembelajaran dan pengembangan lebih lanjut.
