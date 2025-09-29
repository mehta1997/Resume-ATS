from django.db import models
from django.core.validators import FileExtensionValidator
import os


def resume_upload_path(instance, filename):
    """Generate upload path for resume files"""
    return os.path.join('resumes', filename)


class Resume(models.Model):
    """Model to store uploaded resume information"""
    name = models.CharField(max_length=255, help_text="Name of the person (optional)")
    email = models.EmailField(blank=True, null=True, help_text="Email address (optional)")
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc'])],
        help_text="Upload PDF or Word document"
    )
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.original_filename} - {self.uploaded_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
        super().save(*args, **kwargs)


class ATSAnalysis(models.Model):
    """Model to store ATS analysis results"""
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='analysis')
    
    # Text extraction
    extracted_text = models.TextField(help_text="Raw text extracted from resume")
    word_count = models.IntegerField(default=0)
    
    # ATS Score components
    overall_score = models.FloatField(default=0.0, help_text="Overall ATS compatibility score (0-100)")
    
    # Formatting analysis
    has_clear_sections = models.BooleanField(default=False)
    has_contact_info = models.BooleanField(default=False)
    has_work_experience = models.BooleanField(default=False)
    has_education = models.BooleanField(default=False)
    has_skills = models.BooleanField(default=False)
    
    # Content analysis
    keyword_density = models.FloatField(default=0.0, help_text="Percentage of relevant keywords")
    readability_score = models.FloatField(default=0.0, help_text="Flesch reading ease score")
    
    # Technical issues
    has_images = models.BooleanField(default=False, help_text="Contains images or graphics")
    has_tables = models.BooleanField(default=False, help_text="Contains tables")
    has_special_characters = models.BooleanField(default=False, help_text="Contains special characters")
    
    # Recommendations
    recommendations = models.TextField(blank=True, help_text="Suggestions for improvement")
    
    # Additional analysis data (JSON field for detailed suggestions)
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Analysis metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    analysis_version = models.CharField(max_length=10, default="1.0")
    
    def __str__(self):
        return f"Analysis for {self.resume.original_filename} - Score: {self.overall_score:.1f}"
    
    def get_score_color(self):
        """Return CSS color class based on score"""
        if self.overall_score >= 80:
            return 'success'  # Green
        elif self.overall_score >= 60:
            return 'warning'  # Yellow
        else:
            return 'danger'   # Red
    
    def get_score_grade(self):
        """Return letter grade based on score"""
        if self.overall_score >= 90:
            return 'A'
        elif self.overall_score >= 80:
            return 'B'
        elif self.overall_score >= 70:
            return 'C'
        elif self.overall_score >= 60:
            return 'D'
        else:
            return 'F'


class JobKeyword(models.Model):
    """Model to store common job keywords for different industries"""
    INDUSTRY_CHOICES = [
        ('tech', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('education', 'Education'),
        ('general', 'General'),
    ]
    
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES)
    keyword = models.CharField(max_length=100)
    weight = models.FloatField(default=1.0, help_text="Importance weight for this keyword")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['industry', 'keyword']
    
    def __str__(self):
        return f"{self.industry}: {self.keyword} (weight: {self.weight})"
