from django import forms
from .models import Account, UserProfile

# Clases compartidas para inputs de formulario
# Light mode: fondo blanco, texto negro, borde gris
# Dark mode: fondo oscuro, texto blanco, borde gris-700
INPUT_CLASS = (
    'w-full pl-12 pr-4 py-4 bg-white dark:bg-gray-800 '
    'border border-gray-300 dark:border-gray-600 '
    'rounded-2xl text-gray-900 dark:text-white '
    'placeholder-gray-400 dark:placeholder-gray-500 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-indigo-500 '
    'focus:border-indigo-500 transition-all duration-300'
)

FILE_INPUT_CLASS = (
    'w-full px-4 py-3 bg-white dark:bg-gray-800 '
    'border border-gray-300 dark:border-gray-600 '
    'rounded-2xl text-gray-900 dark:text-white text-sm '
    'focus:outline-none focus:ring-2 focus:ring-indigo-500 '
    'focus:border-indigo-500 transition-all duration-300 '
    'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 '
    'file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 '
    'dark:file:bg-indigo-900 dark:file:text-indigo-300 '
    'hover:file:bg-indigo-100 dark:hover:file:bg-indigo-800'
)


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Ingrese Password',
        'class': INPUT_CLASS,
    }))

    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirmar Password',
        'class': INPUT_CLASS,
    }))

    class Meta:
        model = Account
        fields = ['first_name', 'last_name',
                  'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Ingrese nombre',
            'class': INPUT_CLASS,
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Ingrese apellidos',
            'class': INPUT_CLASS,
        })
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'Ingrese telefono',
            'class': INPUT_CLASS,
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Ingrese email',
            'class': INPUT_CLASS,
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
                'class': INPUT_CLASS,
            })


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={
        'invalid': 'Solo archivos de imagen'
    }, widget=forms.FileInput(attrs={
        'class': FILE_INPUT_CLASS,
    }))

    class Meta:
        model = UserProfile
        fields = ('address_line_1', 'address_line_2', 'city',
                  'state', 'country', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'profile_picture':
                self.fields[field].widget.attrs.update({
                    'class': INPUT_CLASS,
                })
