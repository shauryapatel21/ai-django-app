from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # -------------------------------------------------------------
    # 1. LANDING & COURSE OVERVIEW
    # -------------------------------------------------------------
    path('', views.course_home, name='course_home'),
    path('course/', views.course_home, name='course_detail'),

    # -------------------------------------------------------------
    # 2. AUTHENTICATION (DJANGO BUILT-IN + CUSTOM REGISTRATION)
    # -------------------------------------------------------------
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # -------------------------------------------------------------
    # 3. PAYMENT GATEWAY PIPELINE (RAZORPAY)
    # -------------------------------------------------------------
    path('pay/<int:course_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('preview-checkout/', views.preview_checkout, name='preview_checkout'),
    path('unlock-test/<int:course_id>/', views.unlock_test_access, name='unlock_test_access'), # Added this route

    # -------------------------------------------------------------
    # 4. DEVELOPER TOOLS & INTERACTIVE PLATFORMS
    # -------------------------------------------------------------
    path('compiler/', views.compiler_view, name='compiler'),
    path('events/', views.events_view, name='events'),

    # -------------------------------------------------------------
    # 5. VERIFIED CREDENTIALS & CERTIFICATION
    # -------------------------------------------------------------
    path('certificate/', views.generate_certificate, name='generate_certificate'),
    path('get-certificate/', views.generate_certificate, name='certificate'),
    path('verify/<str:cert_id>/', views.verify_certificate, name='verify_certificate'),
]