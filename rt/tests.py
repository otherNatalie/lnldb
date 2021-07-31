from data.tests.util import ViewTestCase
from django.shortcuts import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from cryptography.fernet import Fernet

from accounts.models import UserPreferences


class RTAPITests(ViewTestCase):
    def test_ticket_form(self):
        # Check that form loads ok
        self.assertOk(self.client.get(reverse("support:new-ticket")))

        # Test response with invalid data
        invalid_data = {
            "subject": "Website broken",
            "description": "",
            "attachments": [],
            "save": "Submit"
        }
        self.assertOk(self.client.post(reverse("support:new-ticket"), invalid_data))

        # Check response with valid data
        attachment = SimpleUploadedFile('test.txt', b'Contents of a file')
        valid_data = {
            "subject": "Website broken",
            "description": "I tried using this website to file my taxes but it isn't working for some reason",
            "attachments": [attachment],
            "save": "Submit"
        }

        # We do not want to submit new tickets if testing is triggered in prod
        if settings.RT_TOKEN in ['', None]:
            self.assertRedirects(self.client.post(reverse("support:new-ticket"), valid_data), reverse("home"))

    def test_account_setup(self):
        # Check that form loads ok
        self.assertOk(self.client.get(reverse("support:link-account")))

        # Test valid entry
        data = {
            "token": "1-234-567890abcdef1a2b3c4d5e6f7f8e9d0c",
            "save": "Submit"
        }

        self.assertRedirects(self.client.post(reverse("support:link-account"), data, follow=True),
                             reverse("accounts:detail", args=[self.user.pk]))

        # Check that user preferences exist
        self.assertTrue(UserPreferences.objects.filter(user=self.user).exists())

        # If the cryptographic key is available, check that the token was saved properly
        if settings.RT_CRYPTO_KEY:
            prefs = UserPreferences.objects.get(user=self.user)
            cipher_suite = Fernet(settings.RT_CRYPTO_KEY)
            self.assertEqual(data["token"], cipher_suite.decrypt(prefs.rt_token.encode('utf-8')).decode('utf-8'))
