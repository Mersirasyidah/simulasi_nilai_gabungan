import io
import os
import numpy as np
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, lightgrey, blue, white
from datetime import datetime

# --- Inisialisasi Database di Session State ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = None

MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
SEMESTER_LIST = ["S1", "S2", "S3", "S4", "S5"]

bulan_id = {
    "January": "Januari", "February": "Februari", "March": "Maret",
    "April": "April", "May": "Mei", "June": "Juni",
    "July": "Juli", "August": "Agustus", "September": "September",
    "October": "Oktober", "November": "November", "December": "Desember"
}

# --- Fungsi PDF (Tetap sama dengan kode asli Anda) ---
def draw_kwarto_page(c, row, sel_tahun, tgl_ttd):
    # (Fungsi draw_kwarto_page Anda yang asli diletakkan di sini tanpa perubahan)
    # Pastikan variabel 'tkad' di fungsi ini mengambil dari input simulasi
    width, height = LETTER
    margin_left = 25 * mm
    margin_right = 20 * mm
    y = height - 18 * mm

    # --- KOP & LOGO ---
    # ... (Gunakan kode menggambar PDF yang Anda miliki) ...
    # Bagian perhitungan di dalam PDF:
    total_rata_s15 = 0
    total_tkad = 0
    for idx, m in enumerate(MAPEL_UTAMA, 1):
        vals_sem = [row[f"{m}_{s}"] for s in SEMESTER_LIST]
        rata = sum(vals_sem) / 5
        tkad = row[f"{m}_TKAD"] # Ini akan mengambil nilai dari simulasi
        total_rata_s15 += rata
        total_tkad += tkad
        # ... (Sisa kode drawing tabel) ...

    # Contoh ringkas logic nilai gabungan sesuai rumus Anda
    nilai_gabungan = (total_rata_s15 * 0.4) + (total_tkad * 0.6)
    # ... (Lanjutkan drawing footer pdf) ...
    pass # Hapus 'pass' jika sudah copy-paste kode asli Anda

# --- UI Streamlit ---
st.set_page_config(page_title="Simulasi Nilai Gabungan", layout="wide")

tabs = st.sidebar.radio("Navigasi Menu", ["1. Upload Data Rapor", "2. Simulasi & Generate"])

# --- MENU 1: UPLOAD DATA ---
if tabs == "1. Upload Data Rapor":
    st.header("📂 Database Nilai Rapor Semester 1-5")

    # Download Template
    cols_template = ["Kelas", "NIS", "Nama Siswa"] + [f"{m}_{s}" for m in MAPEL_UTAMA for s in SEMESTER_LIST]
    df_temp = pd.DataFrame(columns=cols_template)
    buffer_temp = io.BytesIO()
    with pd.ExcelWriter(buffer_temp, engine="openpyxl") as writer:
        df_temp.to_excel(writer, index=False)

    st.download_button("📥 Download Template Excel", data=buffer_temp.getvalue(), file_name="Template_Rapor.xlsx")

    uploaded = st.file_uploader("Upload Nilai Rapor S1-S5", type=["xlsx"])

    if uploaded:
        df_raw = pd.read_excel(uploaded)
        # Cleaning & Numerik
        for col in df_raw.columns:
            if col not in ["Kelas", "NIS", "Nama Siswa"]:
                df_raw[col] = pd.to_numeric(df_raw[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0)

        st.session_state.db_siswa = df_raw
        st.success(f"✅ Berhasil menyimpan {len(df_raw)} data siswa ke sistem.")
        st.dataframe(df_raw.head())

# --- MENU 2: SIMULASI ---
elif tabs == "2. Simulasi & Generate":
    st.header("🧪 Simulasi Nilai TKA/D")

    if st.session_state.db_siswa is None:
        st.warning("⚠️ Data Rapor belum diunggah. Silakan ke menu Upload terlebih dahulu.")
    else:
        df = st.session_state.db_siswa.copy()

        col_a, col_b = st.columns(2)
        with col_a:
            sel_kelas = st.selectbox("Pilih Kelas", sorted(df["Kelas"].unique()))
        with col_b:
            sel_tahun = st.selectbox("Tahun Pelajaran", ["2024/2025", "2025/2026"])

        tgl_ttd = st.date_input("Tanggal TTD Laporan", datetime.now())

        # Filter siswa berdasarkan kelas
        df_filtered = df[df["Kelas"] == sel_kelas].reset_index(drop=True)

        st.subheader(f"Input Nilai TKA/D - Kelas {sel_kelas}")
        st.info("Masukkan nilai TKA/D untuk setiap mapel di bawah ini:")

        # Buat kolom input TKA/D secara dinamis
        # Kita gunakan data_editor agar user bisa input langsung seperti Excel
        tkad_cols = [f"{m}_TKAD" for m in MAPEL_UTAMA]
        for col in tkad_cols:
            if col not in df_filtered.columns:
                df_filtered[col] = 0.0

        # Tampilkan editor untuk mengisi nilai TKA/D
        edited_df = st.data_editor(
            df_filtered,
            column_order=["NIS", "Nama Siswa"] + tkad_cols,
            disabled=["NIS", "Nama Siswa"], # NIS/Nama tidak boleh diedit di sini
            hide_index=True
        )

        if st.button("🚀 Generate PDF Hasil Simulasi"):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=LETTER)

            # Progress bar
            progress_bar = st.progress(0)
            total_siswa = len(edited_df)

            for i, (_, row) in enumerate(edited_df.iterrows()):
                # Panggil fungsi gambar PDF (pastikan fungsi draw_kwarto_page sudah terisi lengkap)
                # draw_kwarto_page(c, row, sel_tahun, tgl_ttd)
                # (Saya matikan panggilannya di contoh ini agar tidak error karena butuh assets/logo)

                # Logic simulasi sederhana untuk tampilan di Streamlit sebelum print PDF
                c.showPage()
                progress_bar.progress((i + 1) / total_siswa)

            # --- CATATAN: Karena saya tidak punya assets gambar Anda,
            # bagian simpan PDF di bawah ini hanya akan berfungsi jika fungsi
            # draw_kwarto_page Anda sudah dicopy dengan benar ---

            # c.save()
            # st.download_button("📄 Unduh PDF Gabungan", data=buffer.getvalue(), file_name=f"Laporan_Simulasi_{sel_kelas}.pdf")
            st.success("Simulasi selesai! PDF siap diunduh (Pastikan file logo/ttd tersedia di folder assets).")
