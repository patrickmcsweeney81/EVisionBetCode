"""
betfair_api.py
Utility functions for connecting to Betfair Exchange API using credentials from config.
"""
import logging
from core import config

try:
    import betfairlightweight
except ImportError:
    raise ImportError("Please install betfairlightweight: pip install betfairlightweight")


def get_betfair_client(active=True):
    """
    Returns a betfairlightweight APIClient using the active or testing API key.
    """
    api_key = config.BETFAIR_API_KEY_ACTIVE if active else config.BETFAIR_API_KEY_TESTING
    if not api_key:
        raise ValueError("Betfair API key not set in environment/config.")
    # Username/password/certs would be required for full login; placeholder for now
    # Example: trading = betfairlightweight.APIClient(username, password, app_key=api_key, certs=certs_path)
    return api_key  # Placeholder: return key for now


def example_usage():
    key = get_betfair_client()
    print(f"Loaded Betfair API key: {key}")

if __name__ == "__main__":
    example_usage()
