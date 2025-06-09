#!/usr/bin/env python3
"""
Simple health check script for Docker container
"""
import sys
import urllib.request
import urllib.error

def health_check():
    try:
        # Try to connect to the health endpoint
        response = urllib.request.urlopen('http://localhost:8000/healthz/', timeout=5)
        if response.getcode() == 200:
            print("Health check passed")
            return 0
        else:
            print(f"Health check failed with status code: {response.getcode()}")
            return 1
    except urllib.error.URLError as e:
        print(f"Health check failed: {e}")
        return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
