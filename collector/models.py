from django.db import models
from museum_site.models import User

# Create your models here.
class Interaction(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    timestamp = models.DateTimeField()
    content_id = models.CharField(max_length = 32)
    event = models.CharField(max_length = 64)
    page = models.CharField(max_length = 256)

    def __str__(self):
        return f"[{self.timestamp}] {self.user.user_id} {self.event} {self.content_id} {self.page}"