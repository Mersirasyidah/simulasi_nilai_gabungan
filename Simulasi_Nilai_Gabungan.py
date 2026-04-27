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
    """Memuat data dari CSV dengan pengecekan kolom agar tidak error"""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Pastikan kolom kunci dibaca sebagai string
            if "NIS" in df.columns:
                df["NIS"] = df["NIS"].astype(str).str.strip()
            if "NISN" in df.columns:
                df["NISN"] = df["NISN"].astype(str).str.strip()
            return df
        except Exception:
            return None
    return None

def save_data(df):
    """Menyimpan DataFrame ke file CSV lokal"""
    df.to_csv(DB_FILE, index=False)

def generate_template():
    """Membuat template Excel untuk Admin"""
    columns = ["NIS", "NISN", "Nama Siswa", "Kelas"]
    mapels = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]
    for mapel in mapels:
        for s in range(1, 6):
            columns.append(f"{mapel}_S{s}")
    
    df_template = pd.DataFrame(columns=columns)
    # Contoh Baris Data
    example = ["1", "0011223344", "ADELIA ARIMI AZALEA", "IX A"] + [80]*20
    df_template.loc[0] = example
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(user, detail_data, nilai_akhir):
    """Membuat laporan PDF sesuai format lampiran"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER

    # Header Laporan
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    p.line(20*mm, h - 25*mm, w - 20*mm, h - 25*mm)

    # Identitas Siswa
    p.setFont("Helvetica", 10)
    p.drawString(25*mm, h - 35*mm, f"Nama Siswa  : {user.get('Nama Siswa', '-')}")
    p.drawString(25*mm, h - 40*mm, f"NIS / NISN    : {user.get('NIS', '-')} / {user.get('NISN', '-')}")
    p.drawString(25*mm, h - 45*mm, f"Kelas             : {user.get('Kelas', '-')}")

    # Tabel Rincian Nilai
    data = [["No", "Mata Pelajaran", "S1", "S2", "S3", "S4", "S5", "Rerata", "TKA/D"]]
    for i, d in enumerate(detail_data, 1):
        data.append([
            i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], 
            d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]
        ])
    
    table = Table(data, colWidths=[10*mm, 45*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm, 20*mm, 20*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    
    tw, th = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 25*mm, h - 60*mm - th)

    # Hasil Akhir
    y_pos = h - 65*mm - th
    p.setFont("Helvetica-Bold", 11)
    p.drawString(25*mm, y_pos, f"NILAI GABUNGAN : {nilai_akhir:.2f}")
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(25*mm, y_pos - 5*mm, "Ket: Rumus = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Rapor S1-5 x 40%)")

    # Tanda Tangan
    p.setFont("Helvetica", 10)
    p.drawString(130*mm, y_pos - 20*mm, "Banguntapan, 27 April 2026")
    p.drawString(130*mm, y_pos - 25*mm, "Kepala Sekolah,")
    p.drawString(130*mm, y_pos - 50*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- 3. INISIALISASI SESSION STATE ---
if 'db_siswa' not in st.session_state:
    st.session_state.db_siswa = load_data()
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

MAPEL_UTAMA = ["Bahasa Indonesia", "Matematika", "Bahasa Inggris", "IPA"]

# --- 4. TAMPILAN UTAMA ---
st.markdown("""<div class="running-text"><marquee scrollamount="8">✨ Selamat Datang di Portal Simulasi Nilai Gabungan SMPN 2 Banguntapan ✨</marquee></div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Home / Login", "Admin Upload"])

# --- MODUL ADMIN ---
if menu == "Admin Upload":
    st.title("📂 Admin Control")
    pwd = st.text_input("Password Admin", type="password")
    
    if pwd == "admin123":
        st.success("Login Admin Berhasil")
        st.info("Gunakan tombol di bawah untuk mengelola database permanen.")
        
        # Download Template
        st.download_button(
            label="📥 Download Template Excel",
            data=generate_template(),
            file_name="template_nilai_siswa.xlsx"
        )
        
        st.divider()
        
        # Upload Data Baru
        uploaded = st.file_uploader("Upload Data Siswa (Wajib ada kolom NIS & NISN)", type=["xlsx"])
        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                df.columns = df.columns.str.strip() # Bersihkan nama kolom
                
                # Validasi Kolom Kunci
                if "NIS" in df.columns and "NISN" in df.columns:
                    save_data(df)
                    st.session_state.db_siswa = load_data()
                    st.success(f"Berhasil mengunggah dan menyimpan {len(df)} data secara permanen!")
                else:
                    st.error("Gagal: Kolom 'NIS' atau 'NISN' tidak ditemukan dalam file Excel.")
            except Exception as e:
                st.error(f"Terjadi kesalahan pembacaan file: {e}")

# --- MODUL SISWA ---
else:
    if not st.session_state.logged_in:
        st.title("🏛️ Portal Simulasi")
        st.write("Silakan login untuk melihat nilai rapor dan simulasi.")
        
        with st.form("login_form"):
            user_id = st.text_input("Username (NIS)", placeholder="Masukkan NIS")
            password = st.text_input("Password (NISN)", type="password", placeholder="Masukkan NISN")
            submit = st.form_submit_button("LOGIN")
            
            if submit:
                db = st.session_state.db_siswa
                if db is not None:
                    # Pencocokan NIS dan NISN
                    match = db[(db["NIS"] == user_id.strip()) & (db["NISN"] == password.strip())]
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("NIS atau NISN tidak ditemukan.")
                else:
                    st.warning("Database belum di-upload oleh Admin.")
    
    else:
        # Dashboard Siswa
        user = st.session_state.user_data
        st.title(f"🏫 Halo, {user.get('Nama Siswa', 'Siswa')}!")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        col_in, col_res = st.columns([1, 2])
        sim_tkad = {}
        
        with col_in:
            st.subheader("📝 Input Simulasi")
            st.write("Masukkan estimasi nilai TKA/D Anda:")
            for m in MAPEL_UTAMA:
                sim_tkad[m] = st.number_input(f"{m}", 0.0, 100.0, 0.0, step=0.01, format="%.2f", key=f"in_{m}")

        with col_res:
            total_rerata = 0
            detail_data = []
            
            try:
                for m in MAPEL_UTAMA:
                    # Ambil nilai S1-S5 dari database
                    v = [float(user[f"{m}_S{i}"]) for i in range(1, 6)]
                    avg = sum(v) / 5
                    total_rerata += avg
                    detail_data.append({
                        "Mata Pelajaran": m, 
                        "Sem-1": int(v[0]), "Sem-2": int(v[1]), "Sem-3": int(v[2]), "Sem-4": int(v[3]), "Sem-5": int(v[4]),
                        "Rerata": f"{avg:.2f}", 
                        "TKA/D": f"{sim_tkad[m]:.2f}"
                    })
                
                total_tkad = sum(sim_tkad.values())
                # Rumus: (Rerata Rapor Total * 0.4) + (Total TKAD * 0.6)
                nilai_akhir = (total_rerata * 0.4) + (total_tkad * 0.6)

                st.markdown(f"""
                    <div style="background:#E8F5E9;padding:20px;border-radius:12px;border:1px solid #A5D6A7;text-align:center;">
                        <p style="margin:0; font-size:14px; font-weight:bold; color:#2E7D32;">HASIL SIMULASI NILAI GABUNGAN</p>
                        <h1 style="font-size:50px !important;color:#1B5E20 !important;margin:10px 0;">{nilai_akhir:.2f}</h1>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔍 Lihat Rincian Rapor Semester 1-5"):
                    st.table(pd.DataFrame(detail_data))

                # Tombol Cetak PDF
                pdf_output = create_pdf(user, detail_data, nilai_akhir)
                st.download_button(
                    label="🖨️ UNDUH LAPORAN HASIL (PDF)", 
                    data=pdf_output, 
                    file_name=f"Laporan_{user['NIS']}.pdf", 
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("Data nilai di database tidak lengkap untuk akun ini. Hubungi Admin.")
