from django import forms
from .models import Account, UserProfile


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Ingrese Password',
        'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm',
    }))

    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirmar Password',
        'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm',
    }))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name',
                  'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Ingrese nombre',
            'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Ingrese apellidos',
            'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
        })
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'Ingrese telefono',
            'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Ingrese email',
            'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
        })

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("El password no coincide!")


class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
            })


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={
        'invalid': 'Solo archivos de imagen'
    }, widget=forms.FileInput(attrs={
        'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
    }))

    class Meta:
        model = UserProfile
        fields = ('address_line_1', 'address_line_2', 'city',
                  'state', 'country', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-5 py-4 bg-gray-900/50 border border-gray-700/50 rounded-2xl text-gray-100 placeholder-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all duration-300 backdrop-blur-sm'
            })
