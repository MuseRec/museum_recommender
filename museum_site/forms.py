from distutils.archive_util import make_archive
from django.forms import ModelForm, HiddenInput
from django.core.validators import EMPTY_VALUES
from django import forms 
from django.core.exceptions import ValidationError

from .models import PostStudy, PostStudyGeneral, User, UserDemographic, DomainKnowledge, DistractionTask
from .models import LIKERT_SCALE

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div
from crispy_forms.bootstrap import InlineRadios

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
        fields = ('age', 'gender', 'education', 'work', 'disability')
        labels = {
            'age': 'What is your age category?',
            'gender': 'What gender do you identify as?',
            'education': 'What is the highest level of education you have received?',
            'work': 'Which of the following categories best describes your employment status?',
            'disability': 'Have you got a disability?'
        }


class DomainKnowledgeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DomainKnowledgeForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True
        
    class Meta:
        model = DomainKnowledge
        fields = ('art_knowledge', 'museum_visits', 'view_collections', 'physical_visits')
        labels = {
            'art_knowledge': 'How would you rate your knowledge of art?',
            'museum_visits': 'How often do you visit museum/art gallery websites?',
            'view_collections': 'How often do you specifically look at collections online?',
            'physical_visits': 'How often do you physically visit a museum/art gallery'
        }

class DistractionTaskForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DistractionTaskForm, self).__init__(*args, **kwargs)
        self.fields['distraction'].required = True 
    
    class Meta: 
        model = DistractionTask
        fields = ('distraction',)
        labels = {'distraction': 'Which of the following animals is the lightest?'}

class HorizontalRadioSelect(forms.RadioSelect):
    template_name = 'horizontal_select.html'

class PostStudyForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(PostStudyForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

    class Meta:
        model = PostStudy
        exclude = ('user', 'submission_timestamp', 'part')
        labels = {
            # PERCEIVED QUALITY
            'perceived_quality_one': 'I liked the artworks shown by the system:',
            'perceived_quality_two': 'The artworks fitted my preference:',
            'perceived_quality_three': 'The artworks were well-chosen:',
            'perceived_quality_four': 'The artworks were relevant:',
            'perceived_quality_five': 'The system showed me too many bad artworks:',
            'perceived_quality_six': 'I did not like any of the artworks shown:',
            # SYSTEM EFFECTIVENESS AND FUN
            'perceived_effectiveness_one': 'I have fun when I am using the system:',
            'perceived_effectiveness_two': 'I would recommend the system to others:',
            'perceived_effectiveness_three': 'Using the system is a pleasant experience:',
            'perceived_effectiveness_four': 'I can find interesting artworks with the system:',
            'perceived_effectiveness_five': 'The system showed me artworks I would usually not find:',
            'perceived_effectiveness_six': 'The system is useless:',
            'perceived_effectiveness_seven': 'The system makes me more aware of my choice option:',
            'perceived_effectiveness_eight': 'I make more informed choices with the system:',
            'perceived_effectiveness_nine': 'I can find better items without the help of the system:',
            'perceived_effectiveness_ten': 'The system showed useful items:',
            # CHOICE SATISFACTION
            'choice_satisfaction_one': 'I like the artworks I have seen:',
            'choice_satisfaction_two': 'I was excited about the artworks shown:',
            'choice_satisfaction_three': 'I enjoyed seeing the artworks shown to me:',
            'choice_satisfaction_four': 'The artworks shown to me were diverse:',
            'choice_satisfaction_five': 'The artworks shown to me were novel:',
            'choice_satisfaction_six': 'The system offered serendipitous items:',
            'choice_satisfaction_seven': 'The artworks I have seen were a waste of time:',
            'choice_satisfaction_eight': 'The shown artworks fitted my preference:',
            'choice_satisfaction_nine': 'I would recommend some of the shown artworks to family and friends:',
            # TEST AWARENESS
            'test_awareness_one': 'I am aware that the system showed me recommendations:',
            'test_awareness_two': 'I am aware that items in this part were specifically chosen to suit my choice of artworks:'
        }
        widgets = {
            question: forms.RadioSelect(
                attrs = {
                    'class': 'form-check-inline',
                    'style': 'margin-right: 0; margin-left: 15px;'
                }
            )
            for question, _ in labels.items()
        }


class PostStudyGeneralForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PostStudyGeneralForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True 

    class Meta:
        model = PostStudyGeneral
        exclude = ('user', 'submission_timestamp')
        labels = {
            'intention': 'I did not mind having to choose artworks:',
            'trust_one': 'Technology never works:',
            'trust_two': 'I trust the system I have just used:',
            'trust_three': 'Technology should always be explainable:',
            'trust_four': 'I am not fussed about how things work in the background as long as the technology works:',
            'trust_five': 'I am generally questioning what happens to my personal data:',
            'relevant_one': 'I prefer a classic keyword search compared to this system:',
            'relevant_two': 'The system is not suitable to display artworks:',
            'relevant_three': 'Museum online collections are generally boring:',
            'relevant_four': 'I do not need museum online collections:'
        }
        widgets = {
            question: forms.RadioSelect(
                attrs = {
                    'class': 'form-check-inline',
                    'style': 'margin-right: 0; margin-left: 15px;'
                }
            )
            for question, _ in labels.items()
        }

class SelectedArtworkForm(forms.Form):
    selection_button = forms.CharField()

class StudyTransitionForm(forms.Form):
    move_on_button = forms.CharField()