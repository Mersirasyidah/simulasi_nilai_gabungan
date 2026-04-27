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
    
    /* 1. Latar Belakang Utama Cerah */
    .stApp {
        background: linear-gradient(135deg, #FFFFFF 0%, #E3F2FD 100%) !important;
    }

    /* 2. Menu Navigasi (Sidebar) Senada */
    [data-testid="stSidebar"] {
        background-color: #E3F2FD !important;
        border-right: 1px solid #BBDEFB;
    }
    
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, h2, h3 {
        color: #0D47A1 !important;
        font-family: 'Quicksand', sans-serif;
    }

    /* 3. Running Text */
    .running-text {
        font-family: 'Quicksand', sans-serif;
        font-size: 14px; color: #1565C0; 
        background-color: #BBDEFB !important;
        padding: 12px 0; font-weight: bold; margin-top: -50px;
        margin-bottom: 25px; border-bottom: 2px solid #90CAF9;
    }

    /* 4. Kotak Konten (Cards) */
    [data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background: white !important;
        border-radius: 15px; 
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
        border: 1px solid #E3F2FD !important;
        margin-bottom: 20px;
    }

    /* 5. Tombol Biru Estetik */
    .stButton>button {
        border-radius: 10px; 
        background: linear-gradient(45deg, #2196F3, #64B5F6) !important;
        color: white !important; font-weight: 700; border: none; height: 3em; transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #1E88E5, #42A5F5) !important;
        transform: scale(1.02);
    }

    .copyright-label {
        background: linear-gradient(45deg, #1976D2, #42A5F5);
        color: white; padding: 6px 18px; border-radius: 25px; 
        font-size: 11px; font-weight: bold; letter-spacing: 0.5px;
    }

    .footer-web { 
        text-align: center; color: #546E7A; font-size: 12px; 
        padding: 30px; font-family: 'Quicksand', sans-serif; 
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 2. HELPERS ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df["Nama Siswa"] = df["Nama Siswa"].astype(str).str.strip()
            df["NISN"] = df["NISN"].astype(str).str.strip()
            return df
        except: return None
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
        ["No", "Mata Pelajaran", "Nilai Rapor Sem 1-5", "", "", "", "", "Rerata", "Nilai TKA/D"],
        ["", "", "S1", "S2", "S3", "S4", "S5", "", ""]
    ]
    
    total_r, total_t = 0, 0
    for i, d in enumerate(detail_data, 1):
        data.append([i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]])
        total_r += float(d["Rerata"])
        total_t += float(d["TKA/D"])
    
    data.append(["JUMLAH", "", "", "", "", "", "", f"{total_r:.2f}", f"{total_t:.2f}"])
    data.append(["NILAI GABUNGAN (60% TKA/D + 40% Rapor)", "", "", "", "", "", "", "", f"{nilai_akhir:.2f}"])
    
    table = Table(data, colWidths=[10*mm, 45*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 22*mm, 25*mm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,1), colors.lightblue),
        ('SPAN', (0,0), (0,1)), ('SPAN', (1,0), (1,1)), ('SPAN', (2,0), (6,0)), ('SPAN', (7,0), (7,1)), ('SPAN', (8,0), (8,1)),
        ('SPAN', (0,-2), (6,-2)), ('SPAN', (0,-1), (7,-1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
    ]))
    tw, th = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 15*mm, h - 60*mm - th)
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. LOGIC ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    st.title("Navigasi")
    list_menu = ["Home / Login"]
    with st.expander("🔐 Admin"):
        admin_pass = st.text_input("Password", type="password")
        if admin_pass == "alhamdulillahadmin99":
            list_menu.append("Admin Upload")

menu = st.sidebar.selectbox("Pilih Halaman", list_menu)

if menu == "Admin Upload":
    st.title("📂 Pengaturan Database")
    uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
        save_data(df)
        st.session_state.db_siswa = load_data()
        st.success("Database Diperbarui!")

else:
    st.markdown("""<div class="running-text"><marquee>✨ Rumus: (Total TKA/D x 60%) + (Total Rerata Rapor x 40%) ✨</marquee></div>""", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi Nilai")
        st.markdown("""<div style="text-align: right;"><span class="copyright-label">© 2026 dikembangkan oleh Mersi</span></div>""", unsafe_allow_html=True)
        
        u_nama = st.text_input("Username (Nama Sesuai Rapor)")
        p_nisn = st.text_input("Password (NISN)", type="password")
        if st.button("MASUK"):
            db = st.session_state.db_siswa
            if db is not None:
                match = db[(db["Nama Siswa"].str.upper() == u_nama.strip().upper()) & (db["NISN"].astype(str) == p_nisn.strip())]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Data tidak ditemukan.")
    
    else:
        user = st.session_state.user_data
        st.title(f"🏫 Halo, {user['Nama Siswa']}!")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

        col_in, col_res = st.columns([1, 2])
        MAPEL = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
        sim_tkad = {}
        
        with col_in:
            st.subheader("📝 Input TKA/D")
            for m in MAPEL:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0)

        with col_res:
            total_rerata_rapor = 0
            detail = []
            for m in MAPEL:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v) / 5
                total_rerata_rapor += avg
                detail.append({
                    "Mata Pelajaran": m, "Sem-1": int(v[0]), "Sem-2": int(v[1]), 
                    "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                    "Rerata": f"{avg:.2f}", "TKA/D": f"{sim_tkad[m]:.2f}"
                })
            
            total_tkad = sum(sim_tkad.values())
            
            # --- PERHITUNGAN SESUAI RUMUS ANDA ---
            poin_rapor = total_rerata_rapor * 0.4
            poin_tkad = total_tkad * 0.6
            nilai_akhir = poin_rapor + poin_tkad
            
            m1, m2 = st.columns(2)
            m1.metric("Poin Rapor (40%)", f"{poin_rapor:.2f}")
            m2.metric("Poin TKA/D (60%)", f"{poin_tkad:.2f}")

            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); padding:25px; border-radius:15px; border:1px solid #90CAF9; text-align:center;">
                    <p style="margin:0; color:#0D47A1; font-weight:bold;">ESTIMASI NILAI AKHIR GABUNGAN</p>
                    <h1 style="font-size:65px !important; color:#1565C0 !important; margin:10px 0;">{nilai_akhir:.2f}</h1>
                    <p style="font-size:12px; color:#546E7A;">( {poin_tkad:.2f} + {poin_rapor:.2f} )</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔍 Rincian Rapor"):
                st.table(pd.DataFrame(detail))

            pdf = create_pdf(user, detail, nilai_akhir)
            st.download_button("🖨️ CETAK PDF", pdf, f"Hasil_{user['Nama Siswa']}.pdf")

st.markdown('<div class="footer-web">© 2026 dikembangkan oleh Mersi | SMPN 2 Banguntapan</div>', unsafe_allow_html=True)
