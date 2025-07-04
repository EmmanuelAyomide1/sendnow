import requests

from decouple import config


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
        "Authorization": f"Basic {config('BULKSMS_API_KEY')}"
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
