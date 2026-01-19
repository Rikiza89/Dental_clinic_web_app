# forms.py - Add this to a separate forms.py file
from django import forms
from .models import Patient, Appointment, Treatment, MedicalHistory


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'email', 'phone', 'address', 'city', 'postal_code',
            'insurance_provider', 'insurance_number', 'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        exclude = ['patient', 'updated_at']
        widgets = {
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'current_medications': forms.Textarea(attrs={'rows': 3}),
            'previous_dental_problems': forms.Textarea(attrs={'rows': 3}),
            'other_conditions': forms.Textarea(attrs={'rows': 3}),
            'last_dental_visit': forms.DateInput(attrs={'type': 'date'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient', 'appointment_date', 'appointment_time',
            'duration', 'reason', 'status', 'notes'
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = [
            'treatment_date', 'tooth_number', 'procedure_code',
            'procedure_name', 'description', 'cost',
            'insurance_covered', 'patient_paid', 'xray_image', 'notes'
        ]
        widgets = {
            'treatment_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }