#!/usr/bin/env python3
"""Send a randomized FHIR AuditEvent to the local server's /fhir/notify endpoint.

Usage:
  python send_random_alert.py [--host HOST] [--count N]

Defaults: HOST=http://127.0.0.1:5000, count=1
"""
import argparse
import json
import random
import uuid
from datetime import datetime

try:
    import requests
except Exception:
    requests = None


def random_ip():
    return '.'.join(str(random.randint(1, 254)) for _ in range(4))


def make_audit_event():
    types = ['rest', 'notification', 'pipe', 'system']
    actions = ['C', 'R', 'U', 'D', 'E']
    outcomes = ['0', '4', '8']
    observers = ['sensor-1', 'edge-node', 'hapi-proxy', 'test-client']

    ev = {
        'id': str(uuid.uuid4()),
        'type': {'code': random.choice(types)},
        'action': random.choice(actions),
        'outcome': random.choice(outcomes),
        'recorded': datetime.utcnow().isoformat(),
        'source': {'observer': {'display': random.choice(observers)}},
        'agent': [
            {'network': {'address': random_ip()}}
        ]
    }
    return ev


def send_event(host, event):
    url = host.rstrip('/') + '/fhir/notify'
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(event)

    if requests is None:
        # fallback to urllib
        from urllib import request as _request
        req = _request.Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
        try:
            with _request.urlopen(req, timeout=10) as resp:
                return resp.status, resp.read().decode('utf-8')
        except Exception as e:
            return None, str(e)
    else:
        try:
            r = requests.post(url, json=event, headers=headers, timeout=10)
            return r.status_code, r.text
        except Exception as e:
            return None, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='http://127.0.0.1:5000', help='Base URL of server')
    p.add_argument('--count', type=int, default=1, help='Number of events to send')
    args = p.parse_args()

    for i in range(args.count):
        ev = make_audit_event()
        status, resp = send_event(args.host, ev)
        print(f'Event {i+1}: id={ev["id"]} -> status={status}\nResponse: {resp}\n')


if __name__ == '__main__':
    main()
