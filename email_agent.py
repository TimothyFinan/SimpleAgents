import json
import os
from openai import OpenAI

# 1. Initialize the OpenAI client
client = OpenAI()

# 2. Your Simulated Gmail Inbox
MOCK_INBOX = [
    {
        "id": "msg_001",
        "sender": "netflix@netflix.com",
        "date": "2026-05-10",
        "subject": "Your monthly subscription receipt",
        "body": "Thank you for being a member! Your credit card ending in 4321 was charged $15.49.",
    },
    {
        "id": "msg_002",
        "sender": "accountant@taxpros.com",
        "date": "2026-05-12",
        "subject": "Tax Strategy for Q2",
        "body": "Hi there, regarding your question about write-offs: we should maximize your home office deduction and purchase the new equipment before June to offset your quarterly gains.",
    },
    {
        "id": "msg_003",
        "sender": "newsletter@techcrunch.com",
        "date": "2026-05-14",
        "subject": "Daily Tech Crunch Newsletter",
        "body": "Today we are looking at open-source AI frameworks, new developments in cybersecurity, and changes to venture capital funding.",
    },
    {
        "id": "msg_004",
        "sender": "me@domain.com",
        "date": "2026-05-15",
        "subject": "Follow up on tax strategy",
        "body": "Thanks for the note. I went ahead and bought the new development laptop to use as a business expense write-off for this tax year.",
    },
]


# 3. Define the actual Python search tool
def search_emails(query):
    print(f"  [TOOL RUNNING] Searching inbox for keyword: '{query}'")
    query_lower = query.lower()
    results = []

    # Look through our simulated database for keyword matches
    for email in MOCK_INBOX:
        if (
            query_lower in email["subject"].lower()
            or query_lower in email["body"].lower()
        ):
            results.append(email)

    return results


# 4. Define the JSON schema for our email search function
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Searches the user's email inbox for a specific keyword query. Returns matching emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "CRITICAL: Pass ONLY a single, broad keyword here (like 'tax' or 'invoice'). Do NOT pass multi-word phrases or sentences.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# 5. Set up the conversational state with your original goal question
messages = [
    {
        "role": "system",
        "content": "You are a personal email assistant. Use the tools provided to search the inbox and answer questions accurately.",
    },
    {
        "role": "user",
        "content": "Summarize what my accountant and I decided regarding our tax strategy based on our conversation history.",
    },
]

print(f"User Question: {messages[1]['content']}\n")

# 6. The core Agentic "While Loop"
while True:
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools_schema
    )

    response_message = response.choices[0].message
    messages.append(response_message)

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "search_emails":
                # Execute our local Python search function
                tool_output = search_emails(query=function_args.get("query"))
            else:
                tool_output = f"Error: Tool {function_name} not found."

            # Universal tool response append (your fix from earlier!)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(tool_output),  # Convert list to string
            })
            print(
                f"Agent Observation: Found {len(tool_output)} matching email(s).\n"
            )
    else:
        print(f"Final Agent Answer:\n{response_message.content}")
        break
