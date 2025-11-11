# 🧠 Forensik Analisis Gambar Ijazah (Python)

Program ini digunakan untuk menganalisis keaslian dokumen hasil scan, seperti ijazah, sertifikat, atau dokumen resmi lainnya, menggunakan teknik forensik digital berbasis citra (image forensics).

Analisis yang dilakukan meliputi:
- 🔍 Metadata EXIF
- 🎛️ Noise / tekstur digital
- 💡 Kecerahan (Brightness Consistency)
- ✂️ Tepi / Edge Consistency
- 📝 Konsistensi teks (OCR)
- ⚠️ Error Level Analysis (ELA)

---

## ⚙️ Prasyarat

Pastikan sistem kamu sudah terinstal:

### 1. Python 3.10+
Program ini dikembangkan dan diuji menggunakan Python 3.10.  
Periksa versi Python kamu dengan:

```bash
python3 --version
```

### 2. Instalasi Dependensi Sistem
Beberapa modul membutuhkan library eksternal. Jalankan perintah berikut di terminal Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install python3-opencv
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-ind
```

`tesseract-ocr` digunakan untuk membaca teks dari gambar (OCR).  
`tesseract-ocr-ind` menambahkan dukungan bahasa Indonesia.

---

## 📦 Instalasi Modul Python

Sebelum menjalankan program, install semua pustaka Python yang dibutuhkan:

```bash
python3 -m pip install exifread pytesseract opencv-python Pillow matplotlib numpy
```

---

## 🚀 Cara Menjalankan Program

1. Simpan file Python, misalnya dengan nama:
   ```bash
   digital_forensic_scan_ijazah.py
   ```

2. Jalankan program di terminal:
   ```bash
   python3 digital_forensic_scan_ijazah.py
   ```

3. Masukkan nama file gambar yang akan dianalisis:
   ```bash
   Masukkan nama file gambar (misal: ijazah.jpg): ijazah_s2_eko_heri.jpg
   ```

---

## 🧩 Hasil Analisis yang Ditampilkan

Program akan menampilkan hasil analisis sebagai berikut:

| No | Jenis Analisis | Deskripsi |
|----|----------------|------------|
| 1️⃣ | Metadata EXIF | Menampilkan informasi kamera atau software pembuat file |
| 2️⃣ | Noise Analysis | Mendeteksi tingkat noise — bisa menunjukkan hasil edit digital |
| 3️⃣ | Brightness Consistency | Memeriksa pencahayaan keseluruhan dokumen |
| 4️⃣ | Edge Consistency | Menganalisis jumlah tepi (indikasi potongan digital) |
| 5️⃣ | Text Region Consistency (OCR) | Mengecek keterbacaan dan kejelasan teks |
| 6️⃣ | Error Level Analysis (ELA) | Menyorot area gambar dengan tingkat kompresi tidak konsisten |

---

## 🧾 Contoh Output

```bash
=== [1] Metadata Analysis ===
Tidak ada metadata EXIF ditemukan.

=== [2] Noise / Texture Analysis ===
Rata-rata intensitas noise: 2.66
→ Noise rendah, kemungkinan hasil scan murni.

=== [3] Brightness Consistency Analysis ===
Rata-rata kecerahan: 224.76
→ Terang (kemungkinan hasil scan normal).

=== [4] Edge Consistency Analysis ===
Kepadatan tepi (edge density): 4.12%
→ Jumlah tepi normal untuk dokumen cetak.

=== [5] Text Region Consistency ===
Akurasi OCR rata-rata: 89.22
→ Teks terbaca jelas dan seragam.

=== [6] Error Level Analysis (ELA) ===
ELA menunjukkan perbedaan normal — tidak ada indikasi manipulasi.

=== [Kesimpulan Akhir] ===
→ Dokumen kemungkinan hasil scan asli.
```

---

## 🖼️ Tampilan Visual

Program akan menampilkan beberapa jendela visual:
- **Asli** – gambar sumber
- **Peta Noise** – area dengan noise tinggi
- **Peta Edge** – deteksi tepi
- **Peta ELA** – hasil analisis tingkat kompresi
- **Histogram Kecerahan** – distribusi intensitas cahaya

---

## 📚 Lisensi

Proyek ini dirilis di bawah lisensi **MIT License**.  
Bebas digunakan untuk riset, edukasi, atau integrasi ke proyek forensik digital lainnya.
