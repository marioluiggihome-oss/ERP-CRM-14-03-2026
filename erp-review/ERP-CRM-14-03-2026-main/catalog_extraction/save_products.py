import json
import os

def append_products(products_json, filename="/app/catalog_extraction/all_products.json"):
    """Append products to the JSON file"""
    try:
        # Load existing products
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing = json.load(f)
        else:
            existing = []
        
        # Parse new products
        if isinstance(products_json, str):
            new_products = json.loads(products_json)
        else:
            new_products = products_json
        
        # Add page info and append
        existing.extend(new_products)
        
        # Save back
        with open(filename, 'w') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        return len(new_products), len(existing)
    except Exception as e:
        return 0, str(e)

# Initialize file
if __name__ == "__main__":
    print("Products saver initialized")
