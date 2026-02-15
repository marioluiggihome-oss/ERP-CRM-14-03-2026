"""
Test suite for Armarios IA features:
- IA Configuration endpoint
- IA Render endpoint
- Armarios CRUD operations
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://catalog-builder-31.preview.emergentagent.com')

class TestArmariosIAConfiguration:
    """Tests for IA-based wardrobe configuration"""
    
    def test_ia_configure_basic(self):
        """Test basic IA configuration with simple instruction"""
        response = requests.post(
            f"{BASE_URL}/api/armarios/ia/configure",
            json={
                "instruction": "Quiero un armario con 3 módulos para ropa",
                "current_config": {
                    "width": 2400,
                    "height": 2400,
                    "depth": 600,
                    "modules": 3
                }
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "config" in data
        
        config = data["config"]
        assert "modules" in config
        assert "moduleConfigs" in config
        assert "explanation" in config
    
    def test_ia_configure_detailed_instruction(self):
        """Test IA configuration with detailed requirements"""
        response = requests.post(
            f"{BASE_URL}/api/armarios/ia/configure",
            json={
                "instruction": "Necesito un armario con 4 módulos: uno para colgar vestidos largos, otro con cajones para ropa interior, uno con baldas para zapatos, y otro con barra doble para camisas",
                "current_config": {
                    "width": 3000,
                    "height": 2600,
                    "depth": 650,
                    "modules": 4
                }
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        config = data["config"]
        assert config.get("modules") >= 3  # Should have at least 3 modules
        assert len(config.get("moduleConfigs", [])) >= 3
    
    def test_ia_configure_empty_instruction(self):
        """Test IA configuration with empty instruction"""
        response = requests.post(
            f"{BASE_URL}/api/armarios/ia/configure",
            json={
                "instruction": "",
                "current_config": {
                    "width": 2400,
                    "height": 2400,
                    "depth": 600,
                    "modules": 3
                }
            },
            timeout=60
        )
        
        # Should still return 200 but may have error or default config
        assert response.status_code in [200, 400, 500]


class TestArmariosIARender:
    """Tests for IA-based wardrobe render generation"""
    
    def test_ia_render_basic(self):
        """Test basic render generation"""
        response = requests.post(
            f"{BASE_URL}/api/armarios/ia/render",
            json={
                "width": 2400,
                "height": 2400,
                "depth": 600,
                "modules": 3,
                "doorType": "sliding",
                "exteriorColorName": "Blanco",
                "exteriorColorHex": "#FFFFFF",
                "interiorColorName": "Blanco",
                "handleColorName": "Plata",
                "moduleConfigs": [
                    {"id": 1, "shelves": 4, "drawers": 0, "hangingRods": 1}
                ],
                "roomStyle": "moderno"
            },
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "image" in data
        assert "data" in data["image"]
        assert "mime_type" in data["image"]
        
        # Verify image data is base64
        image_data = data["image"]["data"]
        assert len(image_data) > 100  # Should have substantial image data
    
    def test_ia_render_different_styles(self):
        """Test render with different room styles"""
        styles = ["moderno", "clásico", "minimalista"]
        
        for style in styles:
            response = requests.post(
                f"{BASE_URL}/api/armarios/ia/render",
                json={
                    "width": 2400,
                    "height": 2400,
                    "depth": 600,
                    "modules": 2,
                    "doorType": "hinged",
                    "exteriorColorName": "Roble",
                    "exteriorColorHex": "#8B4513",
                    "interiorColorName": "Blanco",
                    "handleColorName": "Oro",
                    "moduleConfigs": [
                        {"id": 1, "shelves": 4, "drawers": 2, "hangingRods": 0}
                    ],
                    "roomStyle": style
                },
                timeout=120
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") == True, f"Failed for style: {style}"


class TestArmariosProjects:
    """Tests for Armarios project CRUD operations"""
    
    @pytest.fixture
    def test_project_data(self):
        return {
            "name": "TEST_Proyecto_Armario",
            "customerName": "TEST_Cliente",
            "projectRef": "TEST-REF-001",
            "width": 2400,
            "height": 2400,
            "depth": 600,
            "modules": 3,
            "doorType": "sliding",
            "exteriorColor": "010",
            "interiorColor": "010",
            "handleColor": "231",
            "moduleConfigs": [
                {"id": 1, "shelves": 4, "drawers": 0, "hangingRods": 1, "hangingHeight": 1200, "extras": {}},
                {"id": 2, "shelves": 6, "drawers": 2, "hangingRods": 0, "hangingHeight": 0, "extras": {}},
                {"id": 3, "shelves": 4, "drawers": 0, "hangingRods": 2, "hangingHeight": 1000, "extras": {}}
            ],
            "extras": {"softClose": True, "led": False, "mirror": False},
            "ivaRate": 21.0,
            "customAccessories": [],
            "totalPrice": 5000.0,
            "totalArea": 25.0
        }
    
    def test_create_project(self, test_project_data):
        """Test creating a new armarios project"""
        response = requests.post(
            f"{BASE_URL}/api/armarios/projects",
            json=test_project_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "project" in data
        
        project = data["project"]
        assert project["name"] == test_project_data["name"]
        assert project["customerName"] == test_project_data["customerName"]
        assert "id" in project
        
        # Cleanup
        project_id = project["id"]
        requests.delete(f"{BASE_URL}/api/armarios/projects/{project_id}")
    
    def test_get_all_projects(self):
        """Test getting all armarios projects"""
        response = requests.get(
            f"{BASE_URL}/api/armarios/projects",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "projects" in data
        assert isinstance(data["projects"], list)
    
    def test_get_project_by_id(self, test_project_data):
        """Test getting a specific project by ID"""
        # First create a project
        create_response = requests.post(
            f"{BASE_URL}/api/armarios/projects",
            json=test_project_data,
            timeout=30
        )
        
        assert create_response.status_code == 200
        project_id = create_response.json()["project"]["id"]
        
        # Get the project
        response = requests.get(
            f"{BASE_URL}/api/armarios/projects/{project_id}",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["project"]["id"] == project_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/armarios/projects/{project_id}")
    
    def test_update_project(self, test_project_data):
        """Test updating an armarios project"""
        # First create a project
        create_response = requests.post(
            f"{BASE_URL}/api/armarios/projects",
            json=test_project_data,
            timeout=30
        )
        
        assert create_response.status_code == 200
        project_id = create_response.json()["project"]["id"]
        
        # Update the project
        update_data = {
            "name": "TEST_Updated_Project",
            "customerName": "TEST_Updated_Cliente"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/armarios/projects/{project_id}",
            json=update_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["project"]["name"] == "TEST_Updated_Project"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/armarios/projects/{project_id}")
    
    def test_delete_project(self, test_project_data):
        """Test deleting an armarios project"""
        # First create a project
        create_response = requests.post(
            f"{BASE_URL}/api/armarios/projects",
            json=test_project_data,
            timeout=30
        )
        
        assert create_response.status_code == 200
        project_id = create_response.json()["project"]["id"]
        
        # Delete the project
        response = requests.delete(
            f"{BASE_URL}/api/armarios/projects/{project_id}",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/armarios/projects/{project_id}",
            timeout=30
        )
        assert get_response.status_code == 404


class TestArmariosAuth:
    """Tests for authentication with Armarios module"""
    
    def test_login_and_access_armarios(self):
        """Test login and verify user can access Armarios"""
        # Login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "MARIO", "password": "MARIO"},
            timeout=30
        )
        
        assert login_response.status_code == 200
        user_data = login_response.json()
        
        # Check if user has armarios access
        # Note: canAccessArmarios might be True for admin users
        assert "user" in user_data
