#!/usr/bin/env python3
"""
Test FHIR Event Polling Integration
Demonstrates polling AuditEvents from public HAPI server
"""

import sys
import time
import json
import requests
from datetime import datetime

# Add app to path
sys.path.insert(0, 'app')

from fhir_event_poller import FHIREventPoller
from config import (
    FHIR_SERVER_BASE_URL,
    FHIR_POLLING_INTERVAL,
    FHIR_POLLING_BATCH_SIZE,
    FHIR_POLLING_RESOURCE_TYPE
)


def print_event(event):
    """Pretty print a FHIR event"""
    resource_type = event.get('resourceType', 'Unknown')
    event_id = event.get('id', 'N/A')
    timestamp = event.get('recorded', 'N/A')
    
    print(f"\n{'='*70}")
    print(f"📌 {resource_type} Event Received")
    print(f"{'='*70}")
    print(f"ID:        {event_id}")
    print(f"Timestamp: {timestamp}")
    
    # Extract audit event specific info
    if resource_type == 'AuditEvent':
        event_type = event.get('type', {}).get('coding', [{}])[0].get('code', 'N/A')
        action = event.get('action', 'N/A')
        outcome = event.get('outcome', 'N/A')
        
        print(f"Type:      {event_type}")
        print(f"Action:    {action}")
        print(f"Outcome:   {outcome}")
        
        # Extract agent info
        agents = event.get('agent', [])
        if agents:
            agent = agents[0]
            print(f"Agent:     {agent.get('name', 'Unknown')}")
            print(f"Role:      {agent.get('role', [{}])[0].get('coding', [{}])[0].get('code', 'N/A')}")
    
    print()


def test_hapi_connectivity():
    """Test if we can reach the HAPI server"""
    print(f"\nTesting HAPI Server Connectivity...")
    print(f"Server: {FHIR_SERVER_BASE_URL}")
    
    try:
        response = requests.head(f"{FHIR_SERVER_BASE_URL}/metadata", timeout=5)
        if response.status_code == 200:
            print(f"✓ HAPI Server is reachable")
            return True
        else:
            print(f"✗ HAPI Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot reach HAPI Server: {e}")
        return False


def test_polling():
    """Test the polling functionality"""
    print(f"\n{'='*70}")
    print(f"FHIR Event Polling Test")
    print(f"{'='*70}")
    print(f"Server: {FHIR_SERVER_BASE_URL}")
    print(f"Resource: {FHIR_POLLING_RESOURCE_TYPE}")
    print(f"Poll Interval: {FHIR_POLLING_INTERVAL}s")
    print(f"Batch Size: {FHIR_POLLING_BATCH_SIZE}")
    print(f"{'='*70}\n")
    
    # Check connectivity first
    if not test_hapi_connectivity():
        print("\n✗ Cannot connect to HAPI server. Cannot proceed with polling test.")
        return False
    
    # Create poller
    poller = FHIREventPoller(
        fhir_base_url=FHIR_SERVER_BASE_URL,
        poll_interval_seconds=FHIR_POLLING_INTERVAL,
        batch_size=FHIR_POLLING_BATCH_SIZE,
        resource_type=FHIR_POLLING_RESOURCE_TYPE
    )
    
    # Test single fetch
    print(f"\nTesting single event fetch...")
    events = poller.fetch_events()
    
    if events:
        print(f"✓ Successfully fetched {len(events)} event(s)")
        for event in events[:3]:  # Show first 3
            print_event(event)
    else:
        print(f"ℹ No new events found (this is normal if no recent events)")
    
    # Get stats
    stats = poller.get_stats()
    print(f"\nPoller Statistics:")
    print(f"  Events Fetched: {stats['events_fetched']}")
    print(f"  Last Update: {stats['last_update']}")
    
    # Test continuous polling
    print(f"\n{'='*70}")
    print(f"Starting Continuous Polling (10 seconds, Ctrl+C to stop)")
    print(f"{'='*70}\n")
    
    event_count = 0
    
    def handle_event(event):
        nonlocal event_count
        event_count += 1
        print_event(event)
    
    poller.start_polling(callback=handle_event, daemon=False)
    
    try:
        start_time = time.time()
        while time.time() - start_time < 10:  # Run for 10 seconds
            status = poller.get_stats()
            elapsed = int(time.time() - start_time)
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Elapsed: {elapsed}s | Events Received: {event_count} | "
                  f"Total Fetched: {status['events_fetched']}", 
                  end='', flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        poller.stop_polling()
    
    print(f"\n\n{'='*70}")
    print(f"Test Results:")
    print(f"{'='*70}")
    print(f"✓ Polling Started Successfully")
    print(f"✓ Events Processed: {event_count}")
    print(f"✓ Total Events Fetched: {stats['events_fetched']}")
    print(f"{'='*70}\n")
    
    return True


if __name__ == '__main__':
    try:
        success = test_polling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
