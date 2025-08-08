from django.conf import settings
from eskiz.client.sync import ClientSync


def send_otp_code(number: str, code: int):
    if settings.DEBUG or settings.TESTING:
        return print(f"{number}: {code}")

    eskiz_client = ClientSync(
        email=settings.OTP_EMAIL,
        password=settings.OTP_PASSWORD,
    )

    text = f"SpiskaUz dasturi ro'yhatdan o'tish tasdiqlash kodi: {code}"

    resp = eskiz_client.send_sms(phone_number=int(number[1:]), message=text)

    return resp
