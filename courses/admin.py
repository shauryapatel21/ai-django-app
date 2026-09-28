from django.contrib import admin
from .models import Course, Enrollment, TechEvent, Certificate, BlogPost

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'has_paid', 'payment_id', 'enrolled_at')
    list_filter = ('has_paid', 'course')
    search_fields = ('user__username', 'user__email', 'payment_id')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'certificate_id', 'issued_at')
    readonly_fields = ('certificate_id', 'issued_at')
    search_fields = ('user__username', 'certificate_id')

@admin.register(TechEvent)
class TechEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'tags')
    search_fields = ('name', 'tags')

admin.site.register(Course)

# --- Added by Shaurya: Blog Management ---
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'author')