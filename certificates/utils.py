from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from io import BytesIO

def generate_certificate_pdf(student_name, course_name, date, cert_id):
    buffer = BytesIO()
    # Create a landscape A4 canvas
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # --- 1. PREMIUM BACKGROUND & BORDERS ---
    p.setStrokeColor(HexColor("#1A237E")) # Deep Navy
    p.setLineWidth(20)
    p.rect(0, 0, width, height) 

    p.setStrokeColor(HexColor("#D4AF37")) # Metallic Gold
    p.setLineWidth(3)
    p.rect(0.3*inch, 0.3*inch, width-0.6*inch, height-0.6*inch)

    # --- 2. DECORATIVE CORNER ELEMENTS ---
    p.setFillColor(HexColor("#D4AF37"))
    p.circle(0, 0, 0.5*inch, fill=1) 
    p.circle(width, 0, 0.5*inch, fill=1) 
    p.circle(0, height, 0.5*inch, fill=1) 
    p.circle(width, height, 0.5*inch, fill=1) 

    # --- 3. MAIN TITLES ---
    p.setFillColor(HexColor("#1A237E"))
    p.setFont("Times-Bold", 45)
    p.drawCentredString(width/2, height-1.8*inch, "CERTIFICATE OF COMPLETION")
    
    p.setFillColor(HexColor("#444444"))
    p.setFont("Times-Roman", 20)
    p.drawCentredString(width/2, height-2.5*inch, "This acknowledges that")

    # --- 4. THE GRADUATE'S NAME ---
    p.setFillColor(HexColor("#D4AF37")) 
    p.setFont("Times-BoldItalic", 50)
    p.drawCentredString(width/2, height-3.5*inch, student_name.title())

    # --- 5. COURSE DETAILS ---
    p.setFillColor(HexColor("#444444"))
    p.setFont("Times-Roman", 20)
    p.drawCentredString(width/2, height-4.2*inch, "has successfully mastered all requirements for")
    
    p.setFillColor(HexColor("#1A237E"))
    p.setFont("Times-Bold", 28)
    p.drawCentredString(width/2, height-5.0*inch, f"{course_name}")

    # --- 6. THE SEAL ---
    p.setStrokeColor(HexColor("#D4AF37"))
    p.setFillColor(HexColor("#D4AF37"))
    p.circle(width/2, 1.8*inch, 0.6*inch, stroke=1, fill=1)
    p.setFillColor(HexColor("#FFFFFF"))
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(width/2, 1.9*inch, "OFFICIAL")
    p.drawCentredString(width/2, 1.7*inch, "SEAL")

    # --- 7. DATE & SIGNATURE ---
    p.setFillColor(HexColor("#1A237E"))
    p.setFont("Times-Bold", 14)
    p.drawString(1.5*inch, 1.5*inch, f"DATE: {date}")
    p.line(1.5*inch, 1.7*inch, 3.5*inch, 1.7*inch)

    p.drawCentredString(width-2.5*inch, 1.5*inch, "DIRECTOR, SMART LEARN")
    p.line(width-4.0*inch, 1.7*inch, width-1.0*inch, 1.7*inch)
    p.setFont("Times-Italic", 18)
    p.drawCentredString(width-2.5*inch, 1.9*inch, "Vro Instructor")

    # --- 8. VERIFICATION ID (The Footer) ---
    p.setFillColor(HexColor("#777777"))
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, 0.6*inch, f"Certificate ID: {cert_id}")
    p.drawCentredString(width/2, 0.45*inch, "Verify at: smartlearn.vro/verify")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer