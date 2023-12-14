from django import forms
from .models import AddressBook

class AddressForm(forms.ModelForm):
    class Meta:
        model = AddressBook
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'country', 'state', 'city', 'pincode']
