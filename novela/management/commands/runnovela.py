from django.core.management.base import BaseCommand, CommandError
from novela import tree

class Command(BaseCommand):

        def handle(self, *args, **options):
            tree.main()
