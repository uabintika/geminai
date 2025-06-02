def exit_function(text: str) -> bool:
    exit_commands = ["bye", "exit", "quit"]
    return text.lower() in exit_commands