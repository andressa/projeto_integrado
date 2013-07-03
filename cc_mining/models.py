"""
cc_mining app models
"""

from django.db import models
import json

class ClosedCaption(models.Model):
    """
    Class to describe acquired closed caption, line by line
    """
    timestamp = models.DateField(auto_now_add=True)
    closed_caption = models.CharField(max_length=256)

class CC(models.Model):
    tvshow = models.ForeignKey('TVShow')
    hour = models.DateTimeField()
    text = models.CharField(max_length=300)

class Programa(models.Model):
    name = models.CharField(max_length=80, unique=True)

class TVShow(models.Model):
    pid = models.ForeignKey('Programa')
    date = models.DateField()

class Saves(models.Model):
    fname = models.CharField(max_length=30)
    lbegin = models.IntegerField()
    lend = models.IntegerField()

class Analysis(models.Model):
    tvshow = models.ForeignKey('TVShow')


def load_json(instance, **kwargs):
    if not instance.json: return
    instance.json = json.loads(instance.json)

class Tree(models.Model):
    aid = models.ForeignKey('Analysis')
    json = models.TextField()

    def save(self, *args, **kwargs):
        self.json = json.dumps(self.json)
        super(Tree, self).save()

models.signals.post_init.connect(load_json, Tree)

