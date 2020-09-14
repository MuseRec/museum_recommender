from django.forms import ModelForm, HiddenInput
from django.core.validators import EMPTY_VALUES

from .models import User, UserDemographic

class UserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['consent'].required = True
        self.fields['contact_outcome'].required = False 
        self.fields['email'].required = False

    def clean(self):
        is_contact = self.cleaned_data.get('contact_outcome', False)
        if is_contact:
            provided_email = self.cleaned_data.get('email', None)
            if provided_email in EMPTY_VALUES:
                self._errors['email'] = self.error_class([
                    'Email is required if you want to be contacted'
                ])
        return self.cleaned_data
       
    class Meta:
        model = User
        fields = ('consent', 'contact_outcome', 'email')
        labels = {
            'consent': "I have read the information sheet above and provide consent",
            'contact_outcome': "I would like to be contacted about the outcome of the study",
            'email': "Email (only needed if you want to be contacted to know the outcome)"
        }

class UserDemographicForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserDemographicForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True 
    
    class Meta:
        model = UserDemographic
        fields = ('age', 'gender', 'education', 'work')
        labels = {
            'age': 'What is your age category?',
            'gender': 'What gender do you identify as?',
            'education': 'What is the highest level of education you have received?',
            'work': 'Which of the following categories best describes your employment status?'
        }
