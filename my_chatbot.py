import os
from openai import OpenAI

client = OpenAI()

# Initialize the conversation state with a system personality
messages = [
    {
        "role": "system",
        "content": "You are a witty, helpful AI companion named TimBot. Feel free to give random funny comments based on the prompt",
    }
]

print("TimBot: Hello! Type 'exit' or 'quit' to end our conversation.\n")

# The Core Chatbot Loop
while True:
    # 1. Get input from the physical human user
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("TimBot: Goodbye!")
        break

    # 2. Append the human's message to the conversation history
    messages.append({"role": "user", "content": user_input})

    # 3. Stream or fetch the response from the LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    reply = response.choices[0].message.content
    print(f"\nTimBot: {reply}\n")

    # 4. Append the AI's response to the history so it remembers the context
    messages.append({"role": "assistant", "content": reply})
