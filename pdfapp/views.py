from venv import logger
from django.shortcuts import render, redirect
import re
import jwt
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import logging
import bcrypt
import datetime
from pdfapp.db import get_db
from pdfapp.utils.merge import merge_pdfs
from pdfapp.utils.compress import compress_pdf
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
import logging
from django.views.decorators.http import require_POST
from pdfapp.utils.convert import convert_pdf_to_word, convert_pdf_to_images, convert_pdf_to_pptx
from pdfapp.utils.summarize import summarize_pdf
import zipfile
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from pdfapp.utils.auth import login_required_jwt
import os
import logging
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)


def generate_jwt(user):
    payload={
        'email':user['email'],
        'firstname':user['firstname'],
        'lastname':user.get('lastname', ''),  # Default to empty string if not provided
        'exp':datetime.datetime.now(datetime.UTC)+datetime.timedelta(seconds=86400), # Exactly 86400 seconds (1 day)
        'iat':datetime.datetime.now(datetime.UTC), # Time token was issued
    }
    token=jwt.encode(payload,settings.SECRET_KEY,algorithm='HS256')
    return token


def register(request):
    
    if request.method == "POST":
        db=get_db()

        register_table = db.register
        firstname = request.POST['firstname'].strip()
        lastname = request.POST['lastname'].strip()
        email = request.POST['email'].strip()
        number = request.POST['phoneno'].strip()
        password = request.POST['password'].strip()
        con_pass = request.POST['con_pass'].strip()

        # Define regex patterns
        phone_pattern = re.compile(r'^[0-9]{10}$')
        password_pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$")
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

        if not firstname or not lastname:
            messages.error(request, "First and Last name are required")
            return redirect("register")
        if not email_pattern.match(email):
            messages.error(request, "Invalid email address")
            return redirect("register")
        if not phone_pattern.match(number):
            messages.error(request, "Invalid phone number")
            return redirect("register")
        if len(password) < 8 or not password_pattern.match(password):
            messages.error(request, "Password must be at least 8 characters long and must contain at least one letter, one number, and one special character")
            return redirect("register")
        if password != con_pass:
            messages.error(request, "Password and Confirm Password must be the same")
            return redirect("register")

        existing_user = register_table.find_one({"email": email})
        if existing_user:
            messages.error(request, "User with this email already exists")
            return redirect("register")

        # If all validations pass, proceed with registration
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "phone_no": number,
            "password": hashed_password,
            "created_at": datetime.datetime.now(datetime.UTC),
            "updated_at": datetime.datetime.now(datetime.UTC),
        }
        try:
            register_table.insert_one(user)
            messages.success(request, "Registration Successful!")
            return redirect("login")
        except Exception as e:
            logger.error(f"Error saving user: {e}", exc_info=True)
            messages.error(request, "An error occurred while saving the user. Please try again.")
            return redirect("register")

    return render(request, "signup.html")

def login(request):
    if request.method == "POST":
        email = request.POST['email'].strip()
        password = request.POST['password'].strip()

        user = register_table.find_one({"email": email})
        if not user:
            messages.error(request, "User does not exist")
            return redirect("login")

        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            messages.error(request, "Invalid password")
            return redirect("login")

        token = generate_jwt(user)
        response = redirect("dashboard")
        response.set_cookie(
            "jwt_token", 
            token, 
            httponly=True, 
            max_age=86400,  # Exactly 86400 seconds (1 day)
            secure=not settings.DEBUG,  # Secure in production
            samesite='Lax',
            path='/'
        )
        messages.success(request, "Login successful!")
        return response

    return render(request, "signin.html")



@login_required_jwt
def dashboard(request):
    return render(request, "dashboard.html")
def navbar (request):
    return render(request,'navbar.html')



def compress(request):
    """
    Handle the PDF compression request.
    """
    if request.method == "POST":
        uploaded_file = request.FILES.get("pdf_file")  # Get the uploaded file
        quality = request.POST.get("option", "/ebook")  # Get the selected quality option

        if not uploaded_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect("compress")

        try:
            # Call the utility function to compress the PDF
            compressed_file_path = compress_pdf(uploaded_file, quality)
            relative_path = os.path.relpath(compressed_file_path, settings.MEDIA_ROOT)  # Get relative path for MEDIA_URL
            messages.success(request, f"PDF Compressed Successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred while compressing the PDF: {str(e)}")

    return render(request, "compress.html")


from django.utils.html import format_html


