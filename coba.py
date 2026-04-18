import io
import os
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(page_title="Portal Akademik SMPN 2 Banguntapan", layout="wide")

# File path untuk database permanen sederhana
DB_FILE = "database_siswa.csv"

def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
    .running-text {
        font-family: 'Quicksand', sans-serif;
        font-size: 14px; color: #3E584A; background-color: #E8F0E8;
        padding: 8px 0; font-weight: bold; margin-top: -50px;
        margin-bottom: 20px; border-bottom: 1px solid #D1DBD1;
    }
    .stApp { background-color: #F7F9F7; color: #34495E; }
    [data-testid="stSidebar"] { background-color: #E8F0E8 !important; border-right: 1px solid #D1DBD1; }
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background: white; border-radius: 12px; padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #E0E7E0; margin-bottom: 8px;
    }
    h1, h2, h3 { color: #3E584A !important; }
    [data-testid="stMetricValue"] { color: #4F7942 !important; font-size: 24px !important; font-weight: 700; }
    .stButton>button { border-radius: 8px; background-color: #6B8E7B; color: white; font-weight: 600; border: none; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. FUNGSI DATABASE PERMANEN ---
def save_db(df):
    df.to_csv(DB_FILE, index=False)

def load_db():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df["NIS"] = df["NIS"].astype(str).str.strip()
        return df
    return None

# --- 3. FUNGSI PEMBANTU (HELPERS) ---
def generate_template():
    columns = ["NIS", "Nama Siswa"]
    mapels = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
    for mapel in mapels:
        for s in range(1, 6):
            columns.append(f"{mapel}_S{s}")
    df_template = pd.DataFrame(columns=columns)
    df_template.loc[0] = ["12345", "Contoh Nama Siswa"] + [80]*20
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(user, detail_data, total_rerata, total_tkad, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w/2, h - 20*mm, "LAPORAN SIMULASI NILAI GABUNGAN")
    p.setFont("Helvetica", 12)
    p.drawCentredString(w/2, h - 26*mm, "SMP NEGERI 2 BANGUNTAPAN")
    p.line(20*mm, h - 32*mm, w - 20*mm, h - 32*mm)
    
    # Identitas
    p.setFont("Helvetica-Bold", 11)
    p.drawString(25*mm, h - 45*mm, f"Nama Siswa : {user['Nama Siswa']}")
    p.drawString(25*mm, h - 51*mm, f"NIS          : {user['NIS']}")
    
    # Tabel
    y = h - 65*mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(25*mm, y, "Mata Pelajaran")
    p.drawString(120*mm, y, "Rerata Rapor")
    p.drawString(160*mm, y, "Nilai TKA/D")
    p.line(25*mm, y - 2*mm, 190*mm, y - 2*mm)
    
    y -= 7*mm
    p.setFont("Helvetica", 10)
    for d in detail_data:
        p.drawString(25*mm, y, d["Mata Pelajaran"])
        p.drawString(125*mm, y, d["Rerata"])
        p.drawString(165*mm, y, d["TKA/D"])
        y -= 6*mm
        
    p.line(25*mm, y + 1*mm, 190*mm, y + 1*mm)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(25*mm, y - 4*mm, "JUMLAH TOTAL")
    p.drawString(125*mm, y - 4*mm, f"{total_rerata:.2f}")
    p.drawString(165*mm, y - 4*mm, f"{total_tkad:.2f}")
    
    # Skor Akhir
    y -= 25*mm
    p.setFillColor(colors.HexColor("#E8F5E9"))
    p.rect(50*mm, y, 110*mm, 20*mm, fill=1)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, y + 12*mm, "NILAI AKHIR GABUNGAN")
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(w/2, y + 3*mm, f"{nilai_akhir:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 4. LOGIKA UTAMA ---
# Load database saat aplikasi pertama kali jalan
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]

st.markdown("""<div class="running-text"><marquee scrollamount="8">✨ Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%) ✨</marquee></div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Home / Login", "Admin Upload"])

if menu == "Admin Upload":
    st.title("📂 Admin Control (Database Permanen)")
    pwd = st.text_input("Password", type="password")
    if pwd == "admin123":
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 Download Template Excel", generate_template(), "template.xlsx", "application/vnd.ms-excel")
        with c2:
            uploaded = st.file_uploader("Upload Data Siswa", type=["xlsx"])
            if uploaded:
                df = pd.read_excel(uploaded)
                df.columns = df.columns.str.strip()
                df["NIS"] = df["NIS"].astype(str).str.replace('.0', '', regex=False).str.strip()
                save_db(df) # Simpan permanen ke CSV
                st.session_state.db_siswa = df
                st.success("✅ Data berhasil disimpan secara permanen!")
        
        if st.session_state.db_siswa is not None:
            st.write(f"Data tersimpan: {len(st.session_state.db_siswa)} siswa.")

else:
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi")
        nis_in = st.text_input("MASUKKAN NIS")
        if st.button("LOGIN"):
            if st.session_state.db_siswa is not None:
                match = st.session_state.db_siswa[st.session_state.db_siswa["NIS"] == nis_in.strip()]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("NIS tidak ditemukan.")
            else: st.warning("Database kosong. Admin harus upload data.")
    else:
        user = st.session_state.user_data
        st.title(f"🏫 Hallo: {user['Nama Siswa']}!")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        col_in, col_res = st.columns([1, 2])
        sim_tkad = {}
        with col_in:
            st.subheader("📝 Input Nilai TKA/D")
            for m in MAPEL_UTAMA:
                sim_tkad[f"{m}_TKAD"] = st.number_input(f"{m}", 0.0, 100.0, 0.0, step=0.01, format="%.2f", key=f"in_{m}")

        with col_res:
            total_rerata = 0
            detail_data = []
            for m in MAPEL_UTAMA:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v) / 5
                total_rerata += avg
                detail_data.append({
                    "Mata Pelajaran": m, 
                    "S1": int(v[0]), "S2": int(v[1]), "S3": int(v[2]), "S4": int(v[3]), "S5": int(v[4]),
                    "Rerata": f"{avg:.2f}", 
                    "TKA/D": f"{sim_tkad[f'{m}_TKAD']:.2f}"
                })
            
            total_tkad = sum(sim_tkad.values())
            nilai_akhir = (total_rerata * 0.4) + (total_tkad * 0.6)

            m1, m2 = st.columns(2)
            m1.metric("Poin Rapor (40%)", f"{total_rerata * 0.4:.2f}")
            m2.metric("Poin TKA/D (60%)", f"{total_tkad * 0.6:.2f}")

            st.markdown(f"""<div style="background:#E8F5E9;padding:20px;border-radius:12px;border:1px solid #A5D6A7;text-align:center;margin-bottom:20px;">
                <h1 style="font-size:60px !important;color:#1B5E20 !important;margin:0;">{nilai_akhir:.2f}</h1></div>""", unsafe_allow_html=True)
            
            # --- TABEL DENGAN BARIS TOTAL ---
            df_display = pd.DataFrame(detail_data)
            # Buat baris total untuk tampilan tabel
            row_total = pd.DataFrame([{
                "Mata Pelajaran": "JUMLAH TOTAL",
                "S1": "", "S2": "", "S3": "", "S4": "", "S5": "",
                "Rerata": f"{total_rerata:.2f}",
                "TKA/D": f"{total_tkad:.2f}"
            }])
            df_final = pd.concat([df_display, row_total], ignore_index=True)
            
            with st.expander("🔍 Rincian Nilai", expanded=True):
                st.table(df_final)

            pdf_file = create_pdf(user, detail_data, total_rerata, total_tkad, nilai_akhir)
            st.download_button("🖨️ UNDUH HASIL SIMULASI (PDF)", pdf_file, f"Hasil_{user['NIS']}.pdf", "application/pdf")
