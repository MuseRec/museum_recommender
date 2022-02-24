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
    ('novice', 'Novice'), ('some', 'I have got some knowledge'), ('knowledgeable', 'knowledgeable'),
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
        return f"{self.user}: [{self.art_knowledge}, {self.museum_visits}, {self.view_collections}" + \
            f"{self.physical_visits}]"