#!/usr/bin/env python3
"""
Simple test to validate dashboard data files
"""
import json
import os

def test_dashboard_data():
    """Test that dashboard data files exist and are valid JSON"""
    dashboard_dir = "/Users/cchizinski2/Dev/wildlife-grad/dashboard"
    
    files_to_test = [
        "enhanced_data.json",
        "export_data.json"
    ]
    
    for filename in files_to_test:
        filepath = os.path.join(dashboard_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ {filename} does not exist")
            continue
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if filename == "enhanced_data.json":
                print(f"✅ {filename} - Total positions: {data.get('total_positions', 'Unknown')}")
                print(f"   - Disciplines: {data.get('overview', {}).get('total_disciplines', 'Unknown')}")
                print(f"   - Last updated: {data.get('last_updated', 'Unknown')}")
                
            elif filename == "export_data.json":
                print(f"✅ {filename} - Records: {len(data) if isinstance(data, list) else 'Unknown'}")
                
        except json.JSONDecodeError as e:
            print(f"❌ {filename} - Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ {filename} - Error: {e}")
    
    print("\n🌐 To view the dashboard:")
    print("1. Run: cd /Users/cchizinski2/Dev/wildlife-grad/dashboard")
    print("2. Run: python3 -m http.server 8080")
    print("3. Open: http://localhost:8080")

if __name__ == "__main__":
    test_dashboard_data()