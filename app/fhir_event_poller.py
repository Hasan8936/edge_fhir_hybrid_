"""
FHIR Event Poller - Fetch AuditEvents from public HAPI FHIR server
Polls periodically since subscriptions are restricted on public servers
"""

import requests
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FHIREventPoller:
    """Polls a FHIR server for new AuditEvents"""
    
    def __init__(
        self,
        fhir_base_url: str,
        poll_interval_seconds: int = 30,
        batch_size: int = 10,
        resource_type: str = 'AuditEvent',
        tracking_file: str = None
    ):
        """
        Initialize FHIR Event Poller
        
        Args:
            fhir_base_url: Base URL of FHIR server (e.g., 'https://hapi.fhir.org/baseR4')
            poll_interval_seconds: How often to poll (default 30 seconds)
            batch_size: How many resources to fetch per poll
            resource_type: FHIR resource type to monitor (default 'AuditEvent')
            tracking_file: File to store last fetched timestamp for deduplication
        """
        self.fhir_base_url = fhir_base_url.rstrip('/')
        self.poll_interval = poll_interval_seconds
        self.batch_size = batch_size
        self.resource_type = resource_type
        self.tracking_file = tracking_file or '.fhir_polling_tracker.json'
        self.is_running = False
        self.last_update = self._load_last_update()
        self.events_fetched = 0
        self.thread = None
        
        logger.info(
            f"Initialized FHIR Poller for {resource_type} "
            f"(interval: {poll_interval_seconds}s, batch: {batch_size})"
        )
    
    def _load_last_update(self) -> str:
        """Load last update timestamp for deduplication"""
        try:
            if Path(self.tracking_file).exists():
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    timestamp = data.get('last_update')
                    logger.info(f"Loaded last update timestamp: {timestamp}")
                    return timestamp
        except Exception as e:
            logger.warning(f"Could not load tracking file: {e}")
        
        # Default to 1 hour ago if no tracking file
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        return one_hour_ago
    
    def _save_last_update(self, timestamp: str):
        """Save last update timestamp"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump({
                    'last_update': timestamp,
                    'saved_at': datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tracking file: {e}")
    
    def _build_query(self) -> dict:
        """Build search parameters for FHIR query"""
        params = {
            '_count': self.batch_size,
            '_sort': '-_lastUpdated',  # Newest first
        }
        
        # If we have a last update time, fetch only newer events
        if self.last_update:
            params['_lastUpdated'] = f'ge{self.last_update}'
        
        return params
    
    def fetch_events(self) -> list:
        """
        Fetch new events from FHIR server
        
        Returns:
            List of FHIR resources (dicts)
        """
        url = f"{self.fhir_base_url}/{self.resource_type}"
        params = self._build_query()
        headers = {
            'Accept': 'application/fhir+json'
        }
        
        try:
            logger.info(f"Polling {url} with params: {params}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            bundle = response.json()
            entries = bundle.get('entry', [])
            resources = [entry['resource'] for entry in entries]
            
            if resources:
                logger.info(f"✓ Fetched {len(resources)} {self.resource_type} event(s)")
                self.events_fetched += len(resources)
                
                # Update tracking timestamp
                newest_event = resources[0]  # First one is newest (sorted -_lastUpdated)
                updated = newest_event.get('meta', {}).get('lastUpdated')
                if updated:
                    self._save_last_update(updated)
                    logger.debug(f"Updated tracking timestamp to: {updated}")
            else:
                logger.debug(f"No new {self.resource_type} events")
            
            return resources
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch events: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return []
    
    def start_polling(self, callback=None, daemon=True):
        """
        Start polling in background thread
        
        Args:
            callback: Function to call with each fetched event: callback(event)
            daemon: If True, thread exits when main program exits
        """
        if self.is_running:
            logger.warning("Poller is already running")
            return
        
        self.callback = callback
        self.is_running = True
        
        def polling_loop():
            logger.info(f"Starting polling loop (interval: {self.poll_interval}s)")
            while self.is_running:
                try:
                    events = self.fetch_events()
                    
                    if events and callback:
                        for event in events:
                            try:
                                callback(event)
                            except Exception as e:
                                logger.error(f"Error in callback: {e}")
                    
                    time.sleep(self.poll_interval)
                
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    time.sleep(self.poll_interval)
        
        self.thread = threading.Thread(target=polling_loop, daemon=daemon)
        self.thread.name = f"FHIRPoller-{self.resource_type}"
        self.thread.start()
        
        logger.info(f"Polling thread started (daemon={daemon})")
    
    def stop_polling(self):
        """Stop polling thread"""
        logger.info("Stopping polling...")
        self.is_running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            logger.info("Polling stopped")
    
    def get_stats(self) -> dict:
        """Get polling statistics"""
        return {
            'is_running': self.is_running,
            'events_fetched': self.events_fetched,
            'last_update': self.last_update,
            'resource_type': self.resource_type,
            'poll_interval': self.poll_interval,
            'batch_size': self.batch_size
        }
    
    def reset_tracking(self):
        """Reset polling tracker to fetch older events"""
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        self.last_update = one_hour_ago
        self._save_last_update(self.last_update)
        logger.info(f"Reset tracking to: {self.last_update}")


if __name__ == "__main__":
    # Test polling
    poller = FHIREventPoller(
        fhir_base_url='https://hapi.fhir.org/baseR4',
        poll_interval_seconds=10,
        batch_size=5,
        resource_type='AuditEvent'
    )
    
    def handle_event(event):
        print(f"\n📌 Got {event.get('resourceType')} event: {event.get('id')}")
        print(f"   Type: {event.get('type', {}).get('coding', [{}])[0].get('code', 'N/A')}")
    
    print("Starting FHIR Event Poller Demo...")
    print(f"FHIR Server: https://hapi.fhir.org/baseR4")
    print(f"Resource: AuditEvent")
    print("Press Ctrl+C to stop\n")
    
    poller.start_polling(callback=handle_event, daemon=False)
    
    try:
        while True:
            stats = poller.get_stats()
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Fetched: {stats['events_fetched']} events | "
                  f"Running: {stats['is_running']}", end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        poller.stop_polling()
