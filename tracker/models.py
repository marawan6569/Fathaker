import uuid

from django.db import models

# Create your models here.

class Statistics(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
