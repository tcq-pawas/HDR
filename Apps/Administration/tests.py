from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
import requests

from Apps.Administration.models import UserVerification
from Apps.Administration.services.bulksms import (
    build_otp_message,
    format_phone_for_bulksms,
    send_otp_sms,
)
from Apps.Administration.utils import generate_otp


class PhoneFormattingTests(TestCase):
    def test_ten_digit_indian_number(self):
        self.assertEqual(format_phone_for_bulksms("9876543210"), "+919876543210")

    def test_does_not_double_country_code(self):
        self.assertEqual(format_phone_for_bulksms("+919876543210"), "+919876543210")
        self.assertEqual(format_phone_for_bulksms("919876543210"), "+919876543210")

    def test_strips_formatting(self):
        self.assertEqual(format_phone_for_bulksms("91-98765-43210"), "+919876543210")

    def test_invalid_phone(self):
        self.assertIsNone(format_phone_for_bulksms(""))
        self.assertIsNone(format_phone_for_bulksms("12345"))


class OTPGenerationTests(TestCase):
    def test_generate_otp_length_and_digits(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_otp_message_template(self):
        message = build_otp_message("583921")
        self.assertIn("583921", message)
        self.assertIn("Valid for 10 minutes", message)
        self.assertIn("The Codiq Global Private Limited", message)


@override_settings(
    BULKSMS_TOKEN_ID="test-token-id",
    BULKSMS_TOKEN_SECRET="test-token-secret",
    BULKSMS_SENDER="HECTRE",
)
class BulkSMSServiceTests(TestCase):
    @patch("Apps.Administration.services.bulksms.requests.post")
    def test_bulksms_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = "[]"
        mock_post.return_value = mock_response

        result = send_otp_sms("9876543210", "583921")

        self.assertTrue(result["success"])
        self.assertIsNone(result["error_code"])
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.bulksms.com/v1/messages")
        payload = kwargs["json"]
        self.assertEqual(payload[0]["to"], "+919876543210")
        self.assertEqual(payload[0]["from"], "HECTRE")
        self.assertIn("583921", payload[0]["body"])
        self.assertIsNotNone(kwargs["auth"])

    @patch("Apps.Administration.services.bulksms.requests.post")
    def test_bulksms_auth_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        result = send_otp_sms("9876543210", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "auth_failed")

    @patch("Apps.Administration.services.bulksms.requests.post")
    def test_bulksms_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()
        result = send_otp_sms("9876543210", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "timeout")

    @patch("Apps.Administration.services.bulksms.requests.post")
    def test_bulksms_http_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        result = send_otp_sms("9876543210", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "provider_error")

    @patch("Apps.Administration.services.bulksms.requests.post")
    def test_bulksms_insufficient_credits(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Insufficient credits"
        mock_post.return_value = mock_response

        result = send_otp_sms("9876543210", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "insufficient_credits")

    def test_missing_credentials(self):
        with override_settings(BULKSMS_TOKEN_ID="", BULKSMS_TOKEN_SECRET=""):
            result = send_otp_sms("9876543210", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "missing_credentials")

    def test_invalid_phone(self):
        result = send_otp_sms("abc", "123456")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "invalid_phone")


@override_settings(
    BULKSMS_TOKEN_ID="test-token-id",
    BULKSMS_TOKEN_SECRET="test-token-secret",
    BULKSMS_SENDER="HECTRE",
)
class OTPApiFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="otpuser",
            email="otpuser@example.com",
            password="testpass123",
        )
        self.client.login(username="otpuser", password="testpass123")
        self.request_url = reverse("auth:request_otp")
        self.verify_url = reverse("auth:verify_otp")

    @patch("Apps.Administration.auth_views.send_otp_sms")
    def test_request_otp_success(self, mock_send):
        mock_send.return_value = {
            "success": True,
            "error_code": None,
            "message": "sent",
            "status_code": 201,
        }
        response = self.client.post(
            self.request_url,
            {"type": "mobile", "phone": "9876543210"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "OTP sent via SMS")

        verification = UserVerification.objects.get(user=self.user)
        self.assertEqual(verification.phone_number, "9876543210")
        self.assertTrue(verification.mobile_otp)
        self.assertEqual(len(verification.mobile_otp), 6)
        mock_send.assert_called_once()
        args, _kwargs = mock_send.call_args
        self.assertEqual(args[0], "9876543210")
        self.assertEqual(args[1], verification.mobile_otp)

    @patch("Apps.Administration.auth_views.send_otp_sms")
    def test_request_otp_provider_failure(self, mock_send):
        mock_send.return_value = {
            "success": False,
            "error_code": "auth_failed",
            "message": "failed",
            "status_code": 401,
        }
        response = self.client.post(
            self.request_url,
            {"type": "mobile", "phone": "9876543210"},
        )
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Failed to send SMS")

    def test_verify_valid_otp(self):
        verification = UserVerification.objects.create(
            user=self.user,
            phone_number="9876543210",
            mobile_otp="654321",
            otp_created_at=timezone.now(),
        )
        response = self.client.post(
            self.verify_url,
            {"type": "mobile", "otp": "654321"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        verification.refresh_from_db()
        self.assertTrue(verification.is_mobile_verified)
        self.assertIsNone(verification.mobile_otp)

    def test_verify_invalid_otp(self):
        UserVerification.objects.create(
            user=self.user,
            phone_number="9876543210",
            mobile_otp="654321",
            otp_created_at=timezone.now(),
        )
        response = self.client.post(
            self.verify_url,
            {"type": "mobile", "otp": "000000"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Invalid OTP")

    def test_verify_expired_otp(self):
        UserVerification.objects.create(
            user=self.user,
            phone_number="9876543210",
            mobile_otp="654321",
            otp_created_at=timezone.now() - timedelta(minutes=11),
        )
        response = self.client.post(
            self.verify_url,
            {"type": "mobile", "otp": "654321"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "OTP expired")
