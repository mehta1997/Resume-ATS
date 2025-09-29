from django.core.management.base import BaseCommand
from resume_analyzer.models import JobKeyword


class Command(BaseCommand):
    help = 'Populate the database with sample job keywords'

    def handle(self, *args, **options):
        keywords_data = {
            'tech': [
                ('Python', 2.0), ('JavaScript', 2.0), ('React', 1.8), ('Django', 1.8),
                ('SQL', 1.9), ('Git', 1.5), ('AWS', 1.7), ('Docker', 1.6),
                ('API', 1.5), ('Machine Learning', 1.8), ('Data Science', 1.8),
                ('Agile', 1.3), ('Scrum', 1.3), ('DevOps', 1.6), ('Linux', 1.4),
                ('HTML', 1.2), ('CSS', 1.2), ('Node.js', 1.6), ('MongoDB', 1.5),
            ],
            'finance': [
                ('Financial Analysis', 2.0), ('Excel', 1.8), ('Bloomberg', 1.7),
                ('Risk Management', 1.9), ('Portfolio Management', 1.8), ('Trading', 1.6),
                ('Compliance', 1.5), ('Accounting', 1.4), ('GAAP', 1.3), ('CPA', 1.7),
                ('Financial Modeling', 1.9), ('Valuation', 1.6), ('Investment', 1.5),
                ('Banking', 1.4), ('Credit Analysis', 1.6), ('Derivatives', 1.5),
            ],
            'healthcare': [
                ('Patient Care', 2.0), ('Medical Records', 1.5), ('HIPAA', 1.6),
                ('Clinical Research', 1.7), ('Healthcare Administration', 1.5),
                ('Nursing', 1.8), ('EMR', 1.4), ('Medical Terminology', 1.6),
                ('Quality Assurance', 1.5), ('Healthcare Management', 1.6),
                ('Clinical Trials', 1.7), ('Medical Coding', 1.5), ('Pharmacy', 1.4),
            ],
            'marketing': [
                ('Digital Marketing', 2.0), ('SEO', 1.8), ('Google Analytics', 1.7),
                ('Social Media', 1.6), ('Content Marketing', 1.7), ('Email Marketing', 1.5),
                ('PPC', 1.6), ('Brand Management', 1.5), ('Market Research', 1.6),
                ('Campaign Management', 1.5), ('Adobe Creative Suite', 1.4),
                ('Marketing Automation', 1.6), ('CRM', 1.5), ('A/B Testing', 1.4),
            ],
            'sales': [
                ('Sales Management', 2.0), ('Lead Generation', 1.8), ('CRM', 1.7),
                ('Account Management', 1.8), ('Cold Calling', 1.4), ('Negotiation', 1.7),
                ('Customer Relationship', 1.6), ('Sales Forecasting', 1.5),
                ('Territory Management', 1.5), ('Salesforce', 1.6), ('B2B Sales', 1.7),
                ('Pipeline Management', 1.6), ('Client Relations', 1.5),
            ],
            'education': [
                ('Curriculum Development', 1.8), ('Lesson Planning', 1.6),
                ('Classroom Management', 1.7), ('Student Assessment', 1.6),
                ('Educational Technology', 1.5), ('Special Education', 1.6),
                ('Online Learning', 1.5), ('Teaching', 2.0), ('Educational Research', 1.4),
                ('Learning Management Systems', 1.4), ('Tutoring', 1.3),
            ],
            'general': [
                ('Communication', 1.8), ('Leadership', 1.9), ('Project Management', 1.8),
                ('Team Management', 1.7), ('Problem Solving', 1.6), ('Time Management', 1.5),
                ('Critical Thinking', 1.5), ('Analytical Skills', 1.6), ('Collaboration', 1.4),
                ('Adaptability', 1.3), ('Customer Service', 1.5), ('Microsoft Office', 1.4),
                ('Attention to Detail', 1.4), ('Multitasking', 1.2), ('Organization', 1.3),
                ('Strategic Planning', 1.6), ('Process Improvement', 1.5),
            ]
        }

        created_count = 0
        for industry, keywords in keywords_data.items():
            for keyword, weight in keywords:
                keyword_obj, created = JobKeyword.objects.get_or_create(
                    industry=industry,
                    keyword=keyword,
                    defaults={'weight': weight}
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} keywords')
        )
