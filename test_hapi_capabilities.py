"""Test HAPI server capabilities and subscription support"""
import requests
import json

url = 'https://hapi.fhir.org/baseR4/metadata'
headers = {'Accept': 'application/fhir+json'}

try:
    print("Checking HAPI Server Capabilities...\n")
    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()
    
    # Look for subscription information in capabilities
    rest = data.get('rest', [{}])[0]
    resources = rest.get('resource', [])
    
    print(f"Total available resources: {len(resources)}\n")
    
    # Look for Subscription resource
    sub_resource = [r for r in resources if r.get('type') == 'Subscription']
    if sub_resource:
        print("✓ Subscription Resource Found!")
        sub_info = sub_resource[0]
        print(f"  Supported Interactions: {[int_info.get('code') for int_info in sub_info.get('interaction', [])]}")
    else:
        print("✗ Subscription resource NOT in capabilities")
    
    print("\nAll available resources:")
    for r in sorted(resources, key=lambda x: x.get('type', '')):
        interactions = [i.get('code') for i in r.get('interaction', [])]
        print(f"  {r.get('type')}: {', '.join(interactions)}")
        
except Exception as e:
    print(f'Error: {e}')
