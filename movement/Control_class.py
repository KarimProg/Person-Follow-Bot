import requests

class Control:
    def __init__(self):
        # ESP IP address
        self.esp_ip = "http://10.42.0.253:8080"
        self.route = "/speeds"

    def post_speeds(self, y, yaw):
        # Data payload
        payload = {"y": y, "yaw": yaw}

        # Send POST request with timeout
        try:
            response = requests.post(f"{self.esp_ip}{self.route}", data=payload, timeout=1)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send data. Error: {e}")
            return

        # Check response
        if response.status_code == 200:
            print("Response from ESP:", response.text)
            1
        else:
            print(f"Failed to send data. Status code: {response.status_code}")
