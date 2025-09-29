from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Resume, ATSAnalysis, JobKeyword
from .forms import ResumeUploadForm, JobKeywordForm
from .utils import analyze_resume
from django.core.paginator import Paginator
import os


def home(request):
    """Home page with upload form"""
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save()
            industry = form.cleaned_data.get('industry', 'general')
            
            try:
                # Analyze the resume
                analysis = analyze_resume(resume, industry)
                messages.success(request, f'Resume analyzed successfully! Your ATS score is {analysis.overall_score:.1f}')
                return redirect('interactive_review', analysis_id=analysis.id)
            except Exception as e:
                messages.error(request, f'Error analyzing resume: {str(e)}')
                return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResumeUploadForm()
    
    # Get recent analyses for display
    recent_analyses = ATSAnalysis.objects.select_related('resume').order_by('-analyzed_at')[:5]
    
    context = {
        'form': form,
        'recent_analyses': recent_analyses,
    }
    return render(request, 'resume_analyzer/home.html', context)


def analysis_result(request, analysis_id):
    """Display analysis results"""
    analysis = get_object_or_404(ATSAnalysis, id=analysis_id)
    
    # Calculate component scores for visualization
    section_score = 0
    if analysis.has_contact_info:
        section_score += 25
    if analysis.has_work_experience:
        section_score += 25
    if analysis.has_education:
        section_score += 25
    if analysis.has_skills:
        section_score += 25
    
    keyword_score = min(100, analysis.keyword_density * 100 / 60) if analysis.keyword_density else 0
    
    # Readability score mapping
    if 30 <= analysis.readability_score <= 70:
        readability_score = 100
    elif 20 <= analysis.readability_score < 30 or 70 < analysis.readability_score <= 80:
        readability_score = 75
    elif 10 <= analysis.readability_score < 20 or 80 < analysis.readability_score <= 90:
        readability_score = 50
    else:
        readability_score = 25
    
    context = {
        'analysis': analysis,
        'section_score': section_score,
        'keyword_score': keyword_score,
        'readability_score': readability_score,
    }
    return render(request, 'resume_analyzer/analysis_result.html', context)


def enhanced_analysis_result(request, analysis_id):
    """Display enhanced analysis results with detailed suggestions"""
    analysis = get_object_or_404(ATSAnalysis, id=analysis_id)
    
    # Extract additional data from JSON field
    additional_data = analysis.additional_data or {}
    missing_keywords = additional_data.get('missing_keywords', [])
    present_keywords = additional_data.get('present_keywords', [])
    content_gaps = additional_data.get('content_gaps', [])
    section_improvements = additional_data.get('section_improvements', [])
    
    context = {
        'analysis': analysis,
        'missing_keywords': missing_keywords,
        'present_keywords': present_keywords,
        'content_gaps': content_gaps,
        'section_improvements': section_improvements,
    }
    return render(request, 'resume_analyzer/enhanced_analysis_result.html', context)


def interactive_review(request, analysis_id):
    """Display interactive resume review with highlighted text and inline suggestions"""
    analysis = get_object_or_404(ATSAnalysis, id=analysis_id)
    
    # Extract additional data from JSON field
    additional_data = analysis.additional_data or {}
    text_issues = additional_data.get('text_issues', [])
    
    # Calculate statistics
    total_issues = sum(len(line_issue['issues']) for line_issue in text_issues)
    high_priority_issues = sum(
        len([issue for issue in line_issue['issues'] if issue.get('priority') == 'high'])
        for line_issue in text_issues
    )
    
    # Split resume text into lines for fallback display
    resume_lines = analysis.extracted_text.split('\n') if analysis.extracted_text else []
    
    context = {
        'analysis': analysis,
        'text_issues': text_issues,
        'resume_lines': resume_lines,
        'total_issues': total_issues,
        'high_priority_issues': high_priority_issues,
    }
    return render(request, 'resume_analyzer/interactive_review.html', context)


def analysis_list(request):
    """Display list of all analyses"""
    analyses = ATSAnalysis.objects.select_related('resume').order_by('-analyzed_at')
    
    # Pagination
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'resume_analyzer/analysis_list.html', context)


def manage_keywords(request):
    """Manage job keywords for different industries"""
    if request.method == 'POST':
        form = JobKeywordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Keyword added successfully!')
            return redirect('manage_keywords')
    else:
        form = JobKeywordForm()
    
    # Get all keywords grouped by industry
    keywords_by_industry = {}
    for industry_code, industry_name in JobKeyword.INDUSTRY_CHOICES:
        keywords = JobKeyword.objects.filter(industry=industry_code).order_by('keyword')
        if keywords.exists():
            keywords_by_industry[industry_name] = keywords
    
    context = {
        'form': form,
        'keywords_by_industry': keywords_by_industry,
    }
    return render(request, 'resume_analyzer/manage_keywords.html', context)


def delete_keyword(request, keyword_id):
    """Delete a job keyword"""
    keyword = get_object_or_404(JobKeyword, id=keyword_id)
    if request.method == 'POST':
        keyword.delete()
        messages.success(request, f'Keyword "{keyword.keyword}" deleted successfully!')
    return redirect('manage_keywords')


def about(request):
    """About page explaining ATS and the tool"""
    return render(request, 'resume_analyzer/about.html')


def tips(request):
    """Tips for creating ATS-friendly resumes"""
    return render(request, 'resume_analyzer/tips.html')
