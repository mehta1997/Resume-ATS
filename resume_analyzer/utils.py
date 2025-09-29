import os
import re
import docx
import PyPDF2
import textstat
from django.conf import settings
from .models import JobKeyword, ATSAnalysis
from collections import Counter
import nltk


def download_nltk_data():
    """Download required NLTK data"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_text_from_resume(resume):
    """Extract text from uploaded resume file"""
    file_path = resume.file.path
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        return ""


def check_contact_info(text):
    """Check if resume contains contact information"""
    text_lower = text.lower()
    
    # Check for email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    has_email = bool(re.search(email_pattern, text, re.IGNORECASE))
    
    # Check for phone number
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
        r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',      # (123) 456-7890
        r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'  # International
    ]
    has_phone = any(re.search(pattern, text) for pattern in phone_patterns)
    
    return has_email or has_phone


def check_section_presence(text):
    """Check for presence of common resume sections"""
    text_lower = text.lower()
    
    # Define section keywords
    sections = {
        'experience': ['experience', 'work history', 'employment', 'professional experience', 'career'],
        'education': ['education', 'academic', 'degree', 'university', 'college', 'school'],
        'skills': ['skills', 'technical skills', 'competencies', 'proficiencies', 'expertise'],
    }
    
    results = {}
    for section, keywords in sections.items():
        results[section] = any(keyword in text_lower for keyword in keywords)
    
    return results


def calculate_keyword_density(text, industry):
    """Calculate keyword density based on industry-specific keywords"""
    if not text:
        return 0.0
    
    # Get keywords for the industry
    keywords = JobKeyword.objects.filter(industry=industry).values_list('keyword', 'weight')
    
    if not keywords:
        # Use general keywords if industry-specific ones don't exist
        keywords = JobKeyword.objects.filter(industry='general').values_list('keyword', 'weight')
    
    if not keywords:
        return 0.0
    
    text_lower = text.lower()
    total_weight = 0
    matched_weight = 0
    
    for keyword, weight in keywords:
        total_weight += weight
        if keyword.lower() in text_lower:
            matched_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return (matched_weight / total_weight) * 100


def check_formatting_issues(text):
    """Check for common formatting issues that affect ATS readability"""
    issues = {
        'has_images': False,  # Can't detect from text, would need file analysis
        'has_tables': False,  # Simple check for table-like structures
        'has_special_characters': False
    }
    
    # Check for table-like structures (multiple tabs or excessive spacing)
    if re.search(r'\t{2,}|\s{5,}', text):
        issues['has_tables'] = True
    
    # Check for excessive special characters
    special_char_count = len(re.findall(r'[^\w\s\-.,;:!?()@]', text))
    if special_char_count > len(text) * 0.05:  # More than 5% special characters
        issues['has_special_characters'] = True
    
    return issues


def analyze_missing_keywords(text, industry):
    """Analyze what keywords are missing from the resume"""
    keywords = JobKeyword.objects.filter(industry=industry).order_by('-weight')[:20]
    if not keywords:
        keywords = JobKeyword.objects.filter(industry='general').order_by('-weight')[:15]
    
    text_lower = text.lower()
    missing_keywords = []
    present_keywords = []
    
    for keyword_obj in keywords:
        keyword = keyword_obj.keyword.lower()
        if keyword in text_lower:
            present_keywords.append((keyword_obj.keyword, keyword_obj.weight))
        else:
            missing_keywords.append((keyword_obj.keyword, keyword_obj.weight))
    
    return missing_keywords[:10], present_keywords  # Return top 10 missing


def analyze_text_issues(text, industry):
    """Analyze specific text issues that can be highlighted and improved"""
    issues = []
    lines = text.split('\n')
    
    # Get industry keywords for suggestions
    keywords_objs = JobKeyword.objects.filter(industry=industry).order_by('-weight')[:15]
    if not keywords_objs:
        keywords_objs = JobKeyword.objects.filter(industry='general').order_by('-weight')[:10]
    
    industry_keywords = [kw.keyword.lower() for kw in keywords_objs]
    
    # Define weak phrases to strong alternatives
    weak_to_strong = {
        'responsible for': ['Led', 'Managed', 'Oversaw', 'Directed'],
        'duties included': ['Achieved', 'Delivered', 'Executed', 'Accomplished'],
        'worked on': ['Developed', 'Built', 'Created', 'Implemented'],
        'helped with': ['Collaborated on', 'Contributed to', 'Assisted in', 'Supported'],
        'worked with': ['Partnered with', 'Collaborated with', 'Coordinated with'],
        'was involved in': ['Participated in', 'Contributed to', 'Played a key role in'],
        'did': ['Executed', 'Performed', 'Completed', 'Delivered'],
        'made': ['Created', 'Developed', 'Built', 'Established'],
    }
    
    # Analyze each line for issues
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower().strip()
        if not line_lower or len(line_lower) < 10:  # Skip short lines
            continue
        
        line_issues = []
        
        # Check for weak verbs
        for weak_phrase, strong_alternatives in weak_to_strong.items():
            if weak_phrase in line_lower:
                # Find the position of the weak phrase
                start_pos = line_lower.find(weak_phrase)
                end_pos = start_pos + len(weak_phrase)
                
                line_issues.append({
                    'type': 'weak_verb',
                    'start': start_pos,
                    'end': end_pos,
                    'text': weak_phrase,
                    'suggestion': f"Replace with stronger verbs like: {', '.join(strong_alternatives[:3])}",
                    'alternatives': strong_alternatives,
                    'priority': 'high'
                })
        
        # Check for missing quantifiable data
        has_numbers = bool(re.search(r'\d+%|\$[\d,]+|\d+\+|\d+ (years|months|people|clients|projects)', line_lower))
        has_achievement_words = any(word in line_lower for word in ['increased', 'decreased', 'improved', 'reduced', 'grew', 'achieved', 'delivered', 'completed'])
        
        if has_achievement_words and not has_numbers:
            line_issues.append({
                'type': 'missing_quantification',
                'start': 0,
                'end': len(line),
                'text': line.strip(),
                'suggestion': 'Add specific numbers, percentages, or metrics to quantify this achievement',
                'examples': ['25% increase', '$50K savings', '10+ projects', '3 years experience'],
                'priority': 'medium'
            })
        
        # Check for missing keywords
        missing_keywords_in_line = []
        for keyword in industry_keywords[:8]:  # Check top keywords
            if keyword not in line_lower and any(word in line_lower for word in ['skills', 'experience', 'expertise', 'proficient']):
                missing_keywords_in_line.append(keyword)
        
        if missing_keywords_in_line and ('skills' in line_lower or 'experience' in line_lower):
            line_issues.append({
                'type': 'missing_keywords',
                'start': 0,
                'end': len(line),
                'text': line.strip(),
                'suggestion': f"Consider adding relevant keywords: {', '.join(missing_keywords_in_line[:4])}",
                'keywords': missing_keywords_in_line[:4],
                'priority': 'medium'
            })
        
        # Check for generic phrases
        generic_phrases = {
            'team player': 'Collaborated effectively with cross-functional teams',
            'hard worker': 'Delivered consistent high-quality results',
            'detail oriented': 'Maintained 99%+ accuracy in data analysis',
            'fast learner': 'Rapidly acquired new technical skills',
            'go-getter': 'Proactively identified and pursued opportunities'
        }
        
        for generic, specific in generic_phrases.items():
            if generic in line_lower:
                start_pos = line_lower.find(generic)
                end_pos = start_pos + len(generic)
                line_issues.append({
                    'type': 'generic_phrase',
                    'start': start_pos,
                    'end': end_pos,
                    'text': generic,
                    'suggestion': f'Replace with specific example: "{specific}"',
                    'alternative': specific,
                    'priority': 'low'
                })
        
        if line_issues:
            issues.append({
                'line_number': line_num,
                'line_text': line.strip(),
                'issues': line_issues
            })
    
    return issues


def analyze_content_gaps(text):
    """Analyze specific content gaps in the resume"""
    text_lower = text.lower()
    gaps = []
    
    # Check for quantifiable achievements
    has_numbers = bool(re.search(r'\d+%|\$\d+|\d+\+|increased by \d+|reduced \d+|managed \d+', text))
    if not has_numbers:
        gaps.append({
            'type': 'quantifiable_achievements',
            'title': 'Add Quantifiable Achievements',
            'description': 'Include numbers, percentages, and metrics to show your impact',
            'examples': ['Increased sales by 25%', 'Managed a team of 8 people', 'Reduced costs by $50,000', 'Improved efficiency by 30%']
        })
    
    # Check for action verbs
    weak_verbs = ['responsible for', 'duties included', 'worked on', 'helped with']
    has_weak_verbs = any(verb in text_lower for verb in weak_verbs)
    if has_weak_verbs:
        gaps.append({
            'type': 'action_verbs',
            'title': 'Use Stronger Action Verbs',
            'description': 'Replace weak phrases with powerful action verbs',
            'examples': ['Led', 'Developed', 'Implemented', 'Achieved', 'Optimized', 'Streamlined', 'Spearheaded', 'Delivered']
        })
    
    # Check for industry certifications
    cert_keywords = ['certified', 'certification', 'license', 'credential']
    has_certs = any(cert in text_lower for cert in cert_keywords)
    if not has_certs:
        gaps.append({
            'type': 'certifications',
            'title': 'Add Relevant Certifications',
            'description': 'Include professional certifications, licenses, and credentials',
            'examples': ['PMP Certification', 'AWS Certified', 'Google Analytics Certified', 'CPA License']
        })
    
    # Check for soft skills
    soft_skills = ['leadership', 'communication', 'problem solving', 'teamwork', 'collaboration']
    found_soft_skills = sum(1 for skill in soft_skills if skill in text_lower)
    if found_soft_skills < 2:
        gaps.append({
            'type': 'soft_skills',
            'title': 'Highlight Soft Skills',
            'description': 'Include important soft skills that employers value',
            'examples': ['Leadership', 'Communication', 'Problem Solving', 'Team Collaboration', 'Adaptability', 'Critical Thinking']
        })
    
    return gaps


def analyze_section_improvements(analysis):
    """Provide specific suggestions for each resume section"""
    improvements = []
    
    if not analysis.has_contact_info:
        improvements.append({
            'section': 'Contact Information',
            'priority': 'high',
            'suggestions': [
                'Add your full name at the top of the resume',
                'Include a professional email address',
                'Add your phone number with area code',
                'Include your city and state (zip code optional)',
                'Add LinkedIn profile URL',
                'Consider adding your professional website or portfolio'
            ]
        })
    
    if not analysis.has_work_experience:
        improvements.append({
            'section': 'Work Experience',
            'priority': 'high',
            'suggestions': [
                'Create a "Work Experience" or "Professional Experience" section',
                'List jobs in reverse chronological order',
                'Include job title, company name, location, and dates',
                'Use 3-5 bullet points per job describing achievements',
                'Start each bullet point with an action verb',
                'Quantify your accomplishments with numbers and percentages'
            ]
        })
    
    if not analysis.has_education:
        improvements.append({
            'section': 'Education',
            'priority': 'medium',
            'suggestions': [
                'Add an "Education" section',
                'Include degree type, major, school name, and graduation year',
                'Add GPA if it\'s 3.5 or higher',
                'Include relevant coursework for entry-level positions',
                'Add academic honors or awards if applicable'
            ]
        })
    
    if not analysis.has_skills:
        improvements.append({
            'section': 'Skills',
            'priority': 'high',
            'suggestions': [
                'Create a "Skills" or "Technical Skills" section',
                'List both hard and soft skills',
                'Include programming languages, software, and tools',
                'Add industry-specific skills and certifications',
                'Use keywords from the job description',
                'Consider categorizing skills (e.g., Technical, Languages, Certifications)'
            ]
        })
    
    # Always suggest additional sections
    improvements.append({
        'section': 'Additional Sections to Consider',
        'priority': 'low',
        'suggestions': [
            'Professional Summary - 2-3 lines highlighting your value proposition',
            'Certifications - List relevant professional certifications',
            'Projects - Showcase relevant personal or professional projects',
            'Awards & Recognition - Include professional achievements',
            'Volunteer Experience - Add relevant volunteer work',
            'Publications - Include relevant articles or papers'
        ]
    })
    
    return improvements


def generate_recommendations(analysis):
    """Generate detailed recommendations based on analysis results"""
    recommendations = []
    
    # Score-based recommendations
    if analysis.overall_score < 60:
        recommendations.append("Your resume needs significant improvement for ATS compatibility.")
    elif analysis.overall_score < 80:
        recommendations.append("Your resume is moderately ATS-friendly but could be improved.")
    
    # Section-based recommendations
    if not analysis.has_contact_info:
        recommendations.append("Add clear contact information including email and phone number.")
    
    if not analysis.has_work_experience:
        recommendations.append("Include a dedicated work experience or employment history section.")
    
    if not analysis.has_education:
        recommendations.append("Add an education section with your degrees and certifications.")
    
    if not analysis.has_skills:
        recommendations.append("Include a skills section highlighting your technical and soft skills.")
    
    # Keyword density recommendations
    if analysis.keyword_density < 20:
        recommendations.append("Include more industry-relevant keywords and skills in your resume.")
    elif analysis.keyword_density > 80:
        recommendations.append("Your keyword density might be too high - ensure natural language flow.")
    
    # Readability recommendations
    if analysis.readability_score < 30:
        recommendations.append("Simplify your language to improve readability.")
    elif analysis.readability_score > 90:
        recommendations.append("Consider adding more detailed descriptions to showcase your experience.")
    
    # Technical issues
    if analysis.has_tables:
        recommendations.append("Avoid complex tables - use simple bullet points instead.")
    
    if analysis.has_special_characters:
        recommendations.append("Remove excessive special characters and use standard formatting.")
    
    # Word count recommendations
    if analysis.word_count < 200:
        recommendations.append("Your resume might be too brief - consider adding more details.")
    elif analysis.word_count > 1000:
        recommendations.append("Your resume might be too long - try to be more concise.")
    
    return "; ".join(recommendations)


def calculate_overall_score(analysis):
    """Calculate overall ATS compatibility score"""
    score = 0
    
    # Section completeness (40 points total)
    section_score = 0
    if analysis.has_contact_info:
        section_score += 10
    if analysis.has_work_experience:
        section_score += 10
    if analysis.has_education:
        section_score += 10
    if analysis.has_skills:
        section_score += 10
    
    score += section_score
    
    # Keyword density (25 points)
    if analysis.keyword_density >= 20:
        keyword_score = min(25, analysis.keyword_density * 25 / 60)  # Cap at 25 points
    else:
        keyword_score = analysis.keyword_density * 25 / 20
    
    score += keyword_score
    
    # Readability (20 points)
    if 30 <= analysis.readability_score <= 70:
        readability_score = 20
    elif 20 <= analysis.readability_score < 30 or 70 < analysis.readability_score <= 80:
        readability_score = 15
    elif 10 <= analysis.readability_score < 20 or 80 < analysis.readability_score <= 90:
        readability_score = 10
    else:
        readability_score = 5
    
    score += readability_score
    
    # Technical issues (15 points - deductions)
    technical_score = 15
    if analysis.has_tables:
        technical_score -= 5
    if analysis.has_special_characters:
        technical_score -= 5
    if analysis.has_images:
        technical_score -= 5
    
    score += max(0, technical_score)
    
    return min(100, max(0, score))


def analyze_resume(resume, industry='general'):
    """Perform complete ATS analysis on a resume"""
    # Ensure NLTK data is downloaded
    download_nltk_data()
    
    # Extract text
    extracted_text = extract_text_from_resume(resume)
    
    if not extracted_text:
        # Create minimal analysis if text extraction failed
        analysis = ATSAnalysis.objects.create(
            resume=resume,
            extracted_text="Failed to extract text",
            word_count=0,
            overall_score=0,
            recommendations="Unable to analyze resume - file may be corrupted or in unsupported format."
        )
        return analysis
    
    # Basic text analysis
    word_count = len(extracted_text.split())
    
    # Check sections
    has_contact_info = check_contact_info(extracted_text)
    sections = check_section_presence(extracted_text)
    
    # Calculate scores
    keyword_density = calculate_keyword_density(extracted_text, industry)
    readability_score = textstat.flesch_reading_ease(extracted_text)
    
    # Check formatting issues
    formatting_issues = check_formatting_issues(extracted_text)
    
    # Create analysis object
    analysis = ATSAnalysis.objects.create(
        resume=resume,
        extracted_text=extracted_text,
        word_count=word_count,
        has_contact_info=has_contact_info,
        has_work_experience=sections.get('experience', False),
        has_education=sections.get('education', False),
        has_skills=sections.get('skills', False),
        keyword_density=keyword_density,
        readability_score=readability_score,
        has_tables=formatting_issues['has_tables'],
        has_special_characters=formatting_issues['has_special_characters'],
        has_images=formatting_issues['has_images']
    )
    
    # Calculate overall score
    analysis.overall_score = calculate_overall_score(analysis)
    
    # Generate recommendations
    analysis.recommendations = generate_recommendations(analysis)
    
    # Analyze additional details
    missing_keywords, present_keywords = analyze_missing_keywords(extracted_text, industry)
    content_gaps = analyze_content_gaps(extracted_text)
    section_improvements = analyze_section_improvements(analysis)
    text_issues = analyze_text_issues(extracted_text, industry)
    
    # Store additional analysis data in JSON field
    analysis.additional_data = {
        'missing_keywords': missing_keywords,
        'present_keywords': present_keywords,
        'content_gaps': content_gaps,
        'section_improvements': section_improvements,
        'text_issues': text_issues,
        'industry': industry
    }
    
    # Save analysis
    analysis.save()
    
    # Mark resume as processed
    resume.processed = True
    resume.save()
    
    return analysis
