"""
Test half-point normalization logic used in sport extractors.
"""


def normalize_to_half_point(value: float) -> float:
    """
    Normalize spread/total to nearest half-point increment (e.g., 5.5, 6.0, 6.5).
    This ensures alignment across bookmakers for fair odds calculation.
    """
    if value == 0:
        return 0.0
    # Round to nearest 0.5, always rounding 0.25 up to 0.5 and 0.75 up to 1.0
    import math
    return math.floor(value * 2 + 0.5) / 2


def test_normalization():
    """Test various normalization cases."""
    test_cases = [
        (5.25, 5.5),
        (5.75, 6.0),
        (6.0, 6.0),
        (6.3, 6.5),
        (6.7, 6.5),   # Closer to 6.5 than 7.0
        (7.8, 8.0),
        (10.1, 10.0),
        (10.4, 10.5),
        (-3.2, -3.0),
        (-3.6, -3.5),
        (0.0, 0.0),
        (0.3, 0.5),
        (5.0, 5.0),
        (5.1, 5.0),
        (5.2, 5.0),
        (5.24, 5.0),
        (5.26, 5.5),
        (5.5, 5.5),
        (5.74, 5.5),
        (5.76, 6.0),
    ]
    
    print("Testing half-point normalization...")
    print("=" * 50)
    
    all_passed = True
    for input_val, expected in test_cases:
        result = normalize_to_half_point(input_val)
        passed = result == expected
        status = "✓" if passed else "✗"
        
        print(f"{status} {input_val:6.2f} → {result:6.2f} (expected {expected:6.2f})")
        
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("✅ All normalization tests passed!")
        return True
    else:
        print("❌ Some normalization tests failed!")
        return False


def test_alignment():
    """Test that similar values align to the same half-point."""
    print("\nTesting alignment (similar values should normalize to same point)...")
    print("=" * 50)
    
    # Test groups that should normalize to the same value
    groups = [
        ([5.0, 5.1, 5.2, 5.24], 5.0),
        ([5.25, 5.3, 5.4, 5.49], 5.5),
        ([5.5, 5.6, 5.7, 5.74], 5.5),
        ([5.75, 5.8, 5.9, 5.99], 6.0),
        ([6.0, 6.1, 6.2, 6.24], 6.0),
    ]
    
    all_passed = True
    for values, expected in groups:
        results = [normalize_to_half_point(v) for v in values]
        all_same = all(r == expected for r in results)
        status = "✓" if all_same else "✗"
        
        print(f"{status} {values} → {results[0]:.1f} (expected {expected:.1f})")
        
        if not all_same:
            all_passed = False
            print(f"   ERROR: Got {results}")
    
    print("=" * 50)
    if all_passed:
        print("✅ All alignment tests passed!")
        return True
    else:
        print("❌ Some alignment tests failed!")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("HALF-POINT NORMALIZATION TESTS")
    print("=" * 50 + "\n")
    
    test1 = test_normalization()
    test2 = test_alignment()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
