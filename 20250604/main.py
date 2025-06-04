import os
import json
import requests
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

# Config
token = os.getenv("AIKEY")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-nano"
MEMORY_FILE = "memory.txt"

client = OpenAI(base_url=endpoint, api_key=token)

# Functions
def write_to_memory(content: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {content}\n")
    return f"Saved: {content}"

def read_from_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        return "Memory is empty."
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return content or "Memory is empty."

def handle_function_call(name: str, args: dict) -> str:
    if name == "write_to_memory":
        return write_to_memory(args.get("content", ""))
    elif name == "read_from_memory":
        return read_from_memory()
    elif name == "get_kursenai_info":
        return get_kursenai_info()
    elif name == "search_web":
        return search_web(args.get("query", ""))
    return "Unknown function."

def get_kursenai_info() -> str:
    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": "Kuršėnai"
        }
    )
    data = response.json()
    page = next(iter(data["query"]["pages"].values()))
    return page.get("extract", "Could not find information about Kuršėnai.")

def search_web(query: str) -> str:
    print(f"[Web Search] Query: {query}")
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        output = []
        for r in results:
            output.append(f"- {r['title']}: {r['href']}")
        return "Top web results:\n" + "\n".join(output) if output else "No results found."

# Tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "write_to_memory",
            "description": "Store important user info to memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Text to save."
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_from_memory",
            "description": "Read everything saved in memory.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kursenai_info",
            "description": "Get a brief summary about Kuršėnai, Lithuania.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web when memory or known information is not sufficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Main magic
def main():
    print("Say something or ask about Kuršėnai.")
    print("Type 'exit' to quit.\n")

    messages = [{
        "role": "system",
        "content": (
            "You're a helpful assistant with memory features and knowledge about Kuršėnai. "
            "Use 'write_to_memory' to store facts, 'read_from_memory' to recall them, "
            "and 'get_kursenai_info' when asked about Kuršėnai or Lithuania."
            "Before responding check the memory for relevant information."
            "If I'm asking something about myself and you don't have it in memory, then ask me for it and save it in memory."
            "When you ask the user for missing information, remember to save it to memory using the 'write_to_memory' tool. Before asking again, read the memory using 'read_from_memory' to check if the information was already stored earlier. Do not repeatedly ask for the same information if it's already available in memory."
        )
    }]

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit", "bye"):
                print("AI: Goodbye!")
                break

            messages.append({"role": "user", "content": user_input})
            memory_content = read_from_memory()
            memory_tool_call = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "tool_read_memory",
                        "type": "function",
                        "function": {
                            "name": "read_from_memory",
                            "arguments": "{}"
                        }
                    }
                ]
            }
            memory_tool_response = {
                "role": "tool",
                "tool_call_id": "tool_read_memory",
                "content": memory_content
            }
            messages.append(memory_tool_call)
            messages.append(memory_tool_response)

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            reply = response.choices[0].message

            if reply.tool_calls:
                messages.append(reply)
                for call in reply.tool_calls:
                    function_name = call.function.name
                    args = json.loads(call.function.arguments)
                    result = handle_function_call(function_name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result
                    })

                final = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                answer = final.choices[0].message.content
            else:
                answer = reply.content

            messages.append({"role": "assistant", "content": answer})
            print("AI:", answer)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()
