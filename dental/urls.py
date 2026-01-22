# urls.py (app urls)
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path("signup/", signup, name="signup"),
    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.patient_create, name='patient_create'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    
    # Appointments
    path('appointments/', views.appointment_calendar, name='appointment_calendar'),
    path('appointments/new/', views.appointment_create, name='appointment_create'),
    
    # Treatments
    path('patients/<int:patient_id>/treatments/new/', views.treatment_create, name='treatment_create'),
    
    # Dental Chart - AJAX endpoints
    path('api/tooth/<int:tooth_id>/update/', views.tooth_update, name='tooth_update'),
    
    # Periodontal Exams
    path('periodontal-exam/<int:exam_id>/', views.periodontal_exam_detail, name='periodontal_exam_detail'),
    path('patients/<int:patient_id>/periodontal-exam/new/', views.periodontal_exam_create, name='periodontal_exam_create'),

]
