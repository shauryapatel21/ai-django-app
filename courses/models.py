import uuid
from django.db import models
from django.contrib.auth.models import User

# 1. Course details (Name, price in INR)
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.PositiveIntegerField(default=100) # In INR

    def __str__(self):
        return self.title

# 2. Student Enrollment & Payment tracking
class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    has_paid = models.BooleanField(default=False)
    order_id = models.CharField(max_length=100, blank=True)
    payment_id = models.CharField(max_length=100, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - Paid: {self.has_paid}"

# 3. Tech Events & Hackathons list
class TechEvent(models.Model):
    name = models.CharField(max_length=200)
    registration_link = models.URLField()
    date = models.DateField()
    tags = models.CharField(max_length=100, help_text="e.g. Hackathon, AI, Web3")

    def __str__(self):
        return self.name

# 4. Unlocked Certificate (Updated with manual instructor toggle)
class Certificate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # ADDED: Instructor manual unlock control for workshop generation
    is_unlocked = models.BooleanField(default=False, help_text="Check to unlock certificate for this student")
    
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)

    def __str__(self):
        status = "Unlocked" if self.is_unlocked else "Locked"
        return f"{self.user.username} - {status} ({self.certificate_id})"

# 5. Blog model added by Shaurya
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=300)
    content = models.TextField()
    author = models.CharField(max_length=100, default="AI Faculty")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title