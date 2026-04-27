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
    .footer-web { text-align: center; color: #7f8c8d; font-size: 12px; padding: 20px; font-family: 'Quicksand', sans-serif; }
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
    
    #p.setFont("Helvetica-Bold", 8)
    #p.drawRightString(w - 15*mm, y_f - 10*mm, "DI BUAT OLEH MERSI SMP NEGERI 2 BANGUNTAPAN")

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
    
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi Nilai Gabungan")
        
        st.info("""
        **Selamat datang di aplikasi simulasi nilai gabungan.** Sistem ini dirancang untuk membantu siswa menghitung estimasi nilai gabungan sementara. 
        Simulasi ini menggunakan integrasi nilai Rapor Semester 1-5 yang telah terverifikasi 
        dan nilai TKA/D (Hasil Try Out) yang telah dilaksanakan.
        """)

        # PERBAIKAN: Copyright menarik (Sudah tidak error)
        #st.markdown("""
            #<div style="text-align: right; margin-top: -15px; margin-bottom: 20px;">
                #<span style="background-color: #6B8E7B; color: white; padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    #© 2026 dikembangkan oleh Mersi | Inovasi Digital SMP Negeri 2 Banguntapan
                #</span>
            #</div>
        #""", unsafe_allow_html=True)
        
        with st.container():
            u_nama = st.text_input("Username (Nama Lengkap Sesuai Rapor)")
            p_nisn = st.text_input("Password (NISN)", type="password")
            
            if st.button("MASUK"):
                db = st.session_state.db_siswa
                if db is not None:
                    match = db[
                        (db["Nama Siswa"].astype(str).str.upper() == u_nama.strip().upper()) & 
                        (db["NISN"].astype(str) == p_nisn.strip())
                    ]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("Nama Siswa atau NISN salah. Periksa kembali penulisan nama Anda.")
                else: st.warning("Database belum tersedia. Hubungi Admin.")
    
    else:
        # Halaman Siswa (Setelah Login)
        user = st.session_state.user_data
        st.title(f"🏫 Halo, {user['Nama Siswa']}!")
        if st.sidebar.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

        col_in, col_res = st.columns([1, 2])
        MAPEL = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
        sim_tkad = {}
        
        with col_in:
            st.subheader("📝 Input Nilai TKA/D")
            for m in MAPEL:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, key=f"n_{m}")

        with col_res:
            total_rerata = 0
            detail = []
            for m in MAPEL:
                v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                avg = sum(v) / 5
                total_rerata += avg
                detail.append({
                    "Mata Pelajaran": m, "Sem-1": int(v[0]), "Sem-2": int(v[1]), 
                    "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                    "Rerata": f"{avg:.2f}", "TKA/D": f"{sim_tkad[m]:.2f}"
                })
            
            nilai_akhir = (total_rerata * 0.4) + (sum(sim_tkad.values()) * 0.6)
            
            m1, m2 = st.columns(2)
            m1.metric("Poin Rapor (40%)", f"{(total_rerata * 0.4):.2f}")
            m2.metric("Poin TKA/D (60%)", f"{(sum(sim_tkad.values()) * 0.6):.2f}")

            st.markdown(f"""
                <div style="background:#E8F5E9;padding:20px;border-radius:12px;border:1px solid #A5D6A7;text-align:center;margin-bottom:20px;">
                    <p style="margin:0; color:#2E7D32; font-weight:bold;">ESTIMASI NILAI AKHIR</p>
                    <h1 style="font-size:60px !important;color:#1B5E20 !important;margin:10px 0;">{nilai_akhir:.2f}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔍 Rincian Nilai Rapor Semester 1-5"):
                st.table(pd.DataFrame(detail))

            pdf = create_pdf(user, detail, nilai_akhir)
            st.download_button("🖨️ CETAK LAPORAN PDF", pdf, f"Simulasi_Nilai_Gabungan_{user['Nama Siswa']}.pdf")

# FOOTER WEB
st.markdown("""
    <div class="footer-web">
        © 2026 dikembangkan oleh Mersi | Inovasi Digital SMP Negeri 2 Banguntapan
    </div>
""", unsafe_allow_html=True)
