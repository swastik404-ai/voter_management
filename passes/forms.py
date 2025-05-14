from django import forms
from .models import Pass
from django.utils import timezone


class PassRequestForm(forms.ModelForm):
    class Meta:
        model = Pass
        fields = [
            'name',
            'email',
            'phone',
            'temple',
            'num_persons',
            'visit_date',
            'id_proof_type',
            'id_proof_number'
        ]
        widgets = {
            'visit_date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.now().date().isoformat(),
            }),
            'phone': forms.TextInput(attrs={
                'pattern': '[0-9]{10}',
                'title': 'Enter 10 digit mobile number'
            }),
            'num_persons': forms.NumberInput(attrs={
                'min': '1',
                'max': '6',
                'title': 'Number of persons must be between 1 and 6'
            }),
            'id_proof_number': forms.TextInput(attrs={
                'pattern': '[0-9]{12}',
                'title': 'Enter 12 digit Aadhar number'
            }),
        }
        help_texts = {
            'num_persons': 'Maximum 6 persons allowed per pass',
            'phone': 'Enter 10 digit mobile number',
            'visit_date': 'Select a future date',
            'id_proof_number': 'Enter 12 digit Aadhar number'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set ID proof type to Aadhar Card only
        self.fields['id_proof_type'].choices = [('AADHAR', 'Aadhar Card')]
        self.fields['id_proof_type'].initial = 'AADHAR'

    def clean_id_proof_number(self):
        id_proof_number = self.cleaned_data.get('id_proof_number')
        if not id_proof_number.isdigit() or len(id_proof_number) != 12:
            raise forms.ValidationError('Please enter a valid 12-digit Aadhar number')
        return id_proof_number

    def clean_visit_date(self):
        visit_date = self.cleaned_data.get('visit_date')
        if visit_date and visit_date < timezone.now().date():
            raise forms.ValidationError("Visit date cannot be in the past!")
        return visit_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number!")
        return phone

    def clean_num_persons(self):
        num_persons = self.cleaned_data.get('num_persons')
        if num_persons is not None:
            if num_persons < 1:
                raise forms.ValidationError("Number of persons must be at least 1!")
            if num_persons > 6:
                raise forms.ValidationError("Maximum 6 persons allowed per pass!")
        return num_persons