import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_sync():
    print("Testing Sync...")
    response = requests.post(f"{BASE_URL}/sync-drive")
    print(response.json())
    
    # Wait for sync to complete (for testing, we just check status)
    while True:
        status = requests.get(f"{BASE_URL}/status").json()
        print(f"Status: {status}")
        if status['indexed_chunks'] > 0:
            print("Sync complete!")
            break
        time.sleep(5)

def test_ask(query):
    print(f"Testing Query: {query}")
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"query": query}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data['answer']}")
        print(f"Sources: {data['sources']}")
    else:
        print(f"Error: {response.json()}")

if __name__ == "__main__":
    # Note: This requires the server to be running and credentials to be set up.
    # test_sync()
    # test_ask("What is our refund policy?")
    print("Run api.main first, then use this script to test.")
