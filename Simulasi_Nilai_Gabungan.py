import io
import pandas as pd
import streamlit as st
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# --- CONFIG ---
DB_FILE = "database_siswa.csv"

# --- 1. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(page_title="Portal Akademik SMPN 2 Banguntapan", layout="wide")

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
    
    /* Latar Belakang Estetik (Gradasi) */
    .stApp {
        background: linear-gradient(135deg, #f5f7f6 0%, #e8f0e8 100%);
    }

    .running-text {
        font-family: 'Quicksand', sans-serif;
        font-size: 14px; color: #3E584A; background-color: rgba(232, 240, 232, 0.9);
        padding: 10px 0; font-weight: bold; margin-top: -50px;
        margin-bottom: 25px; border-bottom: 1px solid #D1DBD1;
    }

    /* Card (Kotak Putih) yang lebih lembut */
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 15px; padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 20px;
    }

    h1, h2, h3 { color: #3E584A !important; font-family: 'Quicksand', sans-serif; }
    
    /* Button Estetik */
    .stButton>button {
        border-radius: 10px; 
        background: linear-gradient(45deg, #6B8E7B, #8eb59f);
        color: white; font-weight: 600; border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(107, 142, 123, 0.3);
    }

    .footer-web { 
        text-align: center; color: #7f8c8d; font-size: 12px; 
        padding: 30px; font-family: 'Quicksand', sans-serif; 
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. FUNGSI PEMBANTU (HELPERS) ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df["Nama Siswa"] = df["Nama Siswa"].astype(str).str.strip()
            df["NISN"] = df["NISN"].astype(str).str.strip()
            return df
        except:
            return None
    return None

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "HASIL SIMULASI NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2025/2026")
    
    p.setFont("Helvetica", 11)
    p.drawString(35*mm, h - 35*mm, f"Nama Siswa  : {user.get('Nama Siswa', '')}")
    p.drawString(35*mm, h - 42*mm, f"NIS         : {user.get('NIS', '')}")
    p.drawString(35*mm, h - 49*mm, f"Kelas       : {user.get('Kelas', '-')}")
    
    data = [
        ["No", "Mata Pelajaran", "Nilai Rapor Sem 1-5", "", "", "", "", "Rerata\nSem 1-5", "Nilai TKA/D"],
        ["", "", "Sem-1", "Sem-2", "Sem-3", "Sem-4", "Sem-5", "", ""]
    ]
    
    total_rerata, total_tkad = 0, 0
    for i, d in enumerate(detail_data, 1):
        data.append([i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]])
        total_rerata += float(d["Rerata"])
        total_tkad += float(d["TKA/D"])
    
    data.append(["JUMLAH", "", "", "", "", "", "", f"{total_rerata:.2f}", f"{total_tkad:.2f}"])
    data.append(["NILAI GABUNGAN", "", "", "", "", "", "", "", f"{nilai_akhir:.2f}"])
    
    table = Table(data, colWidths=[10*mm, 45*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 22*mm, 25*mm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
        ('SPAN', (0,0), (0,1)), ('SPAN', (1,0), (1,1)), ('SPAN', (2,0), (6,0)), ('SPAN', (7,0), (7,1)), ('SPAN', (8,0), (8,1)),
        ('SPAN', (0,-2), (6,-2)), ('SPAN', (0,-1), (7,-1)),
        ('BACKGROUND', (0,-1), (7,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    
    tw, th = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 15*mm, h - 60*mm - th)
    
    y_f = h - 75*mm - th
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(15*mm, y_f, "Ket : Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%)")
    
    # CREDIT DI PDF
    p.setFont("Helvetica-Bold", 8)
    p.drawRightString(w - 15*mm, y_f - 10*mm, "DI BUAT OLEH MERSI SMP NEGERI 2 BANGUNTAPAN")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. LOGIKA MENU & KEAMANAN ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    st.title("Navigasi")
    list_menu = ["Home / Login"]
    st.write("---")
    with st.expander("🔐 Admin Access"):
        admin_pass = st.text_input("Admin Password", type="password")
        if admin_pass == "alhamdulillahadmin99":
            list_menu.append("Admin Upload")
            st.success("Menu Admin Terbuka")

menu = st.sidebar.selectbox("Pilih Halaman", list_menu)

# --- 4. HALAMAN ADMIN ---
if menu == "Admin Upload":
    st.title("📂 Pengaturan Database")
    if st.session_state.db_siswa is not None:
        st.info(f"Data tersimpan: {len(st.session_state.db_siswa)} siswa.")
        if st.button("🗑️ Hapus Semua Data"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.db_siswa = None
            st.rerun()

    uploaded = st.file_uploader("Upload Excel Baru", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
        df.columns = df.columns.str.strip()
        if "Nama Siswa" in df.columns and "NISN" in df.columns:
            save_data(df)
            st.session_state.db_siswa = load_data()
            st.success("Database Berhasil Diperbarui!")
        else:
            st.error("Format Excel salah. Wajib ada kolom 'Nama Siswa' dan 'NISN'.")

# --- 5. HALAMAN LOGIN & SISWA ---
else:
    st.markdown("""<div class="running-text"><marquee scrollamount="8">✨ Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%) ✨</marquee></div>""", unsafe_allow_html=True)
    
    if not
