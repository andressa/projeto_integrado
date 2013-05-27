"""
cc_mining app models
"""

from django.db import models

class ClosedCaption(models.Model):
    """
    Class to describe acquired closed caption, line by line
    """
    timestamp = models.DateField(auto_now_add=True)
    closed_caption = models.CharField(max_length=256)
