"""
Test suite for Prescriptor Calendar Notes CRUD API
Tests: GET, POST, PUT, DELETE /api/prescriptor/notes
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
PRESCRIPTOR_ID = "user-862c0854"  # PRESCRIPTOR1 user
PRESCRIPTOR_NAME = "Juan García - Prescriptor"
TEST_DATE = "2026-01-15"


class TestPrescriptorNotesAPI:
    """Test Prescriptor Calendar Notes CRUD operations"""
    
    created_note_id = None
    
    def test_01_get_prescriptor_notes_empty(self):
        """Test GET prescriptor notes for a date range with no notes"""
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes",
            params={
                "prescriptor_id": PRESCRIPTOR_ID,
                "start": "2026-02-01",
                "end": "2026-02-28"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET prescriptor notes (empty range) - Status: {response.status_code}, Count: {len(data)}")
    
    def test_02_get_all_prescriptor_notes_admin(self):
        """Test GET all prescriptor notes (admin endpoint)"""
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes/all",
            params={
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # Should have at least the seed note from 2026-01-28
        print(f"✓ GET all prescriptor notes (admin) - Status: {response.status_code}, Count: {len(data)}")
        
        # Verify seed note exists
        seed_notes = [n for n in data if n.get("title") == "Cita con Promotor Madrid"]
        if seed_notes:
            print(f"  ✓ Found seed note: '{seed_notes[0]['title']}' on {seed_notes[0]['date']}")
    
    def test_03_create_prescriptor_note(self):
        """Test POST create a new prescriptor note"""
        note_data = {
            "title": f"TEST_Note_{uuid.uuid4().hex[:6]}",
            "content": "Test note content for automated testing",
            "date": TEST_DATE,
            "prescriptorId": PRESCRIPTOR_ID,
            "prescriptorName": PRESCRIPTOR_NAME
        }
        
        response = requests.post(
            f"{BASE_URL}/api/prescriptor/notes",
            json=note_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["title"] == note_data["title"], "Title should match"
        assert data["content"] == note_data["content"], "Content should match"
        assert data["date"] == note_data["date"], "Date should match"
        assert data["prescriptorId"] == PRESCRIPTOR_ID, "PrescriptorId should match"
        
        # Store for later tests
        TestPrescriptorNotesAPI.created_note_id = data["id"]
        print(f"✓ POST create note - Status: {response.status_code}, ID: {data['id']}")
        print(f"  Title: {data['title']}, Date: {data['date']}")
    
    def test_04_verify_note_created_via_get(self):
        """Test GET to verify the created note exists"""
        assert TestPrescriptorNotesAPI.created_note_id, "Note ID should be set from previous test"
        
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes",
            params={
                "prescriptor_id": PRESCRIPTOR_ID,
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        created_notes = [n for n in data if n.get("id") == TestPrescriptorNotesAPI.created_note_id]
        assert len(created_notes) == 1, f"Should find exactly 1 created note, found {len(created_notes)}"
        
        note = created_notes[0]
        assert note["date"] == TEST_DATE, "Date should match"
        print(f"✓ GET verify created note - Found note ID: {note['id']}")
    
    def test_05_update_prescriptor_note(self):
        """Test PUT update an existing prescriptor note"""
        assert TestPrescriptorNotesAPI.created_note_id, "Note ID should be set from previous test"
        
        update_data = {
            "title": "TEST_Updated_Note_Title",
            "content": "Updated content for testing"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/prescriptor/notes/{TestPrescriptorNotesAPI.created_note_id}",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["title"] == update_data["title"], "Title should be updated"
        assert data["content"] == update_data["content"], "Content should be updated"
        print(f"✓ PUT update note - Status: {response.status_code}")
        print(f"  Updated title: {data['title']}")
    
    def test_06_verify_note_updated_via_get(self):
        """Test GET to verify the note was updated"""
        assert TestPrescriptorNotesAPI.created_note_id, "Note ID should be set"
        
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes",
            params={
                "prescriptor_id": PRESCRIPTOR_ID,
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        updated_notes = [n for n in data if n.get("id") == TestPrescriptorNotesAPI.created_note_id]
        assert len(updated_notes) == 1, "Should find the updated note"
        
        note = updated_notes[0]
        assert note["title"] == "TEST_Updated_Note_Title", "Title should be updated"
        print(f"✓ GET verify updated note - Title: {note['title']}")
    
    def test_07_delete_prescriptor_note(self):
        """Test DELETE a prescriptor note"""
        assert TestPrescriptorNotesAPI.created_note_id, "Note ID should be set"
        
        response = requests.delete(
            f"{BASE_URL}/api/prescriptor/notes/{TestPrescriptorNotesAPI.created_note_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"✓ DELETE note - Status: {response.status_code}, Message: {data.get('message')}")
    
    def test_08_verify_note_deleted_via_get(self):
        """Test GET to verify the note was deleted"""
        assert TestPrescriptorNotesAPI.created_note_id, "Note ID should be set"
        
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes",
            params={
                "prescriptor_id": PRESCRIPTOR_ID,
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        deleted_notes = [n for n in data if n.get("id") == TestPrescriptorNotesAPI.created_note_id]
        assert len(deleted_notes) == 0, "Deleted note should not be found"
        print(f"✓ GET verify deleted note - Note no longer exists")
    
    def test_09_delete_nonexistent_note(self):
        """Test DELETE a non-existent note returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/prescriptor/notes/nonexistent-note-id"
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ DELETE non-existent note - Status: {response.status_code} (expected 404)")
    
    def test_10_update_nonexistent_note(self):
        """Test PUT update a non-existent note returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/prescriptor/notes/nonexistent-note-id",
            json={"title": "Test", "content": "Test"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ PUT non-existent note - Status: {response.status_code} (expected 404)")


class TestPrescriptorNotesValidation:
    """Test validation and edge cases for prescriptor notes"""
    
    def test_create_note_empty_title_and_content(self):
        """Test creating note with empty title and content should fail or be handled"""
        note_data = {
            "title": "",
            "content": "",
            "date": TEST_DATE,
            "prescriptorId": PRESCRIPTOR_ID,
            "prescriptorName": PRESCRIPTOR_NAME
        }
        
        response = requests.post(
            f"{BASE_URL}/api/prescriptor/notes",
            json=note_data
        )
        # The API might accept empty notes or reject them - document behavior
        print(f"✓ POST empty note - Status: {response.status_code}")
        if response.status_code == 200:
            # Clean up if created
            data = response.json()
            if data.get("id"):
                requests.delete(f"{BASE_URL}/api/prescriptor/notes/{data['id']}")
                print(f"  Note created with empty fields, cleaned up")
    
    def test_get_notes_missing_params(self):
        """Test GET notes with missing required parameters"""
        # Missing prescriptor_id
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes",
            params={
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        # Should return 422 for missing required param or handle gracefully
        print(f"✓ GET notes missing prescriptor_id - Status: {response.status_code}")


class TestAdminPrescriptorNotesView:
    """Test admin view of all prescriptor notes"""
    
    def test_admin_sees_all_prescriptor_notes(self):
        """Test that admin endpoint returns notes from all prescriptors"""
        response = requests.get(
            f"{BASE_URL}/api/prescriptor/notes/all",
            params={
                "start": "2026-01-01",
                "end": "2026-01-31"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Admin GET all notes - Status: {response.status_code}, Total: {len(data)}")
        
        # Check that notes have prescriptor info
        for note in data:
            assert "prescriptorId" in note, "Note should have prescriptorId"
            assert "prescriptorName" in note, "Note should have prescriptorName"
            print(f"  - {note.get('date')}: {note.get('title')} (by {note.get('prescriptorName')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
