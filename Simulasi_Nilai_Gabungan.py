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
    .stButton>button { border-radius: 8px; background-color: #6B8E7B; color: white; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. FUNGSI PEMBANTU (HELPERS) ---

def load_data():
    """Memuat data dengan proteksi KeyError"""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Validasi minimal: Jika kolom NIS atau NISN tidak ada, anggap file rusak
            if "NIS" not in df.columns or "NISN" not in df.columns:
                return None
            
            df["NIS"] = df["NIS"].astype(str).str.strip()
            df["NISN"] = df["NISN"].astype(str).str.strip()
            return df
        except Exception:
            return None
    return None

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def generate_template():
    columns = ["NIS", "NISN", "Nama Siswa", "Kelas"]
    mapels = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
    for mapel in mapels:
        for s in range(1, 6):
            columns.append(f"{mapel}_S{s}")
    df_template = pd.DataFrame(columns=columns)
    df_template.loc[0] = ["1", "0011223344", "CONTOH NAMA", "IX A"] + [80]*20
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER

    # Header sesuai lampiran
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    p.line(20*mm, h - 25*mm, w - 20*mm, h - 25*mm)

    # Info Siswa
    p.setFont("Helvetica", 10)
    p.drawString(25*mm, h - 35*mm, f"Nama Siswa  : {user.get('Nama Siswa', '-')}")
    p.drawString(25*mm, h - 40*mm, f"NIS / NISN    : {user.get('NIS', '-')} / {user.get('NISN', '-')}")
    p.drawString(25*mm, h - 45*mm, f"Kelas             : {user.get('Kelas', '-')}")

    # Tabel Nilai
    data = [["No", "Mata Pelajaran", "S1", "S2", "S3", "S4", "S5", "Rerata", "TKA/D"]]
    sum_rerata = 0
    sum_tkad = 0
    for i, d in enumerate(detail_data, 1):
        data.append([i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]])
        sum_rerata += float(d["Rerata"])
        sum_tkad += float(d["TKA/D"])

    # Tambah Baris Jumlah
    data.append(["", "JUMLAH", "", "", "", "", "", f"{sum_rerata:.2f}", f"{sum_tkad:.2f}"])

    table = Table(data, colWidths=[10*mm, 40*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm, 22*mm, 22*mm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('SPAN', (1, -1), (6, -1)), # Gabungkan kolom jumlah
    ]))
    
    tw, th = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 25*mm, h - 60*mm - th)

    # Nilai Akhir
    y_pos = h - 70*mm - th
    p.setFont("Helvetica-Bold", 12)
    p.drawString(25*mm, y_pos, f"NILAI GABUNGAN : {nilai_akhir:.2f}")

    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(130*mm, y_pos - 20*mm, "Banguntapan, 27 April 2026")
    p.drawString(130*mm, y_pos - 25*mm, "Kepala Sekolah,")
    p.drawString(130*mm, y_pos - 50*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. SESSION STATE ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]

# --- 4. TAMPILAN ---
st.markdown("""<div class="running-text"><marquee>✨ Portal Simulasi Nilai Gabungan SMPN 2 Banguntapan ✨</marquee></div>""", unsafe_allow_html=True)
menu = st.sidebar.selectbox("📂 MENU", ["Home / Login", "Admin Upload"])

if menu == "Admin Upload":
    st.title("📂 Admin Control")
    pwd = st.text_input("Password", type="password")
    if pwd == "admin123":
        if st.button("🗑️ Hapus Database Lama"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.db_siswa = None
            st.success("Database lama dihapus. Silakan upload file baru.")
            st.rerun()

        st.download_button("📥 Download Template Baru", generate_template(), "template_baru.xlsx")
        uploaded = st.file_uploader("Upload File Excel Baru", type=["xlsx"])
        if uploaded:
            df = pd.read_excel(uploaded)
            df.columns = df.columns.str.strip()
            if "NIS" in df.columns and "NISN" in df.columns:
                save_data(df)
                st.session_state.db_siswa = load_data()
                st.success("Berhasil! Database sekarang menggunakan format NISN.")
            else:
                st.error("Gagal! File Excel Anda tidak memiliki kolom 'NISN'.")

else:
    if not st.session_state.logged_in:
        st.title("🏛️ Login Siswa")
        with st.form("login"):
            u = st.text_input("NIS")
            p = st.text_input("NISN (Password)", type="password")
            if st.form_submit_button("LOGIN"):
                db = st.session_state.db_siswa
                if db is not None:
                    match = db[(db["NIS"] == u.strip()) & (db["NISN"] == p.strip())]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("NIS atau NISN salah.")
                else: st.error("Database kosong. Hubungi Admin.")
    else:
        user = st.session_state.user_data
        st.title(f"🏫 Halo, {user['Nama Siswa']}")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

        col1, col2 = st.columns([1, 2])
        sim_tkad = {}
        with col1:
            st.subheader("Input TKA/D")
            for m in MAPEL_UTAMA:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, key=f"v_{m}")

        with col2:
            detail = []
            sum_rerata = 0
            for m in MAPEL_UTAMA:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v)/5
                sum_rerata += avg
                detail.append({"Mata Pelajaran": m, "Sem-1": int(v[0]), "Sem-2": int(v[1]), "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]), "Rerata": f"{avg:.2f}", "TKA/D": f"{sim_tkad[m]:.2f}"})
            
            nilai_akhir = (sum_rerata * 0.4) + (sum(sim_tkad.values()) * 0.6)
            st.metric("NILAI GABUNGAN", f"{nilai_akhir:.2f}")
            st.table(pd.DataFrame(detail))
            
            pdf = create_pdf(user, detail, nilai_akhir)
            st.download_button("🖨️ CETAK PDF", pdf, f"Laporan_{user['NIS']}.pdf")
