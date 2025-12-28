"""
FHIR Subscription Manager - Register/manage subscriptions with HAPI FHIR server
"""

import requests
import json
from pathlib import Path

# Public HAPI FHIR Server
FHIR_SERVER_BASE_URL = 'https://hapi.fhir.org/baseR4'

def register_subscription(endpoint_url: str, config_path: str = None) -> dict:
    """
    Register a FHIR Subscription with the public HAPI server.
    
    Args:
        endpoint_url: Your public endpoint URL (e.g., http://YOUR_PUBLIC_IP:5001/fhir/notify)
        config_path: Path to subscription config JSON file
    
    Returns:
        Response dict with subscription ID and status
    """
    
    # Load subscription config
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            subscription = json.load(f)
    else:
        # Create default subscription
        subscription = {
            "resourceType": "Subscription",
            "status": "active",
            "criteria": "AuditEvent",
            "channel": {
                "type": "rest-hook",
                "endpoint": endpoint_url,
                "payload": "application/fhir+json"
            }
        }
    
    # Update endpoint in subscription
    subscription["channel"]["endpoint"] = endpoint_url
    
    # Register with HAPI server
    url = f"{FHIR_SERVER_BASE_URL}/Subscription"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    
    try:
        print(f"Registering subscription with {url}...")
        print(f"Endpoint: {endpoint_url}")
        
        response = requests.post(url, json=subscription, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        subscription_id = result.get('id', 'unknown')
        
        print(f"✓ Subscription registered successfully!")
        print(f"  Subscription ID: {subscription_id}")
        print(f"  Status: {result.get('status', 'unknown')}")
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "status": result.get('status'),
            "response": result
        }
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to register subscription: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def list_subscriptions() -> dict:
    """
    List all active subscriptions on the HAPI server.
    
    Returns:
        Response dict with list of subscriptions
    """
    url = f"{FHIR_SERVER_BASE_URL}/Subscription"
    headers = {
        "Accept": "application/fhir+json"
    }
    
    try:
        print(f"Fetching subscriptions from {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        subscriptions = result.get('entry', [])
        
        print(f"✓ Found {len(subscriptions)} subscription(s)")
        for sub in subscriptions:
            sub_data = sub.get('resource', {})
            print(f"  - ID: {sub_data.get('id')}")
            print(f"    Status: {sub_data.get('status')}")
            print(f"    Endpoint: {sub_data.get('channel', {}).get('endpoint')}")
        
        return {
            "success": True,
            "count": len(subscriptions),
            "subscriptions": subscriptions
        }
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to fetch subscriptions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fhir_subscription_manager.py <command> [endpoint_url]")
        print("\nCommands:")
        print("  register <endpoint_url>  - Register a new subscription")
        print("  list                     - List all subscriptions")
        print("\nExample:")
        print("  python fhir_subscription_manager.py register http://YOUR_PUBLIC_IP:5001/fhir/notify")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register":
        if len(sys.argv) < 3:
            print("Error: endpoint_url required for register command")
            sys.exit(1)
        endpoint = sys.argv[2]
        register_subscription(endpoint)
    
    elif command == "list":
        list_subscriptions()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
