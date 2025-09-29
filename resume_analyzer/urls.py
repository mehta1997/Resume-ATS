from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('analysis/<int:analysis_id>/', views.analysis_result, name='analysis_result'),
    path('analysis/<int:analysis_id>/enhanced/', views.enhanced_analysis_result, name='enhanced_analysis_result'),
    path('analysis/<int:analysis_id>/interactive/', views.interactive_review, name='interactive_review'),
    path('analyses/', views.analysis_list, name='analysis_list'),
    path('keywords/', views.manage_keywords, name='manage_keywords'),
    path('keywords/delete/<int:keyword_id>/', views.delete_keyword, name='delete_keyword'),
    path('about/', views.about, name='about'),
    path('tips/', views.tips, name='tips'),
]
