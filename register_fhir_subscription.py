"""
FHIR Subscription Manager - Standalone script to register/manage subscriptions with HAPI FHIR server
This script runs independently without importing the Flask app
"""

import requests
import json
from pathlib import Path
import sys
import os

# Public HAPI FHIR Server
FHIR_SERVER_BASE_URL = 'https://hapi.fhir.org/baseR4'

def register_subscription(endpoint_url: str, config_path: str = None, criteria: str = None) -> dict:
    """
    Register a FHIR Subscription with the public HAPI server.
    
    Args:
        endpoint_url: Your public endpoint URL (e.g., https://your-ngrok-url.ngrok-free.dev:5001/fhir/notify)
        config_path: Path to subscription config JSON file
        criteria: FHIR resource criteria (e.g., 'Patient', 'Observation', 'Encounter')
    
    Returns:
        Response dict with subscription ID and status
    """
    
    # Default to Patient if no criteria specified
    if criteria is None:
        criteria = "Patient"
    
    # Load subscription config
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            subscription = json.load(f)
    else:
        # Create default subscription
        subscription = {
            "resourceType": "Subscription",
            "status": "active",
            "criteria": criteria,
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
        print(f"Payload: {json.dumps(subscription, indent=2)}\n")
        
        response = requests.post(url, json=subscription, headers=headers, timeout=10)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
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
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
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
        
        print(f"✓ Found {len(subscriptions)} subscription(s)\n")
        for sub in subscriptions:
            sub_data = sub.get('resource', {})
            print(f"  ID: {sub_data.get('id')}")
            print(f"  Status: {sub_data.get('status')}")
            print(f"  Criteria: {sub_data.get('criteria')}")
            print(f"  Endpoint: {sub_data.get('channel', {}).get('endpoint')}")
            print()
        
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


def get_subscription(sub_id: str) -> dict:
    """
    Get details of a specific subscription.
    
    Args:
        sub_id: Subscription ID
    
    Returns:
        Response dict with subscription details
    """
    url = f"{FHIR_SERVER_BASE_URL}/Subscription/{sub_id}"
    headers = {
        "Accept": "application/fhir+json"
    }
    
    try:
        print(f"Fetching subscription {sub_id}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✓ Subscription found")
        print(f"  ID: {result.get('id')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Criteria: {result.get('criteria')}")
        print(f"  Endpoint: {result.get('channel', {}).get('endpoint')}")
        
        return {
            "success": True,
            "subscription": result
        }
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to fetch subscription: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FHIR Subscription Manager")
        print("=" * 50)
        print("\nUsage: python register_fhir_subscription.py <command> [arguments]")
        print("\nCommands:")
        print("  register <endpoint_url> [criteria]  - Register a new subscription (default criteria: Patient)")
        print("  list                                - List all subscriptions")
        print("  get <subscription_id>               - Get subscription details")
        print("\nSupported Criteria (Common):")
        print("  Patient, Observation, Encounter, MedicationRequest, Condition")
        print("\nExamples:")
        print("  python register_fhir_subscription.py register https://missy-unaggravated-dandiacally.ngrok-free.dev:5001/fhir/notify")
        print("  python register_fhir_subscription.py register https://missy-unaggravated-dandiacally.ngrok-free.dev:5001/fhir/notify Patient")
        print("  python register_fhir_subscription.py register https://missy-unaggravated-dandiacally.ngrok-free.dev:5001/fhir/notify Observation")
        print("  python register_fhir_subscription.py list")
        print("  python register_fhir_subscription.py get abc123")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register":
        if len(sys.argv) < 3:
            print("Error: endpoint_url required for register command")
            print("Usage: python register_fhir_subscription.py register <endpoint_url> [criteria]")
            sys.exit(1)
        endpoint = sys.argv[2]
        criteria = sys.argv[3] if len(sys.argv) > 3 else None
        register_subscription(endpoint, criteria=criteria)
    
    elif command == "list":
        list_subscriptions()
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: subscription_id required for get command")
            print("Usage: python register_fhir_subscription.py get <subscription_id>")
            sys.exit(1)
        sub_id = sys.argv[2]
        get_subscription(sub_id)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python register_fhir_subscription.py' with no arguments for help")
        sys.exit(1)
