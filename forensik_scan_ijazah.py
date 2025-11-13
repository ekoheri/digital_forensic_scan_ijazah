import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import matplotlib.pyplot as plt
import os
from pytesseract import Output
import exifread

# --- 1. Error Level Analysis (ELA) ---
def analyze_ela_local(path, quality=90, block_size=16):
    print("\n=== [1] ELA Lokal (Revisi Final: Analisis Variansi) ===")
    from PIL import Image, ImageChops, ImageEnhance
    import numpy as np
    import cv2
    import os

    try:
        original = Image.open(path).convert('RGB')
        tmp_path = "_tmp_ela_local.jpg"
        original.save(tmp_path, 'JPEG', quality=quality)
        recompressed = Image.open(tmp_path)

        diff = ImageChops.difference(original, recompressed)
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1

        scale = 150.0 / max_diff 
        ela_image = ImageEnhance.Brightness(diff).enhance(scale)
        ela_gray = np.array(ela_image.convert('L'), dtype=np.float32)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        ela_gray_clahe = clahe.apply(ela_gray.astype(np.uint8)).astype(np.float32)

        h, w = ela_gray_clahe.shape
        suspicious_mask = np.zeros_like(ela_gray_clahe, dtype=np.uint8)
        block_vars = [] # Mengubah dari mean menjadi variance

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = ela_gray_clahe[y:y+block_size, x:x+block_size]
                var_val = np.var(block) # Mengukur Variansi
                block_vars.append(var_val)

        mean_global_var = np.mean(block_vars)
        std_global_var = np.std(block_vars)
        
        # Ambang batas ELA: 3.0 * std_global_var
        threshold = mean_global_var + 3.0 * std_global_var

        print(f"Rata-rata global VARIANSI ELA per-blok: {mean_global_var:.2f}")
        print(f"Ambang batas mencurigakan (> {threshold:.2f})")

        # Buat masker kecurigaan berdasarkan ambang batas global
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = ela_gray_clahe[y:y+block_size, x:x+block_size]
                if np.var(block) > threshold:
                    suspicious_mask[y:y+block_size, x:x+block_size] = 255
        
        percent_suspicious = np.sum(suspicious_mask > 0) / suspicious_mask.size * 100
        print(f"Luas area mencurigakan: {percent_suspicious:.2f}% dari total gambar.")

        os.remove(tmp_path)
        return ela_gray_clahe, suspicious_mask, suspicious_mask > 0
    except Exception as e:
        print("Gagal melakukan analisis ELA:", e)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        dummy_mask = np.zeros((10, 10), dtype=bool) 
        return np.zeros((h, w), dtype=np.float32), np.zeros((h, w), dtype=np.uint8), dummy_mask # Pastikan mengembalikan ukuran yang benar

# --- 2. Noise / Texture Analysis (Revisi Final: Ambang Batas Ditingkatkan) ---
def analyze_noise_local(path, block_size=16):
    print("\n=== [2] Analisis Noise Lokal (Revisi Final) ===")
    import cv2
    import numpy as np

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Gagal membaca gambar.")
        return None, None, None

    # 1. Deteksi Tepi untuk membuat masker
    edges = cv2.Canny(img, 50, 150)
    edge_mask = edges > 0

    # 2. Hitung Peta Noise
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    noise_map = cv2.absdiff(img, blur).astype(np.float32)
    amplified_noise = noise_map * 8.0 

    h, w = amplified_noise.shape
    local_mean = np.zeros_like(amplified_noise)
    background_block_means = []

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = amplified_noise[y:y+block_size, x:x+block_size]
            edge_block = edge_mask[y:y+block_size, x:x+block_size]
            mean_val = np.mean(block)
            
            # Hanya hitung rata-rata noise dari blok yang didominasi oleh latar belakang
            if np.sum(edge_block) / edge_block.size < 0.5:
                background_block_means.append(mean_val)
            
            local_mean[y:y+block_size, x:x+block_size] = mean_val

    if not background_block_means:
        print("Tidak ada area latar belakang yang cukup untuk analisis noise.")
        return img, local_mean, np.zeros_like(img, dtype=bool)

    # Hitung statistik hanya dari blok latar belakang
    mean_global = np.mean(background_block_means)
    std_global = np.std(background_block_means)

    # Ambang batas Noise FINAL: 4.0 * std_global
    threshold = mean_global + 4.0 * std_global 

    print(f"Rata-rata intensitas noise Latar Belakang: {mean_global:.2f}")
    print(f"Ambang batas mencurigakan (> {threshold:.2f})")

    # Masker kecurigaan
    suspicious_mask = (local_mean > threshold).astype(np.uint8)
    percent_suspicious = np.sum(suspicious_mask > 0) / suspicious_mask.size * 100
    print(f"Luas area mencurigakan: {percent_suspicious:.2f}% dari total gambar.")

    return img, local_mean, suspicious_mask > 0

