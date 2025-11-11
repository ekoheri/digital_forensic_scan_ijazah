import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import exifread
import matplotlib.pyplot as plt
import pytesseract
from pytesseract import Output

# --- 1. Metadata Analysis ---
def analyze_metadata(path):
    print("=== [1] Metadata Analysis ===")
    with open(path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        if not tags:
            print("Tidak ada metadata EXIF ditemukan.")
        else:
            for tag in tags.keys():
                print(f"{tag}: {tags[tag]}")

# --- 2. Noise / Texture Analysis ---
def analyze_noise(path):
    print("\n=== [2] Noise / Texture Analysis ===")
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Gagal membaca gambar.")
        return None, None, None, 0
    
    blur = cv2.GaussianBlur(img, (5,5), 0)
    noise_map = cv2.absdiff(img, blur)
    amplified = cv2.convertScaleAbs(noise_map, alpha=5, beta=0)

    mean_noise = np.mean(noise_map)
    print(f"Rata-rata intensitas noise: {mean_noise:.2f}")
    if mean_noise < 3:
        print("→ Noise rendah, kemungkinan hasil scan murni.")
    elif mean_noise > 8:
        print("→ Noise tinggi/tidak seragam, kemungkinan ada bagian digital edit.")
    else:
        print("→ Noise tampak wajar dan seragam.")

    return img, amplified, noise_map, mean_noise

# --- 3. Brightness / Illumination Consistency ---
def analyze_brightness(path):
    print("\n=== [3] Brightness Consistency Analysis ===")
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    brightness = np.mean(img)
    print(f"Rata-rata kecerahan: {brightness:.2f}")
    if brightness > 240:
        print("→ Terlalu terang, kemungkinan hasil edit atau foto dengan flash.")
    elif brightness > 200:
        print("→ Terang (kemungkinan hasil scan normal).")
    elif brightness < 50:
        print("→ Sangat gelap, mungkin hasil foto kurang pencahayaan.")
    else:
        print("→ Pencahayaan normal.")
    return img, brightness

# --- 4. Edge Consistency Analysis ---
def analyze_edges(path):
    print("\n=== [4] Edge Consistency Analysis ===")
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(img, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size * 100
    print(f"Kepadatan tepi (edge density): {edge_density:.2f}%")

    if edge_density < 2:
        print("→ Sedikit tepi terdeteksi (dokumen bersih atau hasil scan murni).")
    elif edge_density > 10:
        print("→ Banyak tepi tajam — periksa kemungkinan penambahan digital (tanda tangan, foto).")
    else:
        print("→ Jumlah tepi normal untuk dokumen cetak.")
    return edges, edge_density

# --- 5. Text Region Consistency (OCR) ---
def analyze_text(path):
    print("\n=== [5] Text Region Consistency ===")
    img = cv2.imread(path)
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    confs = [float(c) for c in d['conf'] if c != '-1']
    if not confs:
        print("Tidak ada teks terdeteksi.")
        return 0
    avg_conf = np.mean(confs)
    print(f"Akurasi OCR rata-rata: {avg_conf:.2f}")
    if avg_conf < 60:
        print("→ Ada teks kabur/tidak seragam — periksa bagian itu.")
    else:
        print("→ Teks terbaca jelas dan seragam.")
    return avg_conf

# --- 6. Error Level Analysis (ELA) ---
def analyze_ela(path, quality=90):
    print("\n=== [6] Error Level Analysis (ELA) ===")
    try:
        original = Image.open(path).convert('RGB')
        tmp_path = "_tmp_ela.jpg"
        original.save(tmp_path, 'JPEG', quality=quality)

        recompressed = Image.open(tmp_path)
        diff = ImageChops.difference(original, recompressed)

        # Perkuat perbedaan agar lebih kelihatan
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff

        ela_image = ImageEnhance.Brightness(diff).enhance(scale)
        ela_np = np.array(ela_image)

        mean_diff = np.mean(ela_np)
        print(f"Rata-rata perbedaan ELA: {mean_diff:.2f}")

        if mean_diff < 5:
            print("→ Tidak ada indikasi edit digital (ELA rendah).")
        elif mean_diff < 15:
            print("→ Sedikit variasi ELA — kemungkinan hasil kompresi ulang biasa.")
        else:
            print("→ Perbedaan ELA signifikan — kemungkinan ada bagian yang dimodifikasi.")
        return ela_np, mean_diff
    except Exception as e:
        print("Gagal melakukan analisis ELA:", e)
        return None, 0

# --- MAIN ---
if __name__ == "__main__":
    path = input("Masukkan nama file gambar (misal: ijazah.jpg): ").strip()

    analyze_metadata(path)
    img, amplified, noise_map, mean_noise = analyze_noise(path)
    bright_img, mean_brightness = analyze_brightness(path)
    edges, edge_density = analyze_edges(path)
    avg_conf = analyze_text(path)
    ela_img, mean_ela = analyze_ela(path)

    # === Kesimpulan akhir ===
    
    print("\n=== [Kesimpulan Akhir] ===")
    if mean_noise < 5 and 200 < mean_brightness < 245 and edge_density < 8 and avg_conf > 60 and mean_ela < 10:
        print("→ Tidak ditemukan tanda-tanda manipulasi digital. Dokumen kemungkinan hasil scan asli.")
    elif mean_ela > 15 or mean_noise > 8 or edge_density > 10:
        print("→ Perlu pemeriksaan lebih lanjut, ada kemungkinan area yang dimodifikasi (cek hasil ELA).")
    else:
        print("→ Dokumen tampak normal, tapi lakukan analisis lanjutan bila perlu.")

    print("\nAnalisis selesai. Menampilkan hasil visual...\n")

    # === Tampilkan histogram (matplotlib) ===
    hist = cv2.calcHist([bright_img],[0],None,[256],[0,256])
    plt.title("Histogram Kecerahan Gambar")
    plt.xlabel("Intensitas (0=gelap, 255=terang)")
    plt.ylabel("Jumlah Piksel")
    plt.plot(hist)
    plt.show()

    # === Tampilkan hasil visual (cv2) ===
    if img is not None:
        cv2.namedWindow("Asli", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Peta Noise (Amplified)", cv2.WINDOW_NORMAL)
        cv2.namedWindow("Peta Tepi (Edges)", cv2.WINDOW_NORMAL)

        cv2.resizeWindow("Asli", 600, 400)
        cv2.resizeWindow("Peta Noise (Amplified)", 600, 400)
        cv2.resizeWindow("Peta Tepi (Edges)", 600, 400)

        scale = 0.3
        display_img = cv2.resize(img, None, fx=scale, fy=scale)
        display_noise = cv2.resize(amplified, None, fx=scale, fy=scale)
        display_edges = cv2.resize(edges, None, fx=scale, fy=scale)

        cv2.imshow("Asli", display_img)
        cv2.imshow("Peta Noise (Amplified)", display_noise)
        cv2.imshow("Peta Tepi (Edges)", display_edges)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cv2.waitKey(1)
