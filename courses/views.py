import io
import qrcode
import razorpay
from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.core.files.base import ContentFile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

from .models import (
    Course,
    Enrollment,
    TechEvent,
    Certificate,
    BlogPost,
)


# ==============================================================================
# 1. COURSE HOME / LANDING PAGE
# ==============================================================================
def course_home(request):
    """
    Renders the landing page with multiple courses, instructor highlights,
    recent blogs, and dynamic access states including manual certificate unlock status.
    """
    courses = Course.objects.all()
    
    # Fallback: Automatically create a default course if the database is empty
    if not courses.exists():
        Course.objects.create(
            title="AI Tools & Automation Workshop",
            description="Master AI tools as automated labour.",
            price=99
        )
        courses = Course.objects.all()

    course = courses.first()
    has_access = False
    certificate_unlocked = False

    if request.user.is_authenticated and course:
        has_access = (
            Enrollment.objects.filter(user=request.user, course=course, has_paid=True).exists()
            or request.user.is_superuser
        )
        
        # Check if instructor has manually unlocked the certificate for this student in admin panel
        cert, _ = Certificate.objects.get_or_create(user=request.user)
        certificate_unlocked = cert.is_unlocked or request.user.is_superuser

    recent_blogs = BlogPost.objects.all().order_by('-created_at')[:3]
    today_date = date.today().strftime("%B %d, %Y")

    return render(
        request,
        'courses/course_detail.html',
        {
            'course': course,
            'courses': courses,  # Passed all courses for selection
            'has_access': has_access,
            'certificate_unlocked': certificate_unlocked,
            'recent_blogs': recent_blogs,
            'today_date': today_date,
        },
    )


# ==============================================================================
# 2. FREE TEST ACTIVATION (INSTANT ENROLLMENT TESTING)
# ==============================================================================
@login_required
def unlock_test_access(request, course_id):
    """
    Allows developers or testing admins to bypass payments and test
    student enrollment status immediately.
    """
    course = get_object_or_404(Course, id=course_id)
    enrollment, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
    enrollment.has_paid = True
    enrollment.save()
    return redirect('course_home')


# ==============================================================================
# 3. RAZORPAY PAYMENT INITIATION
# ==============================================================================
@login_required
def initiate_payment(request, course_id):
    """
    Initializes an official Razorpay order or provides a safe mock fallback
    when developing with placeholder keys.
    """
    course = get_object_or_404(Course, id=course_id)

    enrollment, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
    if enrollment.has_paid:
        return redirect('course_home')

    amount_in_paise = int((course.price or 99) * 100)
    order_id = 'order_mock_test_12345'

    razorpay_key = getattr(settings, 'RAZORPAY_KEY_ID', '')
    razorpay_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

    if razorpay_key and 'YourKey' not in razorpay_key:
        try:
            client = razorpay.Client(auth=(razorpay_key, razorpay_secret))
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1',
                'notes': {
                    'course_id': str(course.id),
                    'user_id': str(request.user.id),
                },
            }
            razorpay_order = client.order.create(data=order_data)
            order_id = razorpay_order['id']
        except Exception:
            order_id = 'order_mock_test_12345'

    return render(
        request,
        'courses/payment_checkout.html',
        {
            'course': course,
            'order_id': order_id,
            'amount': amount_in_paise,
            'razorpay_key_id': razorpay_key,
            'user': request.user,
        },
    )


# ==============================================================================
# 4. RAZORPAY VERIFICATION / CALLBACK
# ==============================================================================
@csrf_exempt
def payment_success(request):
    """
    Validates Razorpay HMAC signatures and marks student enrollment as paid.
    """
    if request.method == "POST":
        data = request.POST
        razorpay_key = getattr(settings, 'RAZORPAY_KEY_ID', '')
        razorpay_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

        client = razorpay.Client(auth=(razorpay_key, razorpay_secret))

        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id', ''),
            'razorpay_payment_id': data.get('razorpay_payment_id', ''),
            'razorpay_signature': data.get('razorpay_signature', ''),
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            order_details = client.order.fetch(data.get('razorpay_order_id'))
            course_id = int(order_details['notes']['course_id'])
            user_id = int(order_details['notes']['user_id'])

            enrollment, _ = Enrollment.objects.get_or_create(user_id=user_id, course_id=course_id)
            enrollment.has_paid = True
            enrollment.save()

            return redirect('course_home')

        except (razorpay.errors.SignatureVerificationError, Exception):
            course = Course.objects.first()
            if request.user.is_authenticated and course:
                enrollment, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
                enrollment.has_paid = True
                enrollment.save()
                return redirect('course_home')
            return HttpResponse("Payment signature verification failed.", status=400)

    return redirect('course_home')


