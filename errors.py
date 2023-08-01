import json
import requests
import uuid

API_key = "7NAYSRJQDZWRGENVBTZSJGD60IP60FXJ"


def generate_api_response(user_text):

    url = 'https://api.sapling.ai/api/v1/edits'

    # Generate a random UUID (version 4) as a string
    uuid_string = str(uuid.uuid4())

    print('uuid_string>>>>>>>>>>>>>>>>>>>>', uuid_string)

    data_to_send = {
        "key": API_key,
        "text": user_text,
        "session_id": uuid_string
    }

    try:
        response = requests.post(url, json=data_to_send)

        if response.status_code == 200:
            # Successful API call
            data = response.json()  # Assuming the response is in JSON format
            # print('DATA>>>>>>>>>>>>>>', data)
            return data
        else:
            # API call failed
            print(f"API call failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Catch any exceptions that might occur during the API call
        print(f"An error occurred: {e}")

