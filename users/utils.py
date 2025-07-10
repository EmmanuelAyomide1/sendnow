import cloudinary.uploader
import re
import requests

from decouple import config


def deleteImageInCloudinary(image):
    try:
        print(image.name)
        print(cloudinary.config())
        cloudinary.uploader.destroy(image.name)
        print("deleted successfully")
    except Exception as e:
        # Log error but continue with update
        print(f"Error deleting old image: {e}")


def verify_phone_number_format(phone_number):
    phone_regex = re.compile(r'^\+?1?\d{9,15}$')
    if not phone_regex.match(phone_number):
        return False
    return True


def send_OTP_using_vonage(phone_number, otp):
    """
    Sends an OTP to the given phone number using the BulkSMS API.
    """

    # clean up phone number
    phone_number = phone_number.replace(
        "+", "").replace(" ", "")
    phone_number = phone_number[:3] + phone_number[3::].lstrip("0")

    url = "https://messages-sandbox.nexmo.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "to": phone_number,
        "text": f"Your OTP is: {otp}",
        "from": "14157386102",
        "message_type": "text",
        "channel": "whatsapp"
    }

    response = requests.post(
        url,
        json=data,
        headers=headers,
        auth=(config('VONAGE_USERNAME'), config('VONAGE_PASSWORD'))
    )
    print("response", response.text)
    if response.status_code == 202:
        return True
    else:
        return False
