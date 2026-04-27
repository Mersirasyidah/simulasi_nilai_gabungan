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
    .stApp { background-color: #F7F9F7; color: #34495E; }
    [data-testid="stSidebar"] { background-color: #E8F0E8 !important; border-right: 1px solid #D1DBD1; }
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background: white; border-radius: 12px; padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #E0E7E0; margin-bottom: 8px;
    }
    h1, h2, h3 { color: #3E584A !important; }
    [data-testid="stMetricValue"] { color: #4F7942 !important; font-size: 24px !important; font-weight: 700; }
    .stButton>button { border-radius: 8px; background-color: #6B8E7B; color: white; font-weight: 600; border: none; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. FUNGSI PEMBANTU ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df["NIS"] = df["NIS"].astype(str).str.strip()
            if "NISN" in df.columns:
                df["NISN"] = df["NISN"].astype(str).str.strip()
            return df
        except:
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
    df_template.loc[0] = ["1", "0011223344", "ADELIA ARIMI AZALEA", "IX A"] + [80]*20
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    # Judul
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    
    # Identitas
    p.setFont("Helvetica", 11)
    p.drawString(30*mm, h - 35*mm, f"Nama Siswa  : {user.get('Nama Siswa', '')}")
    p.drawString(30*mm, h - 42*mm, f"NIS         : {user.get('NIS', '')}")
    p.drawString(30*mm, h - 49*mm, f"Kelas       : {user.get('Kelas', '-')}")
    
    # Header Tabel 2 Baris
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
    
    # Footer
    y_f = h - 75*mm - th
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(15*mm, y_f, "Ket : Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%)")
    p.setFont("Helvetica", 10)
    p.drawString(135*mm, y_f - 15*mm, "Banguntapan, 27 April 2026")
    p.drawString(135*mm, y_f - 20*mm, "Kepala Sekolah,")
    p.drawString(135*mm, y_f - 45*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. LOGIKA UTAMA ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.markdown("""<div class="running-text"><marquee scrollamount="8">✨ Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%) ✨</marquee></div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Home / Login", "Admin Upload"])

if menu == "Admin Upload":
    st.title("📂 Admin Control")
    pwd = st.text_input("Password Admin", type="password")
    if pwd == "admin123":
        if st.session_state.db_siswa is not None:
            st.success(f"Database aktif: {len(st.session_state.db_siswa)} siswa.")
            if st.button("Hapus Database"):
                if os.path.exists(DB_FILE): os.remove(DB_FILE)
                st.session_state.db_siswa = None
                st.rerun()
        
        st.download_button("📥 Download Template Excel", generate_template(), "template.xlsx")
        uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
        if uploaded:
            df = pd.read_excel(uploaded)
            df.columns = df.columns.str.strip()
            if "NIS" in df.columns and "NISN" in df.columns:
                save_data(df)
                st.session_state.db_siswa = load_data()
                st.success("Database diperbarui!")
            else: st.error("Kolom NIS dan NISN wajib ada!")

else:
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi")
        u = st.text_input("Username (NIS)")
        p = st.text_input("Password (NISN)", type="password")
        if st.button("LOGIN"):
            db = st.session_state.db_siswa
            if db is not None:
                match = db[(db["NIS"].astype(str) == u.strip()) & (db["NISN"].astype(str) == p.strip())]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("NIS atau NISN salah.")
            else: st.warning("Database kosong.")
    else:
        # TAMPILAN SETELAH LOGIN
        user = st.session_state.user_data
        st.title(f"🏫 Hallo: {user['Nama Siswa']}!")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        col_in, col_res = st.columns([1, 2])
        MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
        sim_tkad = {}
        
        with col_in:
            st.subheader("📝 Input Nilai TKA/D")
            for m in MAPEL_UTAMA:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, key=f"v_{m}")

        with col_res:
            total_rerata = 0
            detail_data = []
            for m in MAPEL_UTAMA:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v) / 5
                total_rerata += avg
                detail_data.append({
                    "Mata Pelajaran": m, "Sem-1": int(v[0]), "Sem-2": int(v[1]), 
                    "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                    "Rerata": f"{avg:.2f}", "TKA/D": f"{sim_tkad[m]:.2f}"
                })
            
            nilai_akhir = (total_rerata * 0.4) + (sum(sim_tkad.values()) * 0.6)
            
            # Metric Box
            m1, m2 = st.columns(2)
            m1.metric("Poin Rapor (40%)", f"{(total_rerata * 0.4):.2f}")
            m2.metric("Poin TKA/D (60%)", f"{(sum(sim_tkad.values()) * 0.6):.2f}")

            st.markdown(f"""
                <div style="background:#E8F5E9;padding:20px;border-radius:12px;border:1px solid #A5D6A7;text-align:center;margin-bottom:20px;">
                    <h1 style="font-size:60px !important;color:#1B5E20 !important;margin:10px 0;">{nilai_akhir:.2f}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔍 Lihat Rincian Nilai Rapor", expanded=True):
                st.table(pd.DataFrame(detail_data))

            pdf = create_pdf(user, detail_data, nilai_akhir)
            st.download_button("🖨️ UNDUH HASIL PDF", pdf, f"Laporan_{user['NIS']}.pdf")
