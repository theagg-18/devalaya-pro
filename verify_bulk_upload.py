
import os
import io
import csv
import sqlite3
from app import app
from database import get_db

def test_bulk_upload():
    print("Testing Bulk Upload Feature...")
    
    # Setup Context
    ctx = app.app_context()
    ctx.push()
    
    client = app.test_client()
    
    # 1. Test Template Download
    print("\n1. Testing Template Download...")
    res = client.get('/admin/items/template')
    if res.status_code == 200:
        content = res.data.decode('utf-8')
        print(f"   Success! Content Preview:\n{content.strip()}")
        if "Name,Amount,Type" in content:
            print("   INFO: Header format is correct.")
        else:
            print("   ERROR: Header format incorrect!")
    else:
        print(f"   ERROR: Failed to download template (Status: {res.status_code})")

    # 2. Test Partial Upload (Creation & Update)
    print("\n2. Testing Upload (Create & Update)...")
    
    # Determine initial state
    db = get_db()
    
    # Create a dummy existing item to update
    db.execute("INSERT OR IGNORE INTO puja_master (name, amount, type) VALUES ('Test_Existing', 10.0, 'puja')")
    db.commit()
    
    before_count = db.execute("SELECT count(*) FROM puja_master").fetchone()[0]
    print(f"   Items before upload: {before_count}")
    
    # Create CSV content
    # Row 1: Update 'Test_Existing' -> Amount 20, Type item
    # Row 2: Create 'Test_New_1' -> Amount 100, Type puja
    csv_content = """Name,Amount,Type
Test_Existing,20.0,item
Test_New_1,100.0,puja
"""
    
    data = {
        'upload_csv': (io.BytesIO(csv_content.encode('utf-8')), 'test_upload.csv')
    }
    
    # Use follow_redirects=True to see the flash messages in the response (if we were parsing HTML)
    # But for admin route, it redirects to /admin/items
    res = client.post('/admin/items', data=data, content_type='multipart/form-data', follow_redirects=True)
    
    if res.status_code == 200:
        print("   Upload POST successful (200 OK after redirect)")
        
        # Verify Database Changes
        new_count = db.execute("SELECT count(*) FROM puja_master").fetchone()[0]
        print(f"   Items after upload: {new_count} (Expected: {before_count + 1})")
        
        # Verify Update
        updated_item = db.execute("SELECT * FROM puja_master WHERE name='Test_Existing'").fetchone()
        if updated_item['amount'] == 20.0 and updated_item['type'] == 'item':
             print("   SUCCESS: Existing item updated correctly.")
        else:
             print(f"   FAILURE: Update failed! Got: {dict(updated_item)}")
             
        # Verify Creation
        new_item = db.execute("SELECT * FROM puja_master WHERE name='Test_New_1'").fetchone()
        if new_item and new_item['amount'] == 100.0:
            print("   SUCCESS: New item created correctly.")
        else:
            print("   FAILURE: Creation failed!")
            
    else:
        print(f"   ERROR: Upload POST failed (Status: {res.status_code})")

    # Cleanup
    print("\nCleaning up test data...")
    db.execute("DELETE FROM puja_master WHERE name IN ('Test_Existing', 'Test_New_1')")
    db.commit()
    print("Done.")

if __name__ == "__main__":
    test_bulk_upload()