# --- 3. FUNGSI Breakness ---
def analyze_brightness_local(path, block_size=16):
    print("\n=== [3] Analisis Kecerahan Lokal (Revisi Final) ===")
    import cv2
    import numpy as np

    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Gagal membaca gambar.")
        return None, None

    # 1. Deteksi Tepi untuk membuat masker (Sama seperti Analisis Noise)
    edges = cv2.Canny(img, 50, 150)
    edge_mask = edges > 0

    h, w = img.shape
    local_brightness_mean = np.zeros_like(img, dtype=np.float32)
    background_block_means = []

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = img[y:y+block_size, x:x+block_size]
            edge_block = edge_mask[y:y+block_size, x:x+block_size]
            mean_val = np.mean(block)
            
            # Hanya kumpulkan data dari blok yang didominasi LATAR BELAKANG (< 50% adalah tepi)
            if np.sum(edge_block) / edge_block.size < 0.5:
                background_block_means.append(mean_val)
            
            local_brightness_mean[y:y+block_size, x:x+block_size] = mean_val

    if not background_block_means:
        print("Tidak ada area latar belakang yang cukup untuk analisis kecerahan.")
        return local_brightness_mean, np.zeros_like(img, dtype=bool)

    # Hitung statistik hanya dari blok latar belakang
    mean_global_bg = np.mean(background_block_means)
    std_global_bg = np.std(background_block_means)
    
    # Ambang batas Brightness FINAL: Ditingkatkan menjadi 3.5 * std_global
    # Ini mencari area kertas yang terlalu terang/gelap secara anomali
    factor = 3.5
    threshold_upper = mean_global_bg + factor * std_global_bg
    threshold_lower = mean_global_bg - factor * std_global_bg

    print(f"Rata-rata kecerahan latar belakang: {mean_global_bg:.2f}")
    print(f"Ambang batas anomali: ({threshold_lower:.2f} hingga {threshold_upper:.2f})")

    # Deteksi blok yang terlalu terang ATAU terlalu gelap
    suspicious_mask = np.logical_or(
        local_brightness_mean > threshold_upper,
        local_brightness_mean < threshold_lower
    ).astype(np.uint8)
    
    percent_suspicious = np.sum(suspicious_mask > 0) / suspicious_mask.size * 100
    print(f"Luas area anomali kecerahan: {percent_suspicious:.2f}% dari total gambar.")

    return local_brightness_mean, suspicious_mask > 0

# ----4. FUNGSI Analyse Metadata
def analyze_metadata(path):
    print("\n=== [4] Metadata Analysis ===")
    with open(path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        if not tags:
            print("Tidak ada metadata EXIF ditemukan.")
        else:
            for tag in tags.keys():
                print(f"{tag}: {tags[tag]}")

# --- 5. FUNGSI analyze_text_consistency (Direvisi untuk Output Masker) ---
def analyze_text_consistency(path, conf_threshold=50):
    print("\n=== [5] Analisis Konsistensi Teks (OCR) ===")
    import cv2
    import pytesseract
    from pytesseract import Output
    import numpy as np

    img = cv2.imread(path)
    if img is None:
        print("Gagal membaca gambar.")
        return 0, None

    h, w, _ = img.shape
    text_susp_mask = np.zeros((h, w), dtype=np.uint8) # Masker untuk visualisasi
    
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    
    total_words = 0
    suspicious_words_count = 0

    for i in range(len(d['conf'])):
        conf = float(d['conf'][i])
        text = d['text'][i].strip()
        
        if conf != -1 and len(text) > 1:
            total_words += 1
            
            # Jika confidence di bawah ambang batas (misalnya 50), tandai sebagai mencurigakan
            if conf < conf_threshold:
                suspicious_words_count += 1
                
                # Gambar kotak di masker pada lokasi kata mencurigakan
                (x, y, w_word, h_word) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                text_susp_mask[y:y + h_word, x:x + w_word] = 255 # Menandai area

    if total_words == 0:
        print("Tidak ada teks yang cukup terdeteksi.")
        return 0, None

    avg_conf = np.mean([float(c) for c in d['conf'] if c != '-1'])
    percent_suspicious_words = (suspicious_words_count / total_words) * 100
    
    print(f"Akurasi OCR rata-rata: {avg_conf:.2f}")
    print(f"Persentase Kata Mencurigakan (<{conf_threshold}%): {percent_suspicious_words:.2f}%")

    # Kembalikan persentase kata mencurigakan dan masker visual
    return percent_suspicious_words, text_susp_mask

# --- FUNGSI show_heatmaps (Revisi Final Padding) ---
def show_heatmaps(img, ela_heat, noise_heat, bright_heat, text_susp_mask, ela_susp, noise_susp, bright_susp, text_susp):
    # Ukuran figur diperbesar
    plt.figure(figsize=(18, 10))

    # 1. Gambar Asli
    plt.subplot(2,3,1)
    plt.title("1. Gambar Asli")
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis('off')

    # 2. ELA Heatmap
    plt.subplot(2,3,2)
    plt.title("2. ELA (Variansi)") 
    plt.imshow(ela_heat, cmap='hot')
    plt.axis('off')

    # 3. Noise Heatmap
    plt.subplot(2,3,3)
    plt.title("3. Noise (Texture)") 
    plt.imshow(noise_heat, cmap='hot')
    plt.axis('off')

    # 4. Brightness Heatmap
    plt.subplot(2,3,4)
    plt.title("4. Brightness (Lokal)") 
    plt.imshow(bright_heat, cmap='viridis') 
    plt.axis('off')
    
    # 5. Text Consistency Mask
    plt.subplot(2,3,5)
    plt.title("5. Teks Mencurigakan") 
    plt.imshow(text_susp_mask, cmap='gray') 
    plt.axis('off')
    
    # 6. Gabungan Area Mencurigakan Total
    plt.subplot(2,3,6)
    plt.title("6. Gabungan Total Anomali") 
    combined_ela_noise_bright = np.logical_or(np.logical_or(ela_susp, noise_susp), bright_susp)
    combined_total = np.logical_or(combined_ela_noise_bright, text_susp).astype(np.uint8) * 255
    plt.imshow(combined_total, cmap='gray')
    plt.axis('off')

    # 1. Gunakan h_pad yang sangat besar (misalnya 8.0)
    plt.tight_layout(w_pad=2.0, h_pad=8.0) 
    
    # 2. Tambahkan padding eksplisit di bagian atas untuk memberi ruang
    # top=0.95 adalah batas atas (1.0 adalah batas maksimal)
    plt.subplots_adjust(top=0.95)
    plt.show()

# --- MAIN ---   
if __name__ == "__main__":
    path = input("Masukkan nama file gambar (misal: ijazah.jpg): ").strip()

    img = cv2.imread(path)
    if img is None:
        print("File tidak ditemukan atau format tidak didukung.")
    else:
        # 1. Panggil semua fungsi analisis
        ela_heat, ela_susp_mask, ela_susp = analyze_ela_local(path)
        img_copy, noise_heat, noise_susp = analyze_noise_local(path)
        bright_heat, bright_susp = analyze_brightness_local(path)
        analyze_metadata(path)
        
        # Panggil fungsi Teks yang baru
        percent_suspicious_text, text_susp_mask = analyze_text_consistency(path) 
        
        # Buat masker boolean untuk Text Susp (diperlukan untuk np.logical_or)
        if text_susp_mask is not None:
             text_susp = (text_susp_mask > 0)
        else:
             # Gunakan array kosong/nol jika gagal, disamakan ukurannya dengan masker lain
             text_susp = np.zeros_like(ela_susp, dtype=bool) 
             # Pastikan ela_susp/noise_susp/bright_susp bukan None sebelum ini
             
        # 2. Logika Kesimpulan Forensik
        if ela_susp is not None and noise_susp is not None and bright_susp is not None:
            print("\n=== [Kesimpulan Forensik Akhir] ===")
            
            # a. Hitung Total Area Mencurigakan dari ELA, Noise, dan Brightness
            combined_ela_noise_bright = np.logical_or(np.logical_or(ela_susp, noise_susp), bright_susp)
            percent_area_total = np.sum(combined_ela_noise_bright) / combined_ela_noise_bright.size * 100
            
            # b. Hitung Skor Anomali Tertimbang
            # Bobot Teks: Menggunakan 0.1x persentase kata mencurigakan sebagai faktor bobot tambahan.
            # Ini memberikan bobot pada inkonsistensi teks tanpa mendominasi total area piksel.
            weighted_anomali_score = percent_area_total + (percent_suspicious_text * 0.1) 
            
            # c. Tetapkan Ambang Batas Forensik
            # Menggunakan 2.80% berdasarkan hasil eksperimen (nilai ini berada di antara Asli: 2.39% dan Edit: 3.01%)
            threshold_forensik = 2.80 

            # d. Cetak Kesimpulan
            if weighted_anomali_score > threshold_forensik: 
                print(f"**Status:** MODIFIKASI TERDETEKSI (Skor Anomali Tertimbang: {weighted_anomali_score:.2f}%)")
                print(f"→ Bukti kuat dari ELA/Noise/Brightness ({percent_area_total:.2f}%) dan Teks Mencurigakan ({percent_suspicious_text:.2f}%).")
                print(f"→ **Indikasi Kuat Manipulasi Digital.** Cek area yang ditunjukkan pada peta gabungan.")
            else:
                print(f"**Status:** KEMUNGKINAN ASLI (Skor Anomali Tertimbang: {weighted_anomali_score:.2f}%)")
                print(f"→ Area anomali minimal atau konsisten ({percent_area_total:.2f}%). Teks mencurigakan: {percent_suspicious_text:.2f}%.")
                print("→ **Tidak Ditemukan Bukti Kuat Manipulasi Digital.**")

            # 3. Panggil show_heatmaps dengan semua argumen (ELA, Noise, Brightness, dan Teks)
            # Pastikan urutan argumen sesuai dengan definisi show_heatmaps
            show_heatmaps(img, ela_heat, noise_heat, bright_heat, text_susp_mask, ela_susp, noise_susp, bright_susp, text_susp)