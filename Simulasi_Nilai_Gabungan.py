import io
import pandas as pd
import streamlit as st
import os  
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime

# --- CONFIG ---
DB_FILE = "database_siswa.csv" 

# --- 1. KONFIGURASI HALAMAN & CSS (TIDAK BERUBAH) ---
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

# --- 2. FUNGSI PEMBANTU (HELPERS) ---

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
    # Menambah kolom NISN dan Kelas di template
    columns = ["NIS", "NISN", "Nama Siswa", "Kelas"]
    mapels = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
    for mapel in mapels:
        for s in range(1, 6):
            columns.append(f"{mapel}_S{s}")
    df_template = pd.DataFrame(columns=columns)
    # Contoh Baris 1
    example_row = ["1", "0011223344", "ADELIA ARIMI AZALEA", "IX A"] + [80]*20
    df_template.loc[0] = example_row
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name='DataSiswa')
    return output.getvalue()

def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    # Header Laporan
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 20*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 26*mm, "TAHUN PELAJARAN 2024/2025")
    p.line(20*mm, h - 30*mm, w - 20*mm, h - 30*mm)
    
    # Identitas
    p.setFont("Helvetica", 10)
    p.drawString(25*mm, h - 40*mm, f"Nama Siswa : {user.get('Nama Siswa', '')}")
    p.drawString(25*mm, h - 45*mm, f"NIS / NISN   : {user.get('NIS', '')} / {user.get('NISN', '-')}")
    p.drawString(25*mm, h - 50*mm, f"Kelas            : {user.get('Kelas', '-')}")
    
    # Tabel Nilai (Data sesuai Lampiran)
    table_data = [["No", "Mata Pelajaran", "S1", "S2", "S3", "S4", "S5", "Rerata", "TKA/D"]]
    total_rerata_all = 0
    total_tkad_all = 0
    
    for i, d in enumerate(detail_data, 1):
        table_data.append([
            i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], 
            d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]
        ])
        total_rerata_all += float(d["Rerata"])
        total_tkad_all += float(d["TKA/D"])
    
    # Baris Jumlah
    table_data.append(["", "JUMLAH", "", "", "", "", "", f"{total_rerata_all:.2f}", f"{total_tkad_all:.2f}"])
    
    table = Table(table_data, colWidths=[10*mm, 45*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm, 20*mm, 20*mm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('SPAN', (1, -1), (6, -1)), # Gabung kolom No-S5 untuk baris Jumlah
    ]))
    
    tw, th = table.wrapOn(p, 25*mm, h - 60*mm)
    table.drawOn(p, 25*mm, h - 60*mm - th)
    
    # Nilai Akhir & Keterangan
    y_pos = h - 70*mm - th
    p.setFont("Helvetica-Bold", 12)
    p.drawString(25*mm, y_pos, f"NILAI GABUNGAN: {nilai_akhir:.2f}")
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(25*mm, y_pos - 8*mm, "Ket: Rumus = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor S1-5 x 40%)")

    # Tanda Tangan (Mengetahui Kepala Sekolah)
    p.setFont("Helvetica", 10)
    p.drawString(135*mm, y_pos - 25*mm, "Banguntapan, 27 April 2026")
    p.drawString(135*mm, y_pos - 30*mm, "Kepala Sekolah,")
    p.drawString(135*mm, y_pos - 55*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. INISIALISASI SESSION STATE ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]

# --- 4. TAMPILAN UTAMA ---
st.markdown("""<div class="running-text"><marquee scrollamount="8">✨ Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%) ✨</marquee></div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Home / Login", "Admin Upload"])

# --- MODUL ADMIN ---
if menu == "Admin Upload":
    st.title("📂 Admin Control")
    pwd = st.text_input("Password", type="password")
    
    if pwd == "admin123":
        if st.session_state.db_siswa is not None:
            st.success(f"Database saat ini berisi {len(st.session_state.db_siswa)} data siswa.")
            if st.button("Hapus Database & Upload Ulang"):
                if os.path.exists(DB_FILE):
                    os.remove(DB_FILE)
                st.session_state.db_siswa = None
                st.rerun()
        
        st.info("Sistem Login sekarang menggunakan NIS (User) dan NISN (Password). Pastikan file Excel memiliki kedua kolom tersebut.")
        template_bytes = generate_template()
        st.download_button(label="📥 Download Template Excel Terbaru", data=template_bytes, file_name="template_data_siswa_baru.xlsx")
        
        st.divider()
        uploaded = st.file_uploader("Upload Data Siswa (Excel)", type=["xlsx"])
        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                df.columns = df.columns.str.strip()
                if "NIS" in df.columns and "NISN" in df.columns:
                    df["NIS"] = df["NIS"].astype(str).str.replace('.0', '', regex=False).str.strip()
                    df["NISN"] = df["NISN"].astype(str).str.replace('.0', '', regex=False).str.strip()
                    save_data(df)
                    st.session_state.db_siswa = df
                    st.success(f"Berhasil menyimpan {len(df)} data ke server secara permanen!")
                else:
                    st.error("Format kolom salah! Pastikan ada kolom 'NIS' dan 'NISN'.")
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
    elif pwd != "":
        st.error("Password Salah!")

# --- MODUL SISWA ---
else:
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi")
        st.write("Silakan login menggunakan NIS dan NISN Anda.")
        
        nis_in = st.text_input("USER ID (NIS)", placeholder="Masukkan NIS")
        nisn_in = st.text_input("PASSWORD (NISN)", placeholder="Masukkan NISN", type="password")
        
        if st.button("LOGIN"):
            if st.session_state.db_siswa is not None:
                db = st.session_state.db_siswa
                # Login dengan NIS dan NISN
                match = db[(db["NIS"] == nis_in.strip()) & (db["NISN"] == nisn_in.strip())]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("NIS atau NISN tidak ditemukan.")
            else:
                st.warning("Database siswa kosong. Admin harus mengunggah data terlebih dahulu.")
    
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
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, step=0.01, format="%.2f", key=f"in_{m}")

        with col_res:
            total_rerata = 0
            detail_data = []
            
            for m in MAPEL_UTAMA:
                try:
                    v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                    avg = sum(v) / 5
                    total_rerata += avg
                    detail_data.append({
                        "Mata Pelajaran": m, 
                        "Sem-1": int(v[0]), "Sem-2": int(v[1]), "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                        "Rerata": f"{avg:.2f}", 
                        "TKA/D": f"{sim_tkad[m]:.2f}"
                    })
                except:
                    st.error(f"Data nilai {m} tidak lengkap.")
                    st.stop()
            
            total_tkad = sum(sim_tkad.values())
            poin_rapor = total_rerata * 0.4
            poin_tkad = total_tkad * 0.6
            nilai_akhir = poin_rapor + poin_tkad

            m1, m2 = st.columns(2)
            m1.metric("Poin Rapor (40%)", f"{poin_rapor:.2f}")
            m2.metric("Poin TKA/D (60%)", f"{poin_tkad:.2f}")

            st.markdown(f"""
                <div style="background:#E8F5E9;padding:20px;border-radius:12px;border:1px solid #A5D6A7;text-align:center;margin-bottom:20px;">
                    <p style="margin:0; font-size:14px; font-weight:bold; color:#2E7D32;">ESTIMASI NILAI GABUNGAN AKHIR</p>
                    <h1 style="font-size:60px !important;color:#1B5E20 !important;margin:10px 0;">{nilai_akhir:.2f}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔍 Lihat Rincian Nilai Rapor", expanded=True):
                st.table(pd.DataFrame(detail_data))

            # Generate PDF
            pdf_file = create_pdf(user, detail_data, nilai_akhir)
            st.download_button(label="🖨️ UNDUH LAPORAN PDF", data=pdf_file, file_name=f"Laporan_{user['NIS']}.pdf", mime="application/pdf")
