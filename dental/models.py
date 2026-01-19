# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from decimal import Decimal

class Patient(models.Model):
    """患者管理 - Patient Management"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Basic Information
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Contact Information
    email = models.EmailField(blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = models.CharField(validators=[phone_regex], max_length=17)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Insurance Information
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['patient_id']),
        ]
    
    def __str__(self):
        return f"{self.patient_id} - {self.last_name} {self.first_name}"
    
    def save(self, *args, **kwargs):
        if not self.patient_id:
            # Generate patient ID: P + year + sequential number
            from django.utils import timezone
            year = timezone.now().year
            last_patient = Patient.objects.filter(
                patient_id__startswith=f'P{year}'
            ).order_by('patient_id').last()
            
            if last_patient:
                last_number = int(last_patient.patient_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.patient_id = f'P{year}{new_number:04d}'
        
        super().save(*args, **kwargs)


class MedicalHistory(models.Model):
    """Medical and Dental History"""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='medical_history')
    
    # Allergies
    allergies = models.TextField(blank=True, help_text="List all known allergies")
    current_medications = models.TextField(blank=True)
    
    # Medical Conditions
    has_heart_disease = models.BooleanField(default=False)
    has_diabetes = models.BooleanField(default=False)
    has_high_blood_pressure = models.BooleanField(default=False)
    has_bleeding_disorder = models.BooleanField(default=False)
    is_pregnant = models.BooleanField(default=False)
    
    # Dental History
    previous_dental_problems = models.TextField(blank=True)
    last_dental_visit = models.DateField(blank=True, null=True)
    
    other_conditions = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Medical History - {self.patient}"


class Tooth(models.Model):
    """Individual Tooth Record"""
    TOOTH_STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('cavity', 'Cavity'),
        ('filled', 'Filled'),
        ('crown', 'Crown'),
        ('root_canal', 'Root Canal'),
        ('missing', 'Missing'),
        ('implant', 'Implant'),
        ('bridge', 'Bridge'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='teeth')
    tooth_number = models.IntegerField()  # FDI notation (11-48)
    status = models.CharField(max_length=20, choices=TOOTH_STATUS_CHOICES, default='healthy')
    notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'tooth_number']
        ordering = ['tooth_number']
    
    def __str__(self):
        return f"Tooth {self.tooth_number} - {self.patient}"


class PeriodontalExam(models.Model):
    """歯周検査 - Periodontal Examination (歯茎深さ・出血位置・歯石)"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='periodontal_exams')
    exam_date = models.DateField()
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-exam_date']
        verbose_name = 'Periodontal Examination'
        verbose_name_plural = 'Periodontal Examinations'
    
    def __str__(self):
        return f"Periodontal Exam - {self.patient} ({self.exam_date})"


class ToothMeasurement(models.Model):
    """Individual tooth measurements for periodontal exam"""
    POSITION_CHOICES = [
        ('mesial', 'Mesial (近心)'),
        ('middle', 'Middle (中央)'),
        ('distal', 'Distal (遠心)'),
    ]
    
    SURFACE_CHOICES = [
        ('buccal', 'Buccal/Labial (頬側/唇側)'),
        ('lingual', 'Lingual/Palatal (舌側/口蓋側)'),
    ]
    
    exam = models.ForeignKey(PeriodontalExam, on_delete=models.CASCADE, related_name='measurements')
    tooth_number = models.IntegerField()  # FDI notation
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    surface = models.CharField(max_length=10, choices=SURFACE_CHOICES)
    
    # 歯茎深さ (Pocket Depth in mm)
    pocket_depth = models.IntegerField(help_text="Gum pocket depth in mm")
    
    # 出血 (Bleeding on Probing)
    bleeding = models.BooleanField(default=False, help_text="Bleeding detected")
    
    # 歯石 (Calculus/Tartar)
    calculus = models.BooleanField(default=False, help_text="Calculus/tartar present")
    
    # 歯の動揺 (Tooth Mobility) - optional
    mobility = models.IntegerField(
        null=True, 
        blank=True, 
        choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')],
        help_text="Tooth mobility degree (0-3)"
    )
    
    class Meta:
        unique_together = ['exam', 'tooth_number', 'position', 'surface']
        ordering = ['tooth_number', 'surface', 'position']
    
    def __str__(self):
        return f"Tooth {self.tooth_number} - {self.get_position_display()} {self.get_surface_display()}"


class Appointment(models.Model):
    """Appointment Scheduling"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='appointments')
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['patient', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.patient} - {self.appointment_date} {self.appointment_time}"


class Treatment(models.Model):
    """Treatment Records"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='treatments')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    dentist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    treatment_date = models.DateField()
    tooth_number = models.IntegerField(blank=True, null=True)
    
    # Treatment Details
    procedure_code = models.CharField(max_length=20)
    procedure_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Costs
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    insurance_covered = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    patient_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Files
    xray_image = models.ImageField(upload_to='xrays/', blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-treatment_date']
    
    def __str__(self):
        return f"{self.patient} - {self.procedure_name} ({self.treatment_date})"
    
    @property
    def balance_due(self):
        return self.cost - self.insurance_covered - self.patient_paid


class Invoice(models.Model):
    """Billing and Invoicing"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    treatments = models.ManyToManyField(Treatment, related_name='invoices')
    
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV{year}'
            ).order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f'INV{year}{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def balance_due(self):
        return self.total - self.amount_paid


class Document(models.Model):
    """Patient Documents"""
    DOCUMENT_TYPES = [
        ('consent', 'Consent Form'),
        ('xray', 'X-Ray'),
        ('photo', 'Photo'),
        ('lab_report', 'Lab Report'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='patient_documents/')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient}"