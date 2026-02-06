import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from alerts.whatsapp import send_whatsapp_alert

def main():
    print("🚀 Sending Test WhatsApp Alert...")
    print("Note: Ensure your Twilio Sandbox is active and you have joined it.")
    
    success = send_whatsapp_alert("TestUser", "Punch-In")
    
    if success:
        print("✅ Alert Sent Successfully!")
    else:
        print("❌ Failed to send alert. Check your credentials in alerts/whatsapp.py and ensure you are not on cooldown.")

if __name__ == "__main__":
    main()
