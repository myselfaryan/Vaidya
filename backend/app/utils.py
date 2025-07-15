# Utilities for backend processing

def validate_data(data):
    """Simple data validation utility."""
    if not data:
        raise ValueError("Data cannot be empty.")
    return True


def log_action(action: str) -> None:
    """Log an action for auditing purposes."""
    print(f"Action logged: {action}")
