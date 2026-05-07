import io
import datetime
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

def generate_mcm_pdf(mcm_instance):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Extract student details
    student = mcm_instance.student
    extra_info = student.id # ExtraInfo instance
    user = extra_info.user
    
    name = f"{user.first_name} {user.last_name}".strip()
    roll_no = extra_info.id
    batch = getattr(student, 'batch', "N/A")
    programme = getattr(student, 'programme', "N/A")
    cpi = getattr(student, 'cpi', "N/A")
    category = getattr(student, 'category', "N/A")
    mobile = getattr(extra_info, 'phone_no', "N/A")
    address = "N/A" # Address info could be complex, omitting or adding placeholder
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "MCM Scholarship Application Summary")
    
    p.setFont("Helvetica", 12)
    y = 700
    
    submit_date = str(mcm_instance.date)
    
    fields = [
        f"Application ID: {mcm_instance.id}",
        f"Date of Submission: {submit_date}",
        f"Scholarship Type: MCM",
        "",
        f"--- Student Details ---",
        f"Name: {name}",
        f"Roll No: {roll_no}",
        f"Programme: {programme}",
        f"Batch: {batch}",
        f"Category: {category}",
        f"",
        f"--- Contact Details ---",
        f"Mobile: {mobile}",
        f"Address: {address}",
        f"",
        f"--- Academic Details ---",
        f"CPI / Scores: {cpi}",
        f"",
        f"--- Family Details ---",
        f"Father Income: {mcm_instance.income_father}",
        f"Mother Income: {mcm_instance.income_mother}",
        f"Total Annual Income: {mcm_instance.annual_income}",
        f"Parent Status: {mcm_instance.parent_status}",
        f"Single Parent: {'Yes' if mcm_instance.single_parent else 'No'}",
        f"",
        f"--- Uploaded Documents List ---",
        f"Income Certificate: {'Yes' if mcm_instance.income_certificate else 'No'}",
        f"Mother Income Certificate: {'Yes' if mcm_instance.mother_income_certificate else 'No'}",
        f"Caste Certificate: {'Yes' if mcm_instance.caste_certificate else 'No'}",
        f"Score Card: {'Yes' if mcm_instance.score_card else 'No'}",
        f"Undertaking Form: {'Yes' if mcm_instance.undertaking_form else 'No'}",
        f"Application Form: {'Yes' if mcm_instance.application_form else 'No'}",
        f"Death Certificate: {'Yes' if mcm_instance.death_certificate else 'No'}",
        f"",
        f"--- Declaration / Undertaking ---",
        f"I hereby declare that all information provided is true to the best of my knowledge."
    ]
    
    for line in fields:
        if line == "":
            y -= 10
        else:
            p.drawString(50, y, line)
            y -= 20
        
        # Add new page if y goes below margin
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 750
            
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"mcm_{mcm_instance.id}.pdf")

