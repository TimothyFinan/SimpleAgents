import json
import os
import datetime
from openai import OpenAI

# 1. Initialize the client (it automatically picks up the OPENAI_API_KEY env variable)
client = OpenAI()


# 2. Define the actual Python tool the agent can use
def add_numbers(a, b):
    print(f"  [TOOL RUNNING] Executing add_numbers with a={a}, b={b}")
    return a + b

def get_current_time():
    print("  [TOOL RUNNING] Executing get_current_time")
    # Returns the current date and time as a readable string
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def dumb_tool():
    print("  [TOOL RUNNING] Executing dumb_tool")
    return "If a tomato is a fruit, is ketchup a smoothie?"

# 3. Define the tool's JSON schema so the LLM knows it exists and how to use it
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": "Adds two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "The first number",
                    },
                    "b": {
                        "type": "number",
                        "description": "The second number",
                    },
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current local date and time on the host system.",
            "parameters": {
                "type": "object",
                "properties": {},  # No arguments needed for this tool
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dumb_tool",
            "description": "Returns a random dumb response.",
            "parameters": {
                "type": "object",
                "properties": {},  # No arguments needed for this tool
            },
        },
    }
]

# 4. Set up our initial conversation state
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. You must use the tools provided to answer math questions. ",
    },
    {
        "role": "user",
        "content": "What is 43 + 3?",
    },
]

print(f"User Question: {messages[1]['content']}\n")

# 5. The core Agentic "While Loop"
while True:
    # Ask the LLM what to do next, passing it our message history and tool schemas
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools_schema
    )

    response_message = response.choices[0].message
    messages.append(response_message)  # Save the LLM's thought/response to history

    # Check if the LLM wants to call a tool
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(
                f"Agent Thought: I need to call the '{function_name}' function."
            )

            # Execute the matching Python function
            if function_name == "add_numbers":
                tool_output = add_numbers(
                    a=function_args.get("a"), b=function_args.get("b")
                )
            elif function_name == "get_current_time":
                    tool_output = get_current_time()
            elif function_name == "dumb_tool":  # <-- ADD THIS FIXED BLOCK
                tool_output = dumb_tool()
            else:
                tool_output = f"Error: Tool {function_name} not found."
                # Format the tool output as a "tool" role message and add to history
                # This lets the LLM see the result of its action in the next loop iteration
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_output),
            })
            print(f"Agent Observation: The tool returned {tool_output}\n")
    else:
        # If the LLM didn't request a tool, it means it has the final answer
        print(f"Final Agent Answer: {response_message.content}")
      #  print(f"Role of Final Answer: {response_message.role}")
        break
