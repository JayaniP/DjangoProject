from django import forms
from rentsafe.models import PropertyDetail


class ResetPasswordForm(forms.Form):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "The passwords do not match.")

class PropertyDetailForm(forms.ModelForm):
    class Meta:
        model = PropertyDetail
        fields = ['name', 'description', 'details','daily_price', 'deposit', 
                  'image1','image2','image3','image4','property_status'] 
       # start_datetime = forms.DateField(widget=forms.DateInput(attrs={'id': 'sdate'}))
       # end_datetime = forms.DateField(widget=forms.DateInput(attrs={'id': 'edate'}))
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
