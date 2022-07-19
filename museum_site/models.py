from distutils.errors import LinkError
from django.db import models


AGE_CHOICES = [
    ('18-20', '18-20'), ('21-29', '21-29'), ('30-39', '30-39'), ('40-49', '40-49'),
    ('50-59', '50-59'), ('60+', '60+') 
]

GENDER_CHOICES = [
    ('male', 'Male'), ('female', 'Female'), ('nonbinary', 'Non-binary'), ('other', 'Other'), 
    ('none', 'Prefer not to say')
]

EDU_CHOICES = [
    ('none-high-school', 'Less than high school'), ('high-school', 'High School'), 
    ('college', 'College (no degree)'), ('bachelors', 'Bachelor\'s'), ('masters', 'Master\'s'),
    ('phd', 'Doctorate')
]

WORK_CHOICES = [
    ('employed', 'Employed (full/part time or self)'), ('student', 'Student'), 
    ('retired', 'Retired'), ('unemployed', 'Unemployed')
]

# 'OTHER' IS OPEN ENDED
# ETHNIC_GROUP = [
#     ('white', 'White'), ('mixed', 'Mixed/Multiple Ethnic Groups'), ('asian', 'Asian'),
#     ('black', 'Black/African/Carribean'), ('no answer', 'Prefer not to say')
# ]

DISABILITY = [
    ('disable', 'Identify as disabled'), ('not disabled', 'Do not identify as disable'),
    ('no answer', 'Prefer not to answer')
]

# --- Domain Knowledge Choices ---
ART_KNOWLEDGE = [
    ('novice', 'Novice'), ('some', 'I have got some knowledge'), ('knowledgeable', 'Knowledgeable'),
    ('expert', 'Expert')
]

MUSEUM_VISITS = [
    ('most days', 'Most Days'), ('once a week', 'At least once a week'), 
    ('once a month', 'At least once a month'), 
    ('every two to three months', 'At least once every two to three months'),
    ('once a year', 'At least once a year'), ('first time', 'This is my first time')
]

VIEW_COLLECTIONS = [
    ('most days', 'Most Days'), ('once a week', 'At least once a week'), 
    ('once a month', 'At least once a month'), 
    ('every two to three months', 'At least once every two to three months'),
    ('once a year', 'At least once a year'), ('first time', 'This is my first time')
]

PHYSICAL_VISITS = [
    ('once every 6 months', 'At least once every 6 months'),
    ('once a year', 'At least once a year'),
    ('two or three years', 'Every two or three years'),
    ('four or five years', 'Every four or five years'),
    ('six years or longer', 'I have not been to a museum/art gallery in 6 years or longer'),
    ('never', 'I have never visited a museum/art gallery in person')
]

DISTRACTION_CHOICES = [
    ('duck', 'Duck'), ('mouse', 'Mouse'), ('elephant', 'Elephant'), ('bumblebee', 'Bumblebee')
]

LIKERT_SCALE = [
    ('strongly disagree', 'Strongly Disagree'),
    ('disagree', 'Disagree'),
    ('neutral', 'Neither disagree or agree'),
    ('agree', 'Agree'),
    ('strongly agree', 'Strongly Agree')
]


class User(models.Model):
    """
        A model to represent a user on the website and in the study. 
        We'll create the user object when the user provides consent for their
        data to be collected.

        Note: we'll only require the email address if they want to be contacted.
    """
    # unique identifer for the user; we'll use this across the site
    user_id = models.CharField(max_length = 64, primary_key = True)

    # whether or not the user has provided consent for data collection
    consent = models.BooleanField()

    # the email address for the user and if they want to be contacted to know the outcome
    email = models.EmailField() # default length is 254 chars
    contact_outcome = models.BooleanField()

    # when was the user object created
    user_created = models.DateTimeField()

    def __str__(self):
        """
            Overridden function to format the user when printing
        """
        return f"id: {self.user_id}, contact_outcome: {self.contact_outcome}, " + \
            f"created: {self.user_created}"

class UserDemographic(models.Model):
    """
        A model to represent demographic information about the users.
        We'll use the user_id field (from User) as a foreign key.
    """
    # the user that the demographic information is associated with, when the user is deleted,
    # so is their demographic information
    user = models.OneToOneField(User, on_delete = models.CASCADE, primary_key = True)
    age = models.CharField(max_length = 5, choices = AGE_CHOICES)
    gender = models.CharField(max_length = 9, choices = GENDER_CHOICES)
    education = models.CharField(max_length = 16, choices = EDU_CHOICES)
    work = models.CharField(max_length = 10, choices = WORK_CHOICES)
    disability = models.CharField(max_length = 20, choices = DISABILITY)

    submission_timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user} demographics: [{self.age}, {self.gender}, {self.education}, " +  \
                f"{self.work}]"


