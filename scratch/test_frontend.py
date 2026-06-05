import os
import sys
from playwright.sync_api import sync_playwright

def test_ui():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to frontend
        print("Navigating to http://localhost:8000/...")
        page.goto("http://localhost:8000/")
        
        # Wait for page to load campaigns
        page.wait_for_timeout(3000)
        
        # Take screenshot of initial state
        page.screenshot(path="scratch/initial_ui.png")
        print("Captured initial UI screenshot to scratch/initial_ui.png")
        
        # Find testTime input for campaign 10
        time_input_selector = "#testTime_10"
        
        # Check current value
        current_val = page.locator(time_input_selector).input_value()
        print(f"Current testTime value for Campaign 10: '{current_val}'")
        
        # Type "10" in the time input
        print("Focusing and typing '10' in the time input...")
        page.locator(time_input_selector).fill("")
        page.locator(time_input_selector).type("10")
        
        # Blur the input (click somewhere else, e.g. the body or another input)
        print("Blurring the input...")
        page.click("body")
        page.wait_for_timeout(1000)
        
        # Check value after blur
        val_after_blur = page.locator(time_input_selector).input_value()
        print(f"Value after blur: '{val_after_blur}'")
        
        # Type "10:30"
        print("Typing '10:30'...")
        page.locator(time_input_selector).fill("")
        page.locator(time_input_selector).type("1030")
        page.click("body")
        page.wait_for_timeout(1000)
        val_2 = page.locator(time_input_selector).input_value()
        print(f"Value after typing '1030' and blur: '{val_2}'")
        
        # Check if the database has been updated
        import sqlite3
        conn = sqlite3.connect('tigerone.db')
        cursor = conn.cursor()
        cursor.execute("SELECT test_time FROM campaigns WHERE id = 10")
        db_val = cursor.fetchone()[0]
        conn.close()
        print(f"Value in database for campaign 10 test_time: '{db_val}'")
        
        browser.close()

if __name__ == "__main__":
    test_ui()
