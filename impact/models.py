from __future__ import division
from django.db import models
from django.contrib.auth.models import User
import datetime


class Calculation(models.Model):
    """Calculation model
    """

    user = models.ForeignKey(User)
    success = models.BooleanField()
    run_date = models.DateTimeField()
    run_duration = models.FloatField()
    impact_function = models.CharField(max_length=255, null=True, blank=True)
    impact_function_source = models.TextField()
    exposure_server = models.URLField(null=True, blank=True)
    exposure_layer = models.CharField(max_length=255, null=True, blank=True)
    hazard_server = models.URLField(null=True, blank=True)
    hazard_layer = models.CharField(max_length=255, null=True, blank=True)
    bbox = models.CharField(max_length=255, null=True, blank=True)
    errors = models.CharField(max_length=255, null=True, blank=True)
    stacktrace = models.TextField(null=True, blank=True)
    layer = models.CharField(max_length=255, null=True, blank=True)

    @property
    def url(self):
        return self.layer.url

    def get_absolute_url(self):
        return self.layer.get_absolute_url()

    def __unicode__(self):
        if self.success:
            name = 'Sucessful Calculation'
        else:
            name = 'Failed Calculation'
        return '%s at %s' % (name, self.run_date)


class Server(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()

    def __unicode__(self):
        return self.name


class Workspace(models.Model):
    user = models.ForeignKey(User)
    servers = models.ManyToManyField(Server)

    def __unicode__(self):
        return self.user.username


def duration(sender, **kwargs):
    instance = kwargs['instance']
    now = datetime.datetime.now()
    td = now - instance.run_date
    duration = td.microseconds / 1000000 + td.seconds + td.days * 24 * 3600
    instance.run_duration = round(duration, 2)

models.signals.pre_save.connect(duration, sender=Calculation)
