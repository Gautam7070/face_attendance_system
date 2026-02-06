import requests
import time

API_URL = "http://127.0.0.1:8000/attendance"

def send_to_cloud(payload, retries=3, timeout=15):
    """
    Sends attendance to the new SQLAlchemy backend with retry logic.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                API_URL,
                json={
                    "name": payload["name"],
                    "type": payload["type"]
                },
                timeout=timeout
            )

            if response.status_code == 200:
                print("✅ Attendance synced to cloud")
                return True
            else:
                print(f"⚠️ Cloud error {response.status_code}: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            if attempt == retries:
                print(f"❌ Max retries reached. Final attempt failed: {e}")
            time.sleep(2)

    return False
