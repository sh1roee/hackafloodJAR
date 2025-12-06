"""
Test script for cheapest query feature
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_cheapest_query(question):
    """Test a cheapest query"""
    print(f"\n{'='*70}")
    print(f"🧪 Testing: {question}")
    print(f"{'='*70}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"question": question}
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            print("✅ Query Successful!")
            print(f"\n📋 Answer:\n{result.get('answer', '')}\n")
            print(f"🔧 Method: {result.get('method', 'unknown')}")
        else:
            print("❌ Query Failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TESTING CHEAPEST QUERY FEATURE")
    print("="*70)
    
    # Test 1: Pinakamurang bigas
    test_cheapest_query("pinakamurang bigas")
    
    # Test 2: Cheapest rice (English)
    test_cheapest_query("cheapest rice")
    
    # Test 3: Pinakamahal na bigas
    test_cheapest_query("pinakamahal na bigas")
    
    # Test 4: Pinakamurang gulay
    test_cheapest_query("pinakamurang gulay")
    
    # Test 5: Most expensive karne
    test_cheapest_query("pinakamahal na karne")
    
    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70 + "\n")
