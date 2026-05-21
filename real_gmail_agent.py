import base64
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI

# 1. Initialize our API clients
client = OpenAI()

# The full, untruncated path required by Google's API gateway
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# Helper function to load our secure Gmail login token
def get_gmail_service():
    if not os.path.exists("token.json"):
        raise FileNotFoundError(
            "token.json not found! Please run gmail_auth.py first to log in."
        )
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("gmail", "v1", credentials=creds)


# --- AGENT TOOL 1: Search and return light metadata summaries ---
def search_gmail_metadata(query):
    print(f"  [TOOL RUNNING] Searching live Gmail for keyword: '{query}'")
    service = get_gmail_service()

    # Call Google's search API
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=5)
        .execute()
    )

    # FIX: Renamed 'messages' to 'gmail_results' to completely prevent variable collision
    gmail_results = response.get("messages", [])

    if not gmail_results:
        return "No matching emails found."

    summaries = []
    # Pull light overview data for the top matching email headers
    for msg in gmail_results:
        msg_data = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="metadata")
            .execute()
        )
        headers = msg_data.get("payload", {}).get("headers", [])

        subject = next(
            (h["value"] for h in headers if h["name"].lower() == "subject"),
            "(No Subject)",
        )
        sender = next(
            (h["value"] for h in headers if h["name"].lower() == "from"),
            "Unknown",
        )

        summaries.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "snippet": msg_data.get("snippet", ""),
        })

    return summaries


# --- AGENT TOOL 2: Deep dive to read one single full email body ---
def get_email_body(message_id):
    print(f"  [TOOL RUNNING] Fetching full body for email ID: {message_id}")
    service = get_gmail_service()

    msg_data = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    payload = msg_data.get("payload", {})

    # Decode the email body text out of Google's base64 data wrapper
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                body += base64.urlsafe_b64decode(data).decode("utf-8")
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8")

    return {
        "id": message_id,
        "snippet": msg_data.get("snippet", ""),
        "full_body": body[:2000],  # Caps text length to protect your API token costs
    }


# 2. Map both schemas so the LLM understands its two-step capabilities
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_gmail_metadata",
            "description": "Searches Gmail and returns a lightweight list of matching email IDs, senders, and snippets. Use this first to browse matches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search keyword query (e.g. 'tax strategy', 'receipt'). Keep it to 1-3 broad keywords.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_body",
            "description": "Fetches the full raw text body of a specific email using its unique message ID. Use this after searching if you need to read the deep details of an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The unique message ID string returned by search_gmail_metadata.",
                    }
                },
                "required": ["message_id"],
            },
        },
    },
]

print("TimBot: Gmail Agent Active! Type 'exit' or 'quit' to stop.\n")

# 3. The Master Conversational Input Loop
while True:
    # ALWAYS reset to a clean, fresh history array for every brand new question
    messages = [
        {
            "role": "system",
            "content": "You are an executive email assistant. First, search for relevant message cards. If you see high-probability matches, run get_email_body on their IDs to analyze their contents before outputting your final summary answer.",
        }
    ]

    # Get input from the physical human user
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("TimBot: Goodbye!")
        break

    # Append the human's message to the conversation history
    messages.append({"role": "user", "content": user_input})

    # 4. The Linear Agentic Reasoning Execution Loop
    agent_is_thinking = True
    while agent_is_thinking:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools_schema
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Check if the model wants to call a tool
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name == "search_gmail_metadata":
                    tool_output = search_gmail_metadata(
                        query=function_args.get("query")
                    )
                elif function_name == "get_email_body":
                    tool_output = get_email_body(
                        message_id=function_args.get("message_id")
                    )
                else:
                    tool_output = f"Error: Tool {function_name} not found."

                # Append tool output to history so the LLM sees it on the next loop tick
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_output),
                })
                print(
                    f"Agent Observation: Completed execution for {function_name}.\n"
                )
        else:
            # If no tools are requested, it means the agent has formulated the final response
            print(f"Final Agent Answer:\n{response_message.content}\n")
            agent_is_thinking = (
                False  # Clears the flag to break the internal loop cleanly
            )
