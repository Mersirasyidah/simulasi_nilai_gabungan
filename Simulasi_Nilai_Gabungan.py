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
    .running-text {
        font-family: 'Quicksand', sans-serif;
        font-size: 14px; color: #3E584A; background-color: #E8F0E8;
        padding: 8px 0; font-weight: bold; margin-top: -50px;
        margin-bottom: 20px; border-bottom: 1px solid #D1DBD1;
    }
    .stApp { background-color: #F7F9F7; }
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background: white; border-radius: 12px; padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #E0E7E0;
    }
    h1, h2, h3 { color: #3E584A !important; }
    .stButton>button { border-radius: 8px; background-color: #6B8E7B; color: white; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. FUNGSI PEMBANTU (HELPERS) ---

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df["NIS"] = df["NIS"].astype(str)
        df["NISN"] = df["NISN"].astype(str) # NISN sebagai Password
        return df
    return None

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def generate_template():
    columns = ["NIS", "NISN", "Nama Siswa", "Kelas"] # Ditambah NISN dan Kelas
    mapels = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
    for mapel in mapels:
        for s in range(1, 6):
            columns.append(f"{mapel}_S{s}")
    df_template = pd.DataFrame(columns=columns)
    # Contoh data
    example = ["12345", "0011223344", "ADELIA ARIMI AZALEA", "IX A"] + [80]*20
    df_template.loc[0] = example
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER

    # Header
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    p.line(20*mm, h - 25*mm, w - 20*mm, h - 25*mm)

    # Info Siswa
    p.setFont("Helvetica", 10)
    p.drawString(25*mm, h - 35*mm, f"Nama Siswa  : {user['Nama Siswa']}")
    p.drawString(25*mm, h - 40*mm, f"NIS / NISN    : {user['NIS']} / {user['NISN']}")
    p.drawString(25*mm, h - 45*mm, f"Kelas             : {user.get('Kelas', '-')}")

    # Tabel Nilai
    data = [["No", "Mata Pelajaran", "S1", "S2", "S3", "S4", "S5", "Rerata", "TKA/D"]]
    for i, d in enumerate(detail_data, 1):
        data.append([
            i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], 
            d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]
        ])
    
    # Tambah baris jumlah atau nilai akhir jika perlu
    table = Table(data, colWidths=[10*mm, 45*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm, 20*mm, 20*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    tw, th, = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 25*mm, h - 60*mm - th)

    # Nilai Akhir
    y_pos = h - 65*mm - th
    p.setFont("Helvetica-Bold", 12)
    p.drawString(25*mm, y_pos, f"NILAI GABUNGAN : {nilai_akhir:.2f}")

    # Footer / TTD
    p.setFont("Helvetica", 10)
    p.drawString(130*mm, y_pos - 15*mm, "Banguntapan, 27 April 2026")
    p.drawString(130*mm, y_pos - 20*mm, "Kepala Sekolah,")
    p.drawString(130*mm, y_pos - 45*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. SESSION STATE ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]

# --- 4. TAMPILAN ---
st.markdown("""<div class="running-text"><marquee>✨ Rumus: ((TKA+TKAD) x 60%) + (Rerata Rapor x 40%) ✨</marquee></div>""", unsafe_allow_html=True)
menu = st.sidebar.selectbox("📂 MENU", ["Home / Login", "Admin Upload"])

if menu == "Admin Upload":
    st.title("📂 Admin Control")
    pwd = st.text_input("Password Admin", type="password")
    if pwd == "admin123":
        st.info("Pastikan Excel memiliki kolom: NIS, NISN, Nama Siswa, Kelas, dan Nilai Mapel S1-S5.")
        st.download_button("📥 Download Template", generate_template(), "template.xlsx")
        uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
        if uploaded:
            df = pd.read_excel(uploaded)
            save_data(df)
            st.session_state.db_siswa = load_data()
            st.success("Database diperbarui!")
else:
    if not st.session_state.logged_in:
        st.title("🏛️ Login Siswa")
        user_id = st.text_input("Username (NIS)")
        password = st.text_input("Password (NISN)", type="password")
        if st.button("MASUK"):
            db = st.session_state.db_siswa
            if db is not None:
                match = db[(db["NIS"] == user_id.strip()) & (db["NISN"] == password.strip())]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("NIS atau NISN salah.")
            else: st.warning("Database kosong.")
    else:
        user = st.session_state.user_data
        st.title(f"🏫 Siswa: {user['Nama Siswa']}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # Simulasi & Perhitungan (Sama seperti sebelumnya namun detail_data disesuaikan untuk PDF)
        col1, col2 = st.columns([1, 2])
        sim_tkad = {}
        with col1:
            st.subheader("Input Nilai TKA/D")
            for m in MAPEL_UTAMA:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, key=f"in_{m}")

        with col2:
            detail_data = []
            total_rerata = 0
            for m in MAPEL_UTAMA:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v) / 5
                total_rerata += avg
                detail_data.append({
                    "Mata Pelajaran": m, "Sem-1": int(v[0]), "Sem-2": int(v[1]), 
                    "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                    "Rerata": f"{avg:.2f}", "TKA/D": f"{sim_tkad[m]:.2f}"
                })
            
            total_tkad = sum(sim_tkad.values())
            nilai_akhir = (total_rerata * 0.4) + (total_tkad * 0.6)
            
            st.metric("ESTIMASI NILAI GABUNGAN", f"{nilai_akhir:.2f}")
            st.table(pd.DataFrame(detail_data))
            
            pdf = create_pdf(user, detail_data, nilai_akhir)
            st.download_button("🖨️ UNDUH LAPORAN PDF", pdf, f"Laporan_{user['NIS']}.pdf")