class Artwork(models.Model):
    art_id = models.CharField(max_length=64, primary_key=True)
    collection = models.CharField(max_length=256, null=True)
    classification = models.CharField(max_length=256, null=True)
    title = models.CharField(max_length=1024, null=True)
    medium = models.CharField(max_length=512, null=True)
    artist = models.CharField(max_length=256, null=True)
    birth_date = models.CharField(max_length=64, null=True)
    death_date = models.CharField(max_length=64, null=True)
    earliest_date = models.IntegerField(null=True)
    latest_date = models.IntegerField(null=True)
    image_credit = models.CharField(max_length=1024, null=True)
    linked_terms = models.CharField(max_length=1024, null=True)
    linked_topics = models.CharField(max_length=1024, null=True)
    linked_art_terms = models.CharField(max_length=512, null=True)
    img_file = models.CharField(max_length=512, null=True)
    img_location = models.CharField(max_length=1024, null=True)

    execution_date = models.CharField(max_length = 512, null = True)

    def __str__(self):
        return f"{self.art_id}"


class ArtworkVisited(models.Model):
    """
    """
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    art = models.ForeignKey(Artwork, on_delete = models.CASCADE)
    timestamp = models.DateTimeField()
    rating = models.IntegerField(null = True)

    def __str__(self):
        return f"User: {self.user.user_id}; Art: {self.art.art_id}; Timestamp: {self.timestamp}"


class DomainKnowledge(models.Model):
    """
        A model to represent the domain knowledge questionnaire.
    """
    user = models.OneToOneField(User, on_delete = models.CASCADE, primary_key = True)
    art_knowledge = models.CharField(max_length = 20, choices = ART_KNOWLEDGE)
    museum_visits = models.CharField(max_length = 30, choices = MUSEUM_VISITS)
    view_collections = models.CharField(max_length = 30, choices = VIEW_COLLECTIONS)
    physical_visits = models.CharField(max_length = 30, choices = PHYSICAL_VISITS)
    submission_timestamp = models.DateTimeField()

    def __str__(self) -> str:
        return f"[{self.art_knowledge}, {self.museum_visits}, {self.view_collections}" + \
            f"{self.physical_visits}]"

class UserCondition(models.Model):
    """
    """
    user = models.OneToOneField(User, on_delete = models.CASCADE, primary_key = True)

    # the condition, either meta, image, or concatenated
    condition = models.CharField(max_length = 20)

    # the first condition they see (either random or model)
    order = models.CharField(max_length = 6) 

    # what context the user is currently in (either: initial, random, or model)
    current_context = models.CharField(max_length = 10)

    # what 'step' within a part a user is currently in, i.e., are they in position 3
    # out of 5? Set the default to 1
    current_step = models.IntegerField(default = 1)

    # timestamp
    timestamp = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.user}: {self.condition}, {self.order}"


class ArtworkSelected(models.Model):
    """
    """
    # the user that is doing the selecting
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    # the specific artwork that the user has selected
    selected_artwork = models.ForeignKey(Artwork, on_delete = models.CASCADE)

    # what the context of the selection is (either initial; random; or model)
    selection_context = models.CharField(max_length = 10)

    # log what step the artwork was selected on
    step_selected = models.IntegerField(default = -1)

    # the timestamp for when the selection occurred (probably the same across the selected five)
    timestamp = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.user}: {self.selected_artwork}, {self.selection_context}"

class RecommendedArtwork(models.Model):
    """
    """
    # the user that the artwork has been recommended too
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    # the recommended artwork
    recommended_artwork = models.ForeignKey(Artwork, on_delete = models.CASCADE)

    # the context, i.e., random or model-based (+ model type)
    recommendation_context = models.CharField(max_length = 30)

    # the step at which they were recommended
    recommended_step = models.IntegerField(default = 1)

class DistractionTask(models.Model):
    """
    """
    # the user that is doing the distraction task
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    # the distraction choice for the question
    distraction = models.CharField(max_length = 30, choices = DISTRACTION_CHOICES)

    # the submission timestamp for the survey
    submission_timestamp = models.DateTimeField()

class PostStudy(models.Model):
    """
    """
    # the user taking part
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    # submission timestamp
    submission_timestamp = models.DateTimeField()

    # the part (either part one or two)
    part = models.CharField(max_length = 10)

    # PERCEIVED QUALITY
    perceived_quality_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_quality_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_quality_three = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_quality_four = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_quality_five = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_quality_six = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

    # PERCEIVED SYSTEM EFFECTIVENESS AND FUN
    perceived_effectiveness_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_three = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_four = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_five = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_six = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_seven = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_eight = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_nine = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    perceived_effectiveness_ten = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

    # CHOICE SATISFACTION
    choice_satisfaction_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_three = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_four = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_five = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_six = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_seven = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_eight = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    choice_satisfaction_nine = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

    # TEST AWARENESS
    test_awareness_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    test_awareness_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    
class PostStudyGeneral(models.Model):
    """
    """
    # the user taking part 
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    # submission timestamp
    submission_timestamp = models.DateTimeField()

    # intention to provide feedback
    intention = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

    # GENERAL TRUST IN TECH
    trust_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    trust_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    trust_three = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    trust_four = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    trust_five = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

    # MUSEUM ONLINE COLLECTION RELEVANT QUESTION
    relevant_one = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    relevant_two = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    relevant_three = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')
    relevant_four = models.CharField(max_length = 30, choices = LIKERT_SCALE, default = 'neutral')

