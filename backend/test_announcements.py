"""
Test script for Announcements CRUD operations.

This script tests all announcement endpoints to identify any bugs.
"""
import requests
import json
from datetime import date, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"  # Change to your admin username
PASSWORD = "admin"  # Change to your admin password

def login():
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_list_announcements(token):
    """Test listing announcements."""
    print("\n=== Testing LIST Announcements ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test without show_all
    response = requests.get(f"{BASE_URL}/announcements/", headers=headers)
    print(f"GET /announcements/ (active only): {response.status_code}")
    if response.status_code == 200:
        print(f"  Found {len(response.json())} active announcements")
    else:
        print(f"  Error: {response.text}")
    
    # Test with show_all
    response = requests.get(f"{BASE_URL}/announcements/?show_all=true", headers=headers)
    print(f"GET /announcements/?show_all=true: {response.status_code}")
    if response.status_code == 200:
        announcements = response.json()
        print(f"  Found {len(announcements)} total announcements")
        if announcements:
            print(f"  Sample announcement: {json.dumps(announcements[0], indent=2, default=str)}")
    else:
        print(f"  Error: {response.text}")
    
    return response.json() if response.status_code == 200 else []

def test_create_announcement(token):
    """Test creating an announcement."""
    print("\n=== Testing CREATE Announcement ===")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "title": "Test Announcement",
        "message": "This is a test announcement created by the test script.",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=7))
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/announcements/", headers=headers, json=payload)
    print(f"POST /announcements/: {response.status_code}")
    
    if response.status_code == 200:
        announcement = response.json()
        print(f"  Created announcement ID: {announcement['id']}")
        print(f"  Response: {json.dumps(announcement, indent=2, default=str)}")
        return announcement
    else:
        print(f"  Error: {response.text}")
        return None

def test_get_announcement(token, announcement_id):
    """Test getting a single announcement."""
    print(f"\n=== Testing GET Announcement ID={announcement_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/announcements/{announcement_id}", headers=headers)
    print(f"GET /announcements/{announcement_id}: {response.status_code}")
    
    if response.status_code == 200:
        announcement = response.json()
        print(f"  Response: {json.dumps(announcement, indent=2, default=str)}")
        return announcement
    else:
        print(f"  Error: {response.text}")
        return None

def test_update_announcement(token, announcement_id):
    """Test updating an announcement."""
    print(f"\n=== Testing UPDATE Announcement ID={announcement_id} ===")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "title": "Updated Test Announcement",
        "message": "This announcement has been updated by the test script.",
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.put(f"{BASE_URL}/announcements/{announcement_id}", headers=headers, json=payload)
    print(f"PUT /announcements/{announcement_id}: {response.status_code}")
    
    if response.status_code == 200:
        announcement = response.json()
        print(f"  Response: {json.dumps(announcement, indent=2, default=str)}")
        return announcement
    else:
        print(f"  Error: {response.text}")
        return None

def test_delete_announcement(token, announcement_id):
    """Test deleting an announcement."""
    print(f"\n=== Testing DELETE Announcement ID={announcement_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(f"{BASE_URL}/announcements/{announcement_id}", headers=headers)
    print(f"DELETE /announcements/{announcement_id}: {response.status_code}")
    
    if response.status_code == 200:
        announcement = response.json()
        print(f"  Deleted (soft delete): is_active={announcement.get('is_active')}")
        print(f"  Response: {json.dumps(announcement, indent=2, default=str)}")
        return announcement
    else:
        print(f"  Error: {response.text}")
        return None

def main():
    """Run all tests."""
    print("=" * 60)
    print("Announcements CRUD Test Script")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n❌ Login failed. Cannot proceed with tests.")
        return
    
    print(f"\n✅ Login successful. Token: {token[:20]}...")
    
    # Test LIST
    existing_announcements = test_list_announcements(token)
    
    # Test CREATE
    new_announcement = test_create_announcement(token)
    if not new_announcement:
        print("\n❌ Create failed. Stopping tests.")
        return
    
    announcement_id = new_announcement['id']
    
    # Test GET
    test_get_announcement(token, announcement_id)
    
    # Test UPDATE
    test_update_announcement(token, announcement_id)
    
    # Test DELETE
    test_delete_announcement(token, announcement_id)
    
    # Verify deletion
    print("\n=== Verifying Soft Delete ===")
    deleted = test_get_announcement(token, announcement_id)
    if deleted and not deleted.get('is_active'):
        print("✅ Soft delete verified: announcement is inactive")
    
    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
