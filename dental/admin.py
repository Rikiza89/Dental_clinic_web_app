# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Patient, MedicalHistory, Tooth, Appointment, 
    Treatment, Invoice, Document, PeriodontalExam, ToothMeasurement
)


class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    can_delete = False
    verbose_name_plural = 'Medical History'
    extra = 0


class ToothInline(admin.TabularInline):
    model = Tooth
    extra = 0
    fields = ['tooth_number', 'status', 'notes']


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    fields = ['appointment_date', 'appointment_time', 'reason', 'status']
    readonly_fields = ['created_at']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'patient_id', 'get_full_name', 'date_of_birth', 
        'phone', 'email', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'gender', 'created_at']
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['patient_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'postal_code')
        }),
        ('Insurance Information', {
            'fields': ('insurance_provider', 'insurance_number'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('is_active', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MedicalHistoryInline, AppointmentInline]
    
    def get_full_name(self, obj):
        return f"{obj.last_name} {obj.first_name}"
    get_full_name.short_description = 'Patient Name'
    get_full_name.admin_order_field = 'last_name'
    
    actions = ['activate_patients', 'deactivate_patients']
    
    def activate_patients(self, request, queryset):
        queryset.update(is_active=True)
    activate_patients.short_description = "Activate selected patients"
    
    def deactivate_patients(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_patients.short_description = "Deactivate selected patients"


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'updated_at']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__patient_id']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Allergies and Medications', {
            'fields': ('allergies', 'current_medications')
        }),
        ('Medical Conditions', {
            'fields': (
                'has_heart_disease', 'has_diabetes', 
                'has_high_blood_pressure', 'has_bleeding_disorder', 
                'is_pregnant'
            )
        }),
        ('Dental History', {
            'fields': ('previous_dental_problems', 'last_dental_visit')
        }),
        ('Other', {
            'fields': ('other_conditions', 'updated_at')
        }),
    )


@admin.register(Tooth)
class ToothAdmin(admin.ModelAdmin):
    list_display = ['patient', 'tooth_number', 'status', 'last_updated']
    list_filter = ['status', 'last_updated']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__patient_id']
    readonly_fields = ['last_updated']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'appointment_date', 'appointment_time', 
        'dentist', 'reason', 'get_status_badge', 'created_at'
    ]
    list_filter = ['status', 'appointment_date', 'dentist']
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'patient__patient_id', 'reason'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Patient and Dentist', {
            'fields': ('patient', 'dentist')
        }),
        ('Appointment Details', {
            'fields': (
                'appointment_date', 'appointment_time', 
                'duration', 'reason', 'status'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_badge(self, obj):
        colors = {
            'scheduled': '#FFA500',
            'confirmed': '#4169E1',
            'completed': '#228B22',
            'cancelled': '#DC143C',
            'no_show': '#8B0000',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    actions = ['mark_as_confirmed', 'mark_as_completed']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_as_confirmed.short_description = "Mark as confirmed"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark as completed"


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'treatment_date', 'procedure_name', 
        'dentist', 'cost', 'get_balance', 'created_at'
    ]
    list_filter = ['treatment_date', 'dentist', 'procedure_code']
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'patient__patient_id', 'procedure_name', 'procedure_code'
    ]
    readonly_fields = ['created_at', 'get_balance']
    date_hierarchy = 'treatment_date'
    
    fieldsets = (
        ('Patient and Dentist', {
            'fields': ('patient', 'dentist', 'appointment')
        }),
        ('Treatment Details', {
            'fields': (
                'treatment_date', 'tooth_number', 
                'procedure_code', 'procedure_name', 'description'
            )
        }),
        ('Financial', {
            'fields': ('cost', 'insurance_covered', 'patient_paid', 'get_balance')
        }),
        ('Files and Notes', {
            'fields': ('xray_image', 'notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_balance(self, obj):
        balance = obj.balance_due
        color = '#DC143C' if balance > 0 else '#228B22'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:.2f}</span>',
            color,
            balance
        )
    get_balance.short_description = 'Balance Due'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'patient', 'issue_date', 
        'due_date', 'total', 'get_balance', 'get_status_badge'
    ]
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = [
        'invoice_number', 'patient__first_name', 
        'patient__last_name', 'patient__patient_id'
    ]
    readonly_fields = ['invoice_number', 'get_balance']
    date_hierarchy = 'issue_date'
    filter_horizontal = ['treatments']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'patient', 'issue_date', 'due_date')
        }),
        ('Treatments', {
            'fields': ('treatments',)
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax', 'total', 'amount_paid', 'get_balance', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_balance(self, obj):
        balance = obj.balance_due
        color = '#DC143C' if balance > 0 else '#228B22'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:.2f}</span>',
            color,
            balance
        )
    get_balance.short_description = 'Balance Due'
    
    def get_status_badge(self, obj):
        colors = {
            'draft': '#808080',
            'sent': '#4169E1',
            'paid': '#228B22',
            'overdue': '#DC143C',
            'cancelled': '#8B0000',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    actions = ['mark_as_sent', 'mark_as_paid']
    
    def mark_as_sent(self, request, queryset):
        queryset.update(status='sent')
    mark_as_sent.short_description = "Mark as sent"
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
    mark_as_paid.short_description = "Mark as paid"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'document_type', 'title', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = [
        'patient__first_name', 'patient__last_name', 
        'patient__patient_id', 'title'
    ]
    readonly_fields = ['uploaded_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('patient', 'document_type', 'title')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at', 'notes')
        }),
    )


class ToothMeasurementInline(admin.TabularInline):
    model = ToothMeasurement
    extra = 0
    fields = ['tooth_number', 'surface', 'position', 'pocket_depth', 'bleeding', 'calculus', 'mobility']


@admin.register(PeriodontalExam)
class PeriodontalExamAdmin(admin.ModelAdmin):
    list_display = ['patient', 'exam_date', 'dentist', 'created_at']
    list_filter = ['exam_date', 'dentist']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__patient_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'exam_date'
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('patient', 'exam_date', 'dentist')
        }),
        ('Notes', {
            'fields': ('notes', 'created_at')
        }),
    )
    
    inlines = [ToothMeasurementInline]


@admin.register(ToothMeasurement)
class ToothMeasurementAdmin(admin.ModelAdmin):
    list_display = ['exam', 'tooth_number', 'surface', 'position', 'pocket_depth', 'bleeding', 'calculus']
    list_filter = ['surface', 'bleeding', 'calculus', 'exam__exam_date']
    search_fields = ['exam__patient__first_name', 'exam__patient__last_name']