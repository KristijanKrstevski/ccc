from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Car, CarImage,CarModel

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class CarModelForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = "__all__"
        exclude = ['position', 'description']
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control rounded", "placeholder": "Enter car title..."}),
            "price": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter price", "min": "0", "oninput": "validateNumericField(this)"}),
            "brand": forms.Select(attrs={"class": "form-select rounded"}),
            "model_name": forms.Select(attrs={
                "class": "form-select rounded",
                "disabled": "disabled"  # initially disabled
            }),
            "year": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Year", "min": "0", "oninput": "validateNumericField(this)"}),
            "color": forms.Select(attrs={"class": "form-select rounded"}),
            "transmission": forms.Select(attrs={"class": "form-select rounded"}),
            "fuel_type": forms.Select(attrs={"class": "form-select rounded"}),
            "body_type": forms.Select(attrs={"class": "form-select rounded"}),
            "registration_type": forms.Select(attrs={"class": "form-select rounded"}),
            "engine_capacity": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Engine capacity (cc)", "min": "0", "oninput": "validateNumericField(this)"}),
            "kilowatts": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "kW"}),
            "seats": forms.Select(attrs={"class": "form-select rounded"}),
            "mileage": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter kilometers", "maxlength": "9", "min": "0", "oninput": "validateNumericField(this)"}),
            "consumption": forms.TextInput(attrs={"class": "form-control rounded", "placeholder": "e.g. 6.5", "maxlength": "10"}),
            "banner_type": forms.RadioSelect(attrs={"class": "banner-radio"}),
            "description": forms.Textarea(attrs={"class": "form-control rounded", "rows": 3, "placeholder": "Description..."}),
            "main_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set mileage maxlength to 9 digits
        if 'mileage' in self.fields:
            self.fields['mileage'].widget.attrs['maxlength'] = '9'

        # always start empty
        self.fields['model_name'].queryset = CarModel.objects.none()

        # if brand in POST (user just picked), load that brand's models
        if 'brand' in self.data:
            try:
                bid = int(self.data.get('brand'))
                qs = CarModel.objects.filter(brand_id=bid).order_by('name')
            except (ValueError, TypeError):
                qs = CarModel.objects.none()
            else:
                # enable model field
                self.fields['model_name'].widget.attrs.pop('disabled', None)
            self.fields['model_name'].queryset = qs

        # if editing existing Car, preload its models & enable
        elif self.instance.pk and self.instance.brand_id:
            bid = self.instance.brand_id
            qs = CarModel.objects.filter(brand_id=bid).order_by('name')
            self.fields['model_name'].queryset = qs
            self.fields['model_name'].widget.attrs.pop('disabled', None)

    def clean_consumption(self):
        consumption = self.cleaned_data.get('consumption')
        if consumption is not None and consumption != '':
            consumption = str(consumption).strip()
            
            # Check if it matches decimal pattern (e.g. 6.5, 4.6, 10.2)
            if not re.match(r'^\d+(\.\d+)?$', consumption):
                raise ValidationError('Invalid input. Please enter a valid consumption value (e.g. 6.5)')
            
            # Convert to float to validate range
            try:
                consumption_float = float(consumption)
                if consumption_float < 0:
                    raise ValidationError('Invalid input. Consumption cannot be negative')
                if consumption_float > 99.9:
                    raise ValidationError('Invalid input. Consumption value too high (max 99.9)')
            except ValueError:
                raise ValidationError('Invalid input. Please enter a valid number')
        
        return consumption

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year is not None:
            if year < 0:
                raise ValidationError('Invalid input. Year cannot be negative')
            if year > 2030:
                raise ValidationError('Invalid input. Please enter a valid year')
        return year

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            if price < 0:
                raise ValidationError('Invalid input. Price cannot be negative')
        return price

    def clean_engine_capacity(self):
        engine_capacity = self.cleaned_data.get('engine_capacity')
        if engine_capacity is not None:
            if engine_capacity < 0:
                raise ValidationError('Invalid input. Engine capacity cannot be negative')
        return engine_capacity

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage is not None:
            if mileage < 0:
                raise ValidationError('Invalid input. Mileage cannot be negative')
        return mileage
class CarImageForm(forms.Form):
    images = forms.ImageField(
        widget=MultipleFileInput(attrs={"class": "form-control rounded", "multiple": True}),
        required=False,
        label="Дополнителни слики"
    )

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = "__all__"
        exclude = ['description']  # Remove description field
        widgets = {
            'model_name': forms.Select(attrs={'disabled': 'disabled'}),  # initially empty/disabled
            'mileage': forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter kilometers", "maxlength": "9", "min": "0", "oninput": "validateNumericField(this)"}),
            'consumption': forms.TextInput(attrs={"class": "form-control rounded", "placeholder": "e.g. 6.5", "maxlength": "10"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['model_name'].queryset = CarModel.objects.none()

        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model_name'].queryset = CarModel.objects.filter(brand_id=brand_id).order_by('name')
                self.fields['model_name'].widget.attrs.pop('disabled', None)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.brand:
            self.fields['model_name'].queryset = CarModel.objects.filter(brand=self.instance.brand).order_by('name')
            self.fields['model_name'].widget.attrs.pop('disabled', None)

    def clean_consumption(self):
        consumption = self.cleaned_data.get('consumption')
        if consumption is not None and consumption != '':
            consumption = str(consumption).strip()
            
            # Check if it matches decimal pattern (e.g. 6.5, 4.6, 10.2)
            if not re.match(r'^\d+(\.\d+)?$', consumption):
                raise ValidationError('Invalid input. Please enter a valid consumption value (e.g. 6.5)')
            
            # Convert to float to validate range
            try:
                consumption_float = float(consumption)
                if consumption_float < 0:
                    raise ValidationError('Invalid input. Consumption cannot be negative')
                if consumption_float > 99.9:
                    raise ValidationError('Invalid input. Consumption value too high (max 99.9)')
            except ValueError:
                raise ValidationError('Invalid input. Please enter a valid number')
        
        return consumption

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage is not None:
            if mileage < 0:
                raise ValidationError('Invalid input. Mileage cannot be negative')
        return mileage