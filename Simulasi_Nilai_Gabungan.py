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

st.set_page_config(page_title="Portal Akademik SMPN 2 Banguntapan", layout="wide")

# --- CSS (TIDAK BERUBAH) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');
.stApp { background-color: #F7F9F7; }
.stButton>button { background-color: #6B8E7B; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI PDF (SESUAI GAMBAR) ---
def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    
    p.setFont("Helvetica", 11)
    p.drawString(40*mm, h - 35*mm, f"Nama Siswa  : {user.get('Nama Siswa', '')}")
    p.drawString(40*mm, h - 42*mm, f"NIS         : {user.get('NIS', '')}")
    p.drawString(40*mm, h - 49*mm, f"Kelas       : {user.get('Kelas', '-')}")
    
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
    
    # Footer Tanda Tangan
    y_f = h - 75*mm - th
    p.setFont("Helvetica", 10)
    p.drawString(135*mm, y_f - 15*mm, "Banguntapan, 27 April 2026")
    p.drawString(135*mm, y_f - 20*mm, "Kepala Sekolah,")
    p.drawString(135*mm, y_f - 45*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- LOGIKA APLIKASI ---
if 'db_siswa' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.db_siswa = pd.read_csv(DB_FILE)
    else:
        st.session_state.db_siswa = None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

menu = st.sidebar.selectbox("MENU", ["Login Siswa", "Admin Upload"])

if menu == "Admin Upload":
    pwd = st.text_input("Password Admin", type="password")
    if pwd == "admin123":
        uploaded = st.file_uploader("Upload Excel (Wajib kolom NIS & NISN)", type=["xlsx"])
        if uploaded:
            df = pd.read_excel(uploaded)
            df.to_csv(DB_FILE, index=False)
            st.session_state.db_siswa = df
            st.success("Database diperbarui!")
else:
    if not st.session_state.logged_in:
        st.title("Login Siswa")
        u = st.text_input("NIS")
        p = st.text_input("NISN (Password)", type="password")
        if st.button("Masuk"):
            db = st.session_state.db_siswa
            if db is not None:
                db["NIS"] = db["NIS"].astype(str)
                db["NISN"] = db["NISN"].astype(str)
                res = db[(db["NIS"]==u) & (db["NISN"]==p)]
                if not res.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = res.iloc[0].to_dict()
                    st.rerun()
                else: st.error("NIS/NISN salah.")
    else:
        # Bagian perhitungan dan tampilan siswa (seperti sebelumnya)
        st.write(f"Selamat datang, {st.session_state.user_data['Nama Siswa']}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
