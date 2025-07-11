import streamlit as st

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import os
import re

st.title("🧹 PDF Column Cleaner (Company & Quantity Remover)")

uploaded_file = st.file_uploader("Upload your PDF", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_pdf_path = tmp_input.name

    # Step 1: Extract Text
    doc = fitz.open(input_pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    # Step 2: Dynamically parse records
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    records = []
    current_record = []
    
    for line in lines:
        if re.match(r"^\d+\s", line):  # new record starts
            if current_record:
                records.append(current_record)
            current_record = [line]
        else:
            current_record.append(line)
    if current_record:
        records.append(current_record)

    output_rows = []
    for rec in records:
        flat = " ".join(rec).split()
        if len(flat) >= 8:
            try:
                output_rows.append([flat[0], flat[1], flat[3], flat[5], flat[7]])
            except:
                continue

    st.success(f"✅ Processed {len(output_rows)-1} records")
    st.write("### Sample Data (First 10 Rows):")
    st.table(output_rows[:10])

    # Step 3: Save cleaned PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
        output_pdf_path = tmp_out.name
        c = canvas.Canvas(output_pdf_path, pagesize=letter)
        width, height = letter
        y = height - 40

        # Write header
        x = 40
        for val in output_rows[0]:
            c.drawString(x, y, str(val))
            x += 100
        y -= 20

        # Write rows
        for row in output_rows[1:]:
            x = 40
            for val in row:
                c.drawString(x, y, str(val))
                x += 100
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 40
        c.save()

    with open(output_pdf_path, "rb") as f:
        st.download_button("📥 Download Cleaned PDF", f.read(), file_name="Steel_Data_Cleaned.pdf", mime="application/pdf")
