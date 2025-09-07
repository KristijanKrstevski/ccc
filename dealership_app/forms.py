from django import forms
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
            "price": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter price"}),
            "brand": forms.Select(attrs={"class": "form-select rounded"}),
            "model_name": forms.Select(attrs={
                "class": "form-select rounded",
                "disabled": "disabled"  # initially disabled
            }),
            "year": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Year"}),
            "color": forms.Select(attrs={"class": "form-select rounded"}),
            "transmission": forms.Select(attrs={"class": "form-select rounded"}),
            "fuel_type": forms.Select(attrs={"class": "form-select rounded"}),
            "body_type": forms.Select(attrs={"class": "form-select rounded"}),
            "registration_type": forms.Select(attrs={"class": "form-select rounded"}),
            "engine_capacity": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Engine capacity (cc)"}),
            "kilowatts": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "kW"}),
            "seats": forms.Select(attrs={"class": "form-select rounded"}),
            "mileage": forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter kilometers", "maxlength": "9"}),
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
            'mileage': forms.NumberInput(attrs={"class": "form-control rounded", "placeholder": "Enter kilometers", "maxlength": "9"}),
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