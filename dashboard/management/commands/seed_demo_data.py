from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from dashboard.mock_data import ensure_user_mock_data


class Command(BaseCommand):
    help = "Seeds realistic demo data for a given user (only if they have none)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Username/email of the user to seed")

    def handle(self, *args, **options):
        email = options["email"]
        User = get_user_model()
        user = User.objects.filter(username=email).first()
        if not user:
            self.stderr.write(self.style.ERROR(f"User not found: {email}"))
            return
        ensure_user_mock_data(user)
        self.stdout.write(self.style.SUCCESS("Demo data ensured for user."))

