from django import forms
from .models import User, UserProfile

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'GSM', 'password']

        def clean(self):
            cleaned_data = super(UserForm, self).clean()
            password = cleaned_data.get('password')
            confirm_password = cleaned_data.get('confirm_password')

            if password != confirm_password:
                raise forms.ValidationError(
                     "Wachtwoord komt niet overeen!"
                )

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(widget=forms.FileInput(attrs={"class": 'btn btn-info'}))
    cover_photo = forms.ImageField(widget=forms.FileInput(attrs={"class": 'btn btn-info'}))

    #latitude = forms.CharField(widget=forms.TextInput(atts={"readonly": 'readonly'}))
    #longitude = forms.CharField(widget=forms.TextInput(atts={"readonly": 'readonly'}))
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'cover_photo', 'address', 'huis_number', 'bus_number', 'city', 'country', 'pin_code', 'latitude', 'longitude']

    def __int__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'latitude' or field == 'longitude':
                self.fields[field].widget.attrs['readonly'] = 'readonly'

class UserInfoform(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'GSM']