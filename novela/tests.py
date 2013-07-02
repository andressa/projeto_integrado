from django.test import TestCase
from views import CCParser
from novela import main

class CCParserTest(TestCase):

    def setUp(self):
        self.lines = [
                ('[NICOLE] lalala', ('', 'NICOLE', 'lalala')),
                ('>> NICOLE: lalala', ('', 'NICOLE', 'lalala')),
                ('>>> NICOLE: lalala', ('', 'NICOLE', 'lalala')),
                ('lalalal', ('', '', 'lalalal')),
                ('>> lalala', ('', '', 'lalala')),
                ('de Sangue Bom -----------------------------', ('', '', 'de Sangue Bom -----------------------------')),
                ('speaker: lalala', ('', '', 'speaker: lalala')),
                ('[APLAUSO]', ('APLAUSO', '', ''))
                ]
        self.c = CCParser()

    def test_cases(self):
        for line, attrs in self.lines:
            a = self.c.parse(line)
            self.assertEqual( attrs,
                    (a['action'], a['speaker'], a['text']))