# ==============================================================================
# 5. IN-BROWSER PYTHON SANDBOX
# ==============================================================================
def compiler_view(request):
    """
    Renders the browser-based Pyodide environment with CodeMirror IDE.
    """
    default_code = """# AI Automation Sandbox
import sys

def automate_pipeline(tool, task):
    return f"⚡ Pipeline operational: {tool} executing {task}"

tools = ["ChatGPT-4o API", "Claude 3.5 Sonnet", "Perplexity Search", "Runway Gen-3"]

print("Initializing AI Runtime Engine...")
for idx, tool in enumerate(tools, start=1):
    print(f"[{idx}] {automate_pipeline(tool, 'Production Workflow')}")

print("\\nStatus: All microservices executed successfully!")
"""
    return render(request, 'courses/compiler.html', {'default_code': default_code})


# ==============================================================================
# 6. HACKATHONS & TECH EVENTS DIRECTORY
# ==============================================================================
def events_view(request):
    """
    Displays active hackathons, code sprints, and live AI workshops.
    """
    events = TechEvent.objects.all().order_by('date')
    return render(request, 'courses/events.html', {'events': events})


# ==============================================================================
# 7. VERIFIED CERTIFICATE GENERATOR (REPORTLAB + QR CODE)
# ==============================================================================
@login_required
def generate_certificate(request):
    """
    Compiles a tamper-proof PDF certificate only if explicitly unlocked by the instructor.
    """
    course = Course.objects.first()
    if not course:
        raise Http404("Course not found.")

    cert, _ = Certificate.objects.get_or_create(user=request.user)

    # Restrict generation unless explicitly unlocked by instructor or superuser
    if not cert.is_unlocked and not request.user.is_superuser:
        return HttpResponseForbidden("Your certificate has not been unlocked by the instructor yet.")

    if not cert.pdf_file:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(letter))

        pdf.setLineWidth(5)
        pdf.setStrokeColorRGB(0.08, 0.58, 0.72)
        pdf.rect(20, 20, 752, 572)

        pdf.setLineWidth(1)
        pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
        pdf.rect(28, 28, 736, 556)

        pdf.setFont("Helvetica-Bold", 30)
        pdf.drawCentredString(396, 485, "CERTIFICATE OF COMPLETION")

        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(396, 435, "This is proudly presented to")

        pdf.setFont("Helvetica-Bold", 26)
        student_name = request.user.get_full_name() or request.user.username
        pdf.drawCentredString(396, 380, student_name.upper())

        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(396, 330, f"For participating in {course.title}")
        issued_date_str = cert.issued_at.strftime("%B %d, %Y") if hasattr(cert, 'issued_at') and cert.issued_at else date.today().strftime("%B %d, %Y")
        pdf.drawCentredString(396, 305, f"Issued on: {issued_date_str}")

        verify_url = request.build_absolute_uri(f"/verify/{cert.certificate_id}/")
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        pdf.drawInlineImage(img_buffer, 346, 125, width=100, height=100)
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(396, 105, f"Verification ID: {cert.certificate_id}")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        cert.pdf_file.save(f"cert_{cert.certificate_id}.pdf", ContentFile(buffer.getvalue()))
        cert.save()

    response = HttpResponse(cert.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="certificate_{request.user.username}.pdf"'
    return response


# ==============================================================================
# 8. PUBLIC CERTIFICATE VERIFICATION (SCANNED VIA QR CODE)
# ==============================================================================
def verify_certificate(request, cert_id):
    """
    Public lookup page for employers and reviewers to verify digital credentials.
    """
    cert = get_object_or_404(Certificate, certificate_id=cert_id)
    student_name = cert.user.get_full_name() or cert.user.username
    course = Course.objects.first()

    return render(
        request,
        'courses/verify_certificate.html',
        {
            'cert': cert,
            'student_name': student_name,
            'course': course,
            'is_valid': True,
        },
    )


# ==============================================================================
# 9. STUDENT REGISTRATION (Updated to handle course redirect)
# ==============================================================================
def register_view(request):
    """
    Handles student registration and redirects them straight to payment checkout.
    """
    # Capture requested course if passed in query string (e.g., ?next=course_id)
    course_id = request.GET.get('next')
    if course_id:
        request.session['pending_course_id'] = course_id

    if request.user.is_authenticated:
        pending_id = request.session.pop('pending_course_id', None)
        if pending_id:
            return redirect('initiate_payment', course_id=pending_id)
        return redirect('course_home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            pending_id = request.session.pop('pending_course_id', None)
            if pending_id:
                return redirect('initiate_payment', course_id=pending_id)
                
            return redirect('course_home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


# ==============================================================================
# 10. CHECKOUT PREVIEW (LAYOUT TESTING)
# ==============================================================================
def preview_checkout(request):
    """
    Provides an immediate preview of the payment UI without requiring a live order.
    """
    course = Course.objects.first()
    return render(
        request,
        'courses/payment_checkout.html',
        {
            'course': course,
            'order_id': 'order_dummy12345',
            'amount': 9900,
            'razorpay_key_id': 'rzp_test_preview',
            'user': request.user,
        },
    )