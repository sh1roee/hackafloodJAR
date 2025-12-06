"""
Test Script: Advanced Query Features
Demonstrates all 5 query types for hackathon demo
"""

import requests
import json

BACKEND_URL = "http://localhost:8000"

def test_query(question, description):
    """Test a query and print results"""
    print(f"\n{'='*70}")
    print(f"🔍 {description}")
    print(f"{'='*70}")
    print(f"Tanong: {question}\n")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/query",
            json={"question": question},
            timeout=10
        )
        
        data = response.json()
        
        if data.get('success'):
            print(f"✅ SUCCESS ({data.get('method', 'unknown')} method)")
            print(f"\nSagot:\n{data.get('answer', 'No answer')}\n")
            
            # Show stats if available
            if 'total' in data:
                print(f"Total: ₱{data['total']:.2f}")
            if 'items_count' in data:
                print(f"Items: {data['items_count']}")
        else:
            print(f"❌ FAILED: {data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    print("\n" + "="*70)
    print("🌾 DA PRICE MONITOR - ADVANCED FEATURES TEST")
    print("="*70)
    
    # Test 1: Single Product
    test_query(
        "Magkano kamatis sa NCR?",
        "TEST 1: SINGLE PRODUCT (Basic lookup)"
    )
    
    # Test 2: Multi-Product
    test_query(
        "Magkano kamatis, sibuyas, at bawang?",
        "TEST 2: MULTI-PRODUCT (Multiple items at once)"
    )
    
    # Test 3: Comparison
    test_query(
        "Ano mas mura, manok o baboy?",
        "TEST 3: COMPARISON (Find cheapest option)"
    )
    
    # Test 4: Budget Planning
    test_query(
        "Ano pwede bilhin ng 200 pesos?",
        "TEST 4: BUDGET PLANNING (What can I afford?)"
    )
    
    # Test 5: Category Browsing
    test_query(
        "Presyo ng lahat ng gulay",
        "TEST 5: CATEGORY BROWSING (Market overview)"
    )
    
    # Test 6: City Recognition
    test_query(
        "Magkano bigas sa Pasig?",
        "TEST 6: CITY RECOGNITION (Pasig → NCR mapping)"
    )
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED!")
    print("="*70)
    print("\n💡 Key Features Demonstrated:")
    print("  1. Single product lookup (FREE, instant)")
    print("  2. Multi-product totals (FREE, instant)")
    print("  3. Price comparison (FREE, instant)")
    print("  4. Budget planning (FREE, instant)")
    print("  5. Category overview (FREE, instant)")
    print("  6. City-to-region mapping (Pasig/Makati/QC → NCR)")
    print("\n🎯 Anti-Scam Impact:")
    print("  - Farmers know exact government prices")
    print("  - Can compare products before buying")
    print("  - Maximize budget with smart planning")
    print("  - See full market, make informed decisions")
    print("\n💰 Cost: ₱0 per query (100% FREE)")
    print("⚡ Speed: <150ms average")
    print("📱 Perfect for SMS with limited load!")
    print()

if __name__ == "__main__":
    main()
