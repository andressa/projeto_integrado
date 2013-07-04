"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from cc_mining.views import *

class TestCopa(TestCase):
    def test_json(self):
        test_copa()
