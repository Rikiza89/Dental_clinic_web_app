# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Patient, Appointment, Treatment, Invoice
from .forms import PatientForm, AppointmentForm, TreatmentForm

from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
    
@login_required
def dashboard(request):
    """Main dashboard view"""
    today = timezone.now().date()
    
    # Statistics
    total_patients = Patient.objects.filter(is_active=True).count()
    today_appointments = Appointment.objects.filter(
        appointment_date=today,
        status__in=['scheduled', 'confirmed']
    ).count()
    
    pending_invoices = Invoice.objects.filter(
        status__in=['sent', 'overdue']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Recent appointments
    upcoming_appointments = Appointment.objects.filter(
        appointment_date__gte=today,
        status__in=['scheduled', 'confirmed']
    ).select_related('patient', 'dentist').order_by('appointment_date', 'appointment_time')[:10]
    
    # Recent patients
    recent_patients = Patient.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]
    
    context = {
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_invoices': pending_invoices,
        'upcoming_appointments': upcoming_appointments,
        'recent_patients': recent_patients,
    }
    
    return render(request, 'dental/dashboard.html', context)


@login_required
def patient_list(request):
    """List all patients"""
    query = request.GET.get('q', '')
    
    patients = Patient.objects.filter(is_active=True)
    
    if query:
        patients = patients.filter(
            Q(patient_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    
    patients = patients.order_by('last_name', 'first_name')
    
    context = {
        'patients': patients,
        'query': query,
    }
    
    return render(request, 'dental/patient_list.html', context)


@login_required
def patient_detail(request, patient_id):
    """Patient detail view with chart"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get related data
    appointments = patient.appointments.all().order_by('-appointment_date', '-appointment_time')[:10]
    treatments = patient.treatments.all().order_by('-treatment_date')[:10]
    invoices = patient.invoices.all().order_by('-issue_date')[:5]
    documents = patient.documents.all().order_by('-uploaded_at')[:10]
    
    # Get periodontal exams with statistics
    from .models import PeriodontalExam
    periodontal_exams_qs = patient.periodontal_exams.all().order_by('-exam_date')[:5]
    
    # Add statistics to each exam
    periodontal_exams = []
    for exam in periodontal_exams_qs:
        exam.bleeding_count = exam.measurements.filter(bleeding=True).count()
        exam.calculus_count = exam.measurements.filter(calculus=True).count()
        periodontal_exams.append(exam)
    
    # Get teeth and organize by tooth number
    teeth_queryset = patient.teeth.all()
    teeth_dict = {tooth.tooth_number: tooth for tooth in teeth_queryset}
    
    # Initialize dental chart if not exists
    if not teeth_queryset.exists():
        # Auto-create all 32 teeth
        from .models import Tooth
        tooth_numbers = (
            list(range(18, 10, -1)) + list(range(21, 29)) +  # Upper jaw
            list(range(48, 40, -1)) + list(range(31, 39))    # Lower jaw
        )
        for tooth_num in tooth_numbers:
            Tooth.objects.create(
                patient=patient,
                tooth_number=tooth_num,
                status='healthy'
            )
        # Refresh teeth data
        teeth_queryset = patient.teeth.all()
        teeth_dict = {tooth.tooth_number: tooth for tooth in teeth_queryset}
    
    # Calculate financial summary
    total_treatments = treatments.aggregate(
        total=Sum('cost'),
        paid=Sum('patient_paid')
    )
    
    # Calculate outstanding balance
    total_cost = total_treatments.get('total') or 0
    total_paid = total_treatments.get('paid') or 0
    outstanding = total_cost - total_paid
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'treatments': treatments,
        'invoices': invoices,
        'documents': documents,
        'teeth_dict': teeth_dict,
        'has_dental_chart': teeth_queryset.exists(),
        'total_treatments': total_treatments,
        'outstanding_balance': outstanding,
        'periodontal_exams': periodontal_exams,
    }
    
    return render(request, 'dental/patient_detail.html', context)


@login_required
def patient_create(request):
    """Create new patient"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Patient {patient.patient_id} created successfully!')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientForm()
    
    context = {'form': form}
    return render(request, 'dental/patient_form.html', context)


@login_required
def patient_edit(request, patient_id):
    """Edit patient information"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'dental/patient_form.html', context)


@login_required
def appointment_calendar(request):
    """Appointment calendar view"""
    date_str = request.GET.get('date', timezone.now().date().isoformat())
    selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Get appointments for the selected date
    appointments = Appointment.objects.filter(
        appointment_date=selected_date
    ).select_related('patient', 'dentist').order_by('appointment_time')
    
    # Calculate statistics
    total_count = appointments.count()
    confirmed_count = appointments.filter(status='confirmed').count()
    scheduled_count = appointments.filter(status='scheduled').count()
    completed_count = appointments.filter(status='completed').count()
    
    # Get week range
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    context = {
        'selected_date': selected_date,
        'appointments': appointments,
        'week_dates': week_dates,
        'total_count': total_count,
        'confirmed_count': confirmed_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'dental/appointment_calendar.html', context)


@login_required
def appointment_create(request):
    """Create new appointment"""
    patient_id = request.GET.get('patient_id')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.dentist = request.user
            appointment.save()
            messages.success(request, 'Appointment created successfully!')
            return redirect('appointment_calendar')
    else:
        initial = {}
        if patient_id:
            initial['patient'] = patient_id
        form = AppointmentForm(initial=initial)
    
    context = {'form': form}
    return render(request, 'dental/appointment_form.html', context)


@login_required
def treatment_create(request, patient_id):
    """Create new treatment record"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = TreatmentForm(request.POST, request.FILES)
        if form.is_valid():
            treatment = form.save(commit=False)
            treatment.patient = patient
            treatment.dentist = request.user
            treatment.save()
            messages.success(request, 'Treatment record created successfully!')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = TreatmentForm(initial={'treatment_date': timezone.now().date()})
    
    context = {
        'form': form,
        'patient': patient,
    }
    return render(request, 'dental/treatment_form.html', context)


# AJAX API for tooth updates
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@login_required
@require_http_methods(["POST"])
def tooth_update(request, tooth_id):
    """AJAX endpoint to update tooth status"""
    try:
        from .models import Tooth
        tooth = get_object_or_404(Tooth, id=tooth_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        # Validate status
        valid_statuses = dict(Tooth.TOOTH_STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid tooth status'
            }, status=400)
        
        # Update tooth
        tooth.status = new_status
        if notes:
            tooth.notes = notes
        tooth.save()
        
        return JsonResponse({
            'success': True,
            'tooth_number': tooth.tooth_number,
            'status': tooth.status,
            'status_display': tooth.get_status_display(),
            'notes': tooth.notes,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def periodontal_exam_detail(request, exam_id):
    """View detailed periodontal exam with comparison"""
    from .models import PeriodontalExam, ToothMeasurement
    
    exam = get_object_or_404(PeriodontalExam, id=exam_id)
    patient = exam.patient
    
    # Get all measurements for this exam organized by tooth
    measurements = exam.measurements.all().order_by('tooth_number', 'surface', 'position')
    
    # Organize measurements by tooth number
    tooth_data = {}
    for m in measurements:
        if m.tooth_number not in tooth_data:
            tooth_data[m.tooth_number] = {
                'buccal': {'mesial': None, 'middle': None, 'distal': None},
                'lingual': {'mesial': None, 'middle': None, 'distal': None},
            }
        tooth_data[m.tooth_number][m.surface][m.position] = m
    
    # Get previous exam for comparison
    previous_exam = PeriodontalExam.objects.filter(
        patient=patient,
        exam_date__lt=exam.exam_date
    ).order_by('-exam_date').first()
    
    previous_data = {}
    if previous_exam:
        prev_measurements = previous_exam.measurements.all()
        for m in prev_measurements:
            if m.tooth_number not in previous_data:
                previous_data[m.tooth_number] = {
                    'buccal': {'mesial': None, 'middle': None, 'distal': None},
                    'lingual': {'mesial': None, 'middle': None, 'distal': None},
                }
            previous_data[m.tooth_number][m.surface][m.position] = m
    
    # Tooth number lists
    upper_teeth = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
    lower_teeth = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
    positions = ['mesial', 'middle', 'distal']
    
    context = {
        'exam': exam,
        'patient': patient,
        'tooth_data': tooth_data,
        'previous_exam': previous_exam,
        'previous_data': previous_data,
        'upper_teeth': upper_teeth,
        'lower_teeth': lower_teeth,
        'positions': positions,
    }
    
    return render(request, 'dental/periodontal_exam_detail.html', context)


@login_required
def periodontal_exam_create(request, patient_id):
    """Create new periodontal exam"""
    from .models import PeriodontalExam, ToothMeasurement
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        # Create the exam
        exam = PeriodontalExam.objects.create(
            patient=patient,
            exam_date=request.POST.get('exam_date'),
            dentist=request.user,
            notes=request.POST.get('notes', '')
        )
        
        # Process measurements
        tooth_numbers = (
            list(range(18, 10, -1)) + list(range(21, 29)) +  # Upper jaw
            list(range(48, 40, -1)) + list(range(31, 39))    # Lower jaw
        )
        
        surfaces = ['buccal', 'lingual']
        positions = ['mesial', 'middle', 'distal']
        
        for tooth_num in tooth_numbers:
            for surface in surfaces:
                for position in positions:
                    # Get form field name
                    field_name = f'depth_{tooth_num}_{surface}_{position}'
                    depth = request.POST.get(field_name)
                    
                    if depth and depth.strip():
                        bleeding = request.POST.get(f'bleeding_{tooth_num}_{surface}_{position}') == 'on'
                        calculus = request.POST.get(f'calculus_{tooth_num}_{surface}_{position}') == 'on'
                        
                        ToothMeasurement.objects.create(
                            exam=exam,
                            tooth_number=tooth_num,
                            surface=surface,
                            position=position,
                            pocket_depth=int(depth),
                            bleeding=bleeding,
                            calculus=calculus
                        )
        
        messages.success(request, '歯周検査が正常に作成されました！')
        return redirect('periodontal_exam_detail', exam_id=exam.id)
    
    # Tooth number lists for template
    upper_teeth = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
    lower_teeth = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
    
    context = {
        'patient': patient,
        'upper_teeth': upper_teeth,
        'lower_teeth': lower_teeth,
        'today': timezone.now().date(),
    }
    
    return render(request, 'dental/periodontal_exam_form.html', context)

