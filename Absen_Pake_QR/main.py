import cv2
from pyzbar.pyzbar import decode
import csv
import os
from datetime import datetime
import numpy as np

# --- Konfigurasi ---
FILE_ABSENSI = 'data_absensi.csv'
DURASI_PESAN = 2  # Berapa detik pesan "BERHASIL" tampil di layar

# Set untuk melacak siswa yang sudah absen agar tidak duplikat
siswa_sudah_absen = set()

# Variabel untuk menampilkan pesan sementara di layar
pesan_layar = ""
waktu_pesan = 0


def to_numpy_pts(pts):
    """Mengubah list titik polygon menjadi array numpy untuk cv2.polylines."""
    return np.array(pts, dtype=np.int32)


def inisialisasi_csv():
    """Membuat file CSV dengan header jika belum ada atau masih kosong."""
    file_baru = not os.path.exists(FILE_ABSENSI) or os.path.getsize(FILE_ABSENSI) == 0
    if file_baru:
        with open(FILE_ABSENSI, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nama', 'Kelas', 'Tanggal', 'Jam'])
        print(f"📄 File '{FILE_ABSENSI}' dibuat dengan header.")


def catat_absensi(nama, kelas):
    """Menyimpan data absensi ke dalam file CSV."""
    with open(FILE_ABSENSI, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        waktu_sekarang = datetime.now()
        tanggal = waktu_sekarang.strftime('%Y-%m-%d')
        jam = waktu_sekarang.strftime('%H:%M:%S')
        writer.writerow([nama, kelas, tanggal, jam])


def tampilkan_pesan(frame, teks, warna=(0, 255, 0)):
    """Menampilkan teks besar di bagian atas frame."""
    cv2.putText(frame, teks, (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, warna, 3, cv2.LINE_AA)


# --- Inisialisasi ---
inisialisasi_csv()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Tidak dapat membuka kamera.")
    exit()

print("✅ Kamera aktif. Arahkan QR Code siswa ke kamera...")
print("ℹ️  Tekan 'q' untuk keluar.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Gagal membaca frame dari kamera.")
        break

    for barcode in decode(frame):
        data_qr = barcode.data.decode('utf-8')

        # Gambar kotak di sekitar QR code
        points = barcode.polygon
        if len(points) == 4:
            pts = [tuple(p) for p in points]
            cv2.polylines(frame, [to_numpy_pts(pts)], True, (255, 165, 0), 3)

        if data_qr not in siswa_sudah_absen:
            try:
                nama, kelas = data_qr.split(',')
                nama = nama.strip()
                kelas = kelas.strip()

                catat_absensi(nama, kelas)
                siswa_sudah_absen.add(data_qr)

                print(f"✅ Hadir: {nama} | Kelas: {kelas} | {datetime.now().strftime('%H:%M:%S')}")

                # Set pesan sukses + catat waktu mulai tampil
                pesan_layar = f"HADIR: {nama} ({kelas})"
                waktu_pesan = datetime.now().timestamp()

            except ValueError:
                print("⚠️ Format QR salah! Gunakan format: Nama,Kelas")
                pesan_layar = "FORMAT QR SALAH!"
                waktu_pesan = datetime.now().timestamp()

        else:
            # Siswa sudah absen sebelumnya
            pesan_layar = f"SUDAH ABSEN: {data_qr.split(',')[0].strip()}"
            waktu_pesan = datetime.now().timestamp()

    # Tampilkan pesan selama DURASI_PESAN detik
    if pesan_layar and (datetime.now().timestamp() - waktu_pesan) < DURASI_PESAN:
        if "HADIR" in pesan_layar:
            tampilkan_pesan(frame, pesan_layar, warna=(0, 255, 0))       # Hijau
        elif "SUDAH" in pesan_layar:
            tampilkan_pesan(frame, pesan_layar, warna=(0, 165, 255))     # Oranye
        else:
            tampilkan_pesan(frame, pesan_layar, warna=(0, 0, 255))       # Merah
    else:
        pesan_layar = ""  # Reset pesan setelah durasi habis

    cv2.imshow('Scanner Absensi Siswa', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("📴 Program dihentikan.")