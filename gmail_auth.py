import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the "scopes" (permissions) your agent is allowed to have.
# 'gmail.readonly' allows the AI to read your emails but NOT delete or send them.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate_gmail():
    creds = None

    # 1. Check if a previously generated login token already exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # 2. If there are no valid credentials available, make the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing your expired login token...")
            creds.refresh(Request())
        else:
            print("No valid token found. Starting web browser login flow...")
            # Load your downloaded credentials file
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # Opens a local browser tab on port 0 (auto-selected)
            creds = flow.run_local_server(port=0)

        # 3. Save the secure token for future runs so you don't have to log in every time
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        print("Success! Login token saved to 'token.json'\n")

    # 4. Connect to the live Gmail API service using your keys
    service = build("gmail", "v1", credentials=creds)
    return service


if __name__ == "__main__":
    # Test the connection independently
    print("Testing connection to Gmail API...")
    service = authenticate_gmail()

    # Fetch the profile info of the logged-in user to prove it works
    profile = service.users().getProfile(userId="me").execute()
    print(f"Connected successfully to inbox: {profile.get('emailAddress')}")