def convert(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("pdf_file")
        format_option = request.POST.get("format_option")

        if not uploaded_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect("convert")

        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
        converted_dir = os.path.join(settings.MEDIA_ROOT, "converted")
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(converted_dir, exist_ok=True)

        filename = os.path.splitext(uploaded_file.name)[0]
        temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)

        with open(temp_pdf_path, "wb") as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        try:
            if format_option == "docx":
                output_file = os.path.join(converted_dir, f"{filename}.docx")
                convert_pdf_to_word(temp_pdf_path, output_file)
                file_url = os.path.join(settings.MEDIA_URL, "converted", f"{filename}.docx")
                messages.success(request, format_html("Converted to Word! <a href='{}' download>Download Word</a>", file_url))

            elif format_option == "jpg":
                image_dir = os.path.join(converted_dir, f"{filename}_images")
                image_paths = convert_pdf_to_images(temp_pdf_path, image_dir)

                zip_path = os.path.join(converted_dir, f"{filename}.jpg.zip")
                with zipfile.ZipFile(zip_path, "w") as zf:
                    for image_path in image_paths:
                        zf.write(image_path, os.path.basename(image_path))

                file_url = os.path.join(settings.MEDIA_URL, "converted", f"{filename}.jpg.zip")
                messages.success(request, format_html("Converted to images! <a href='{}' download>Download ZIP</a>", file_url))

            elif format_option == "pptx":
                output_file = os.path.join(converted_dir, f"{filename}.pptx")
                convert_pdf_to_pptx(temp_pdf_path, output_file)
                file_url = os.path.join(settings.MEDIA_URL, "converted", f"{filename}.pptx")
                messages.success(request, format_html("Converted to PowerPoint! <a href='{}' download>Download PPTX</a>", file_url))

            else:
                messages.error(request, "Invalid format selected.")
                return redirect("convert")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("convert")

        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    return render(request, "convert.html")

def merge(request):
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == "POST":
        uploaded_files = request.FILES.getlist("pdf_files")
        success, message = merge_pdfs(uploaded_files)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect("merge")

    return render(request, "merge.html")


def edit(request):
    """
    Render the PDF editing page.
    """
    return render(request, "edit.html")

from django.shortcuts import redirect
import os
from django.conf import settings

import os
def editor_page(request, pdf_path):
    edited_path = os.path.join('edited', pdf_path)
    edited_full_path = os.path.join(settings.MEDIA_ROOT, edited_path)

    if os.path.exists(edited_full_path):
        pdf_url = settings.MEDIA_URL + edited_path
    else:
        pdf_url = settings.MEDIA_URL + pdf_path

    return render(request, 'editor.html', {'pdf_url': pdf_url, 'pdf_path': pdf_path})


def edit_page(request):
    media_dir = settings.MEDIA_ROOT
    pdf_files = []
    for filename in os.listdir(media_dir):
        if filename.lower().endswith('.pdf'):
            pdf_files.append(filename)
    return render(request, 'edit.html', {'pdf_files': pdf_files})

def ai(request):
    return render(request, 'ai.html')

def summarization_view(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        try:
            summary = summarize_pdf(pdf_file)
            logger.info("Generated summary.")
            return render(request, 'summarization.html', {'summary': summary})
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            messages.error(request, f"Error: {e}")
            return redirect('summarization')
    return render(request, 'summarization.html')

from django.http import HttpResponse
from django.conf import settings
from .utils.trans import translate_pdf
import os

def translation_view(request):
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        dest_language = request.POST.get('language')

        if not pdf_file or not dest_language:
            return render(request, 'translation.html', {'error': 'Please provide both PDF file and target language.'})

        # Save uploaded PDF temporarily
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, 'temp', pdf_file.name)
        os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
        with open(temp_pdf_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        # Translate PDF
        with open(temp_pdf_path, 'rb') as f:
            translated_pdf_io = translate_pdf(f, dest_language)

        # Prepare response to download translated PDF
        response = HttpResponse(translated_pdf_io.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="translated_{pdf_file.name}"'

        # Clean up temp file
        os.remove(temp_pdf_path)

        return response

    return render(request, 'translation.html')

@require_POST
def logout(request):
    response = redirect("login")  # or your home page
    response.delete_cookie("jwt_token")
    messages.success(request, "You have been logged out successfully.")
    return response
# Other functions remain unchanged
def admin_login(request):
    if request.method == "POST":
        email = request.POST['email'].strip()
        password = request.POST['password'].strip()

        # Check if the user is an admin
        if email == "admin@gmail.com" and password == "admin":
            return redirect("adminpanel")
            # Generate JWT token for admin
        else:
            messages.error(request, "Invalid admin credentials")
            return redirect("adminlogin")
    return render(request, "adminsignin.html")

def admin_panel(request):
    return render(request, "adminpanel.html")

def adminpanel_register(request):
    users = list(register_table.find({}, {"_id": 0, "password": 0}))
    return render(request, "adminpanel_register.html", {"users": users})

def adminpanel_register(request):
    # Fetch all registered users from the database
    users = list(register_table.find({}, {"_id": 0, "password": 0}))  # Exclude _id and password for security
    return render(request, "adminpanel.html", {"users": users})
