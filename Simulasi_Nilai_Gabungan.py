def create_pdf(user, detail_data, nilai_akhir):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER
    
    # Judul Laporan (Disesuaikan agar lebih rapi)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w/2, h - 15*mm, "LAPORAN HASIL NILAI GABUNGAN")
    p.drawCentredString(w/2, h - 21*mm, "TAHUN PELAJARAN 2024/2025")
    
    # Informasi Identitas (Sesuai Gambar)
    p.setFont("Helvetica", 11)
    p.drawString(40*mm, h - 35*mm, f"Nama Siswa")
    p.drawString(70*mm, h - 35*mm, f": {user.get('Nama Siswa', '')}")
    
    p.drawString(40*mm, h - 42*mm, f"NIS")
    p.drawString(70*mm, h - 42*mm, f": {user.get('NIS', '')}")
    
    p.drawString(40*mm, h - 49*mm, f"Kelas")
    p.drawString(70*mm, h - 49*mm, f": {user.get('Kelas', '-')}")
    
    # Persiapan Data Tabel
    # Header 2 baris sesuai gambar
    data = [
        ["No", "Mata Pelajaran", "Nilai Rapor Sem 1-5", "", "", "", "", "Rerata\nSem 1-5", "Nilai TKA/D"],
        ["", "", "Sem-1", "Sem-2", "Sem-3", "Sem-4", "Sem-5", "", ""]
    ]
    
    total_rerata = 0
    total_tkad = 0
    
    for i, d in enumerate(detail_data, 1):
        data.append([
            i, d["Mata Pelajaran"], d["Sem-1"], d["Sem-2"], d["Sem-3"], 
            d["Sem-4"], d["Sem-5"], d["Rerata"], d["TKA/D"]
        ])
        total_rerata += float(d["Rerata"])
        total_tkad += float(d["TKA/D"])
    
    # Baris JUMLAH
    data.append(["JUMLAH", "", "", "", "", "", "", f"{total_rerata:.2f}", f"{total_tkad:.2f}"])
    
    # Baris NILAI GABUNGAN
    data.append(["NILAI GABUNGAN", "", "", "", "", "", "", "", f"{nilai_akhir:.2f}"])
    
    # Pengaturan Gaya Tabel (Warna, Garis, dan Spanning)
    table = Table(data, colWidths=[10*mm, 45*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 22*mm, 25*mm])
    
    style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        
        # Header Styling
        ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
        ('SPAN', (0, 0), (0, 1)),     # Span No
        ('SPAN', (1, 0), (1, 1)),     # Span Mata Pelajaran
        ('SPAN', (2, 0), (6, 0)),     # Span Nilai Rapor (Header)
        ('SPAN', (7, 0), (7, 1)),     # Span Rerata
        ('SPAN', (8, 0), (8, 1)),     # Span TKA/D
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        
        # Baris Jumlah Styling
        ('SPAN', (0, -2), (6, -2)),   # Gabungkan No s/d Sem-5 pada baris JUMLAH
        ('FONTNAME', (0, -2), (0, -2), 'Helvetica-Bold'),
        
        # Baris Nilai Gabungan Styling
        ('BACKGROUND', (0, -1), (7, -1), colors.lightgrey), # Warna abu-abu pada label
        ('SPAN', (0, -1), (7, -1)),                         # Gabung label Nilai Gabungan
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
    ])
    
    table.setStyle(style)
    
    # Menentukan posisi tabel di PDF
    tw, th = table.wrapOn(p, 20*mm, h - 60*mm)
    table.drawOn(p, 15*mm, h - 60*mm - th)
    
    # Footer: Keterangan Rumus & Tanda Tangan
    y_footer = h - 75*mm - th
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(15*mm, y_footer, "Ket :")
    p.drawString(15*mm, y_footer - 4*mm, "Rumus Nilai Gabungan = ((Nilai TKA + TKAD) x 60%) + (Jumlah Rerata Nilai Rapor Semester 1-5 x 40%)")
    
    p.setFont("Helvetica", 10)
    p.drawString(135*mm, y_footer - 15*mm, "Banguntapan, 27 April 2026")
    p.drawString(135*mm, y_footer - 20*mm, "Kepala Sekolah,")
    p.drawString(135*mm, y_footer - 45*mm, "( ________________________ )")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
