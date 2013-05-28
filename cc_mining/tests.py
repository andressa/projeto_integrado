"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from ClosedCaptionHandler import ClosedCaptionHandler


class CCParser(TestCase):

    def setUp(self):
        self.cc = ClosedCaptionHandler(verbose=False)

    def test_a_lot(self):

        lines = [ '>> ANA MARIA BRAGA: TA MUITO CERTO.',
                '>> [ANA MARIA BRAGA] TA MUITO CERTO.',
                '>>> [ANA MARIA BRAGA] TA MUITO CERTO.']

        for line in lines:
            content = self.cc.parse(line)

            self.assertEquals(content['speaker']['name'], 'ANA MARIA BRAGA')
            self.assertEquals(content['text'], 'TA MUITO CERTO.')

    def test_no_speaker(self):

        content = self.cc.parse('>> TA MUITO CERTO.')
        self.assertEquals(content['speaker']['name'], '')
        self.assertEquals(content.get('text'), 'TA MUITO CERTO.')
