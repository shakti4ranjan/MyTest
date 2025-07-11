import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import os
import re
import smtplib
from email.message import EmailMessage
import fitz 

st.title("🧹 PDF Column Cleaner (Company & Quantity Remover)")

uploaded_file = st.file_uploader("Upload your PDF", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_pdf_path = tmp_input.name

def send_email(success: bool, attachment_path=None):
    sender_email = "your_email@gmail.com"
    app_password = "your_app_password"  # Use Gmail App Password
    receiver_email = "recipient_email@gmail.com"

    msg = EmailMessage()
    if success and attachment_path:
        msg['Subject'] = '✅ PDF Cleaned Successfully'
        msg.set_content('Please find the cleaned PDF attached.')
        with open(attachment_path, "rb") as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename="Cleaned.pdf")
    else:
        msg['Subject'] = '❌ PDF Cleaning Failed'
        msg.set_content('The PDF processing encountered an error.')

    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"📧 Email sending failed: {e}")
        return False

    
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

   try:
    with open(output_pdf_path, "rb") as f:
        cleaned_pdf_bytes = f.read()

    st.download_button("📥 Download Cleaned PDF", cleaned_pdf_bytes, file_name="Steel_Data_Cleaned.pdf", mime="application/pdf")

    # Send email on success
    email_sent = send_email(success=True, attachment_path=output_pdf_path)
    if email_sent:
        st.success("📧 Email with cleaned PDF sent successfully!")

except Exception as e:
    st.error(f"⚠️ Something went wrong: {e}")
    send_email(success=False)
