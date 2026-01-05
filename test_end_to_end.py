#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests the complete system flow
"""

import requests
import time

API_BASE = "http://localhost:8000"

def test_system():
    print("🧪 Running End-to-End Integration Test\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health Check
    print("1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        assert response.status_code == 200
        print("   ✅ Health check passed")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        tests_failed += 1
    
    # Test 2: Agent Status
    print("\n2️⃣ Testing agent status...")
    try:
        response = requests.get(f"{API_BASE}/agent/status")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Agent status: {data['agent']['is_running']}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Agent status failed: {e}")
        tests_failed += 1
    
    # Test 3: Queue Status
    print("\n3️⃣ Testing queue status...")
    try:
        response = requests.get(f"{API_BASE}/queue/status")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Queue: {data['by_status']}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Queue status failed: {e}")
        tests_failed += 1
    
    # Test 4: Analytics
    print("\n4️⃣ Testing analytics...")
    try:
        response = requests.get(f"{API_BASE}/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Analytics: {data['overview']}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Analytics failed: {e}")
        tests_failed += 1
    
    # Test 5: Full Health Check
    print("\n5️⃣ Testing full health check...")
    try:
        response = requests.get(f"{API_BASE}/health/full")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ System status: {data['status']}")
        for service, status in data['checks'].items():
            if isinstance(status, dict) and 'status' in status:
                icon = "✅" if status['status'] == 'healthy' else "❌"
                print(f"      {icon} {service}: {status['message']}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Full health check failed: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
    print("="*60)
    
    if tests_failed == 0:
        print("🎉 ALL TESTS PASSED! System is ready for production!")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix.")
        return False

if __name__ == "__main__":
    success = test_system()
    exit(0 if success else 1)