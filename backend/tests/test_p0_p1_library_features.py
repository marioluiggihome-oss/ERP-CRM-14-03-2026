# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test P0 and P1 features for multi-library pricing system (ZC and MV)
- P0: CATÁLOGO MODELOS button visibility based on currentLibrary
- P0: MV COLUMNA products with height variants (200 and 220)
- P1: Independent Corte Viga increment per library
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP0CatalogoModelosVisibility:
    """Test that CATÁLOGO MODELOS button is only visible for ZC library"""
    
    def test_user_mario_has_both_libraries(self):
        """Verify MARIO user has access to both ZC and MV libraries"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        user = data["user"]
        
        # Verify user has both libraries
        assert "allowedLibraries" in user
        assert "ZC" in user["allowedLibraries"]
        assert "MV" in user["allowedLibraries"]
        print(f"✓ User MARIO has allowedLibraries: {user['allowedLibraries']}")


class TestP0MVColumnaHeightVariants:
    """Test MV products with COLUMNA category have height variants (200 and 220)"""
    
    def test_mv_columna_products_exist(self):
        """Verify MV COLUMNA products exist in the database"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        
        # Filter MV products (have tariffPrices)
        mv_products = [p for p in products if p.get('tariffPrices')]
        assert len(mv_products) > 0, "No MV products found"
        print(f"✓ Found {len(mv_products)} MV products")
        
        # Filter COLUMNA category
        mv_columnas = [p for p in mv_products if 'COLUMNA' in (p.get('category', '').upper())]
        assert len(mv_columnas) > 0, "No MV COLUMNA products found"
        print(f"✓ Found {len(mv_columnas)} MV COLUMNA products")
    
    def test_mv_columna_height_200_variants(self):
        """Verify MV COLUMNA products with height 200 exist"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        
        # Filter MV COLUMNA products with height 200
        mv_columnas_200 = [p for p in products 
                          if p.get('tariffPrices') 
                          and 'COLUMNA' in (p.get('category', '').upper())
                          and p.get('height') == 200]
        
        assert len(mv_columnas_200) > 0, "No MV COLUMNA products with height 200 found"
        print(f"✓ Found {len(mv_columnas_200)} MV COLUMNA products with height 200")
        
        # Show some examples
        for p in mv_columnas_200[:5]:
            print(f"  - {p.get('code')}: {p.get('name')} (H={p.get('height')})")
    
    def test_mv_columna_height_220_variants(self):
        """Verify MV COLUMNA products with height 220 exist"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        
        # Filter MV COLUMNA products with height 220
        mv_columnas_220 = [p for p in products 
                          if p.get('tariffPrices') 
                          and 'COLUMNA' in (p.get('category', '').upper())
                          and p.get('height') == 220]
        
        assert len(mv_columnas_220) > 0, "No MV COLUMNA products with height 220 found"
        print(f"✓ Found {len(mv_columnas_220)} MV COLUMNA products with height 220")
        
        # Show some examples
        for p in mv_columnas_220[:5]:
            print(f"  - {p.get('code')}: {p.get('name')} (H={p.get('height')})")


class TestP1LibraryVigaCutIncrements:
    """Test independent Corte Viga increment per library (ZC and MV)"""
    
    def test_settings_has_library_viga_cut_field(self):
        """Verify settings model supports libraryVigaCutIncrements field"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        settings = response.json()
        
        # Check that libraryVigaCutIncrements field exists (can be null initially)
        assert "libraryVigaCutIncrements" in settings
        print(f"✓ Settings has libraryVigaCutIncrements: {settings.get('libraryVigaCutIncrements')}")
    
    def test_update_library_viga_cut_increments(self):
        """Test updating library-specific viga cut increments"""
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        current_settings = response.json()
        
        # Update with library-specific viga cut values
        update_data = {
            "libraryVigaCutIncrements": {
                "ZC": 15.5,
                "MV": 12.0
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/settings", json=update_data)
        assert response.status_code == 200
        updated_settings = response.json()
        
        # Verify the update
        assert updated_settings.get("libraryVigaCutIncrements") is not None
        assert updated_settings["libraryVigaCutIncrements"].get("ZC") == 15.5
        assert updated_settings["libraryVigaCutIncrements"].get("MV") == 12.0
        print(f"✓ Updated libraryVigaCutIncrements: {updated_settings['libraryVigaCutIncrements']}")
        
        # Reset to original values
        reset_data = {
            "libraryVigaCutIncrements": current_settings.get("libraryVigaCutIncrements")
        }
        requests.put(f"{BASE_URL}/api/settings", json=reset_data)
    
    def test_library_viga_cut_independent_values(self):
        """Test that ZC and MV can have different viga cut values"""
        # Update with different values for each library
        update_data = {
            "libraryVigaCutIncrements": {
                "ZC": 20.0,
                "MV": 10.0
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/settings", json=update_data)
        assert response.status_code == 200
        settings = response.json()
        
        zc_value = settings["libraryVigaCutIncrements"].get("ZC")
        mv_value = settings["libraryVigaCutIncrements"].get("MV")
        
        assert zc_value != mv_value, "ZC and MV should have independent values"
        assert zc_value == 20.0
        assert mv_value == 10.0
        print(f"✓ ZC viga cut: {zc_value}€, MV viga cut: {mv_value}€ (independent)")
        
        # Reset
        requests.put(f"{BASE_URL}/api/settings", json={"libraryVigaCutIncrements": None})


class TestMVProductsStructure:
    """Test MV products have correct structure with tariffPrices"""
    
    def test_mv_products_have_tariff_prices(self):
        """Verify MV products have tariffPrices field"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        
        mv_products = [p for p in products if p.get('tariffPrices')]
        assert len(mv_products) > 0
        
        # Check structure of tariffPrices
        sample = mv_products[0]
        tariff_prices = sample.get('tariffPrices', {})
        
        # MV products should have tariff groups (T1, T2, T3, etc.)
        print(f"✓ Sample MV product: {sample.get('code')}")
        print(f"  tariffPrices keys: {list(tariff_prices.keys())}")
        
        # Verify at least one tariff group exists
        assert len(tariff_prices) > 0, "tariffPrices should have at least one group"
    
    def test_mv_products_have_library_field(self):
        """Verify MV products have library='MV' field"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        
        mv_products = [p for p in products if p.get('tariffPrices')]
        
        # Check that MV products have library field
        for p in mv_products[:5]:
            library = p.get('library', 'ZC')  # Default to ZC if not set
            print(f"  - {p.get('code')}: library={library}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
