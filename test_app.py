#!/usr/bin/env python3
"""
Test script for Kartoshka Youtuber
Tests the backend functionality
Created by NaderB - https://www.naderb.org
"""

import subprocess
import json
import sys
import os

def test_backend():
    """Test the backend application"""
    print("Testing backend application...")
    
    # Test video info command
    print("1. Testing video info command...")
    try:
        cmd = [
            sys.executable, "backend.py",
            "--command", "info",
            "--url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            if 'error' in info:
                print(f"   [ERROR] Error: {info['error']}")
                return False
            else:
                print(f"   [SUCCESS] Video title: {info.get('title', 'Unknown')}")
                print(f"   [SUCCESS] Duration: {info.get('duration', 0)} seconds")
                print(f"   [SUCCESS] Formats available: {len(info.get('formats', []))}")
        else:
            print(f"   [ERROR] Backend returned error code: {result.returncode}")
            print(f"   Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   [ERROR] Backend timed out")
        return False
    except Exception as e:
        print(f"   [ERROR] Error testing backend: {e}")
        return False
    
    print("2. Testing invalid URL...")
    try:
        cmd = [
            sys.executable, "backend.py",
            "--command", "info",
            "--url", "https://invalid-url.com"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print("   [SUCCESS] Correctly handled invalid URL")
        else:
            info = json.loads(result.stdout)
            if 'error' in info:
                print("   [SUCCESS] Correctly returned error for invalid URL")
            else:
                print("   [ERROR] Should have returned error for invalid URL")
                return False
                
    except Exception as e:
        print(f"   [ERROR] Error testing invalid URL: {e}")
        return False
    
    print("[SUCCESS] Backend tests passed!")
    return True

def test_gui_import():
    """Test if GUI can be imported"""
    print("Testing GUI import...")
    
    try:
        import tkinter
        print("   [SUCCESS] tkinter available")
        
        # Try to import our GUI module
        import gui
        print("   [SUCCESS] GUI module imported successfully")
        
        return True
    except ImportError as e:
        print(f"   [ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] Error importing GUI: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Testing Kartoshka Youtuber")
    print("=" * 50)
    print()
    
    # Check if files exist
    if not os.path.exists("backend.py"):
        print("[ERROR] backend.py not found!")
        return False
    
    if not os.path.exists("gui.py"):
        print("[ERROR] gui.py not found!")
        return False
    
    print("[SUCCESS] All required files found")
    print()
    
    # Test backend
    if not test_backend():
        print("[ERROR] Backend tests failed!")
        return False
    
    print()
    
    # Test GUI import
    if not test_gui_import():
        print("[ERROR] GUI import tests failed!")
        return False
    
    print()
    print("[SUCCESS] All tests passed!")
    print("   The application is ready to build and use.")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



