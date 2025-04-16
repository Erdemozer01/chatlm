from django.contrib.auth.models import User
from django.db import models


class Ask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.CharField(max_length=100)
    answer = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now=True)
