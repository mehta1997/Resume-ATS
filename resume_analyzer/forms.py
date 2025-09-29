from django import forms
from .models import Resume, JobKeyword


class ResumeUploadForm(forms.ModelForm):
    """Form for uploading resume files"""
    
    industry = forms.ChoiceField(
        choices=JobKeyword.INDUSTRY_CHOICES,
        initial='general',
        help_text="Select the industry to analyze keywords for",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Resume
        fields = ['name', 'email', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name (optional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email (optional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['email'].required = False
        self.fields['file'].required = True
        
        # Update help text
        self.fields['file'].help_text = "Upload your resume in PDF or Word format (max 10MB)"


class JobKeywordForm(forms.ModelForm):
    """Form for adding custom job keywords"""
    
    class Meta:
        model = JobKeyword
        fields = ['industry', 'keyword', 'weight']
        widgets = {
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'keyword': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter keyword or skill'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '5.0',
                'step': '0.1',
                'value': '1.0'
            })
        }
