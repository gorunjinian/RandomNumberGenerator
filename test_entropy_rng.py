#!/usr/bin/env python3
"""
Test script for entropy RNG - generates 5 random numbers and exits
"""

import time
from entropy_rng import EntropyRNG

def test_rng():
    print("Testing Entropy-based Random Number Generator")
    print("=" * 50)
    
    rng = EntropyRNG()
    
    try:
        # Start entropy collection
        print("Starting entropy collection...")
        rng.start_entropy_collection()
        
        print("Collecting entropy from CPU scheduler...")
        print("(Note: Mouse movement would add more entropy)")
        
        # Wait for sufficient entropy
        while True:
            status = rng.get_entropy_status()
            total_samples = status['total_samples']
            
            print(f"Entropy samples: {total_samples}")
            
            if total_samples >= 50:
                print("Sufficient entropy collected!")
                break
            
            time.sleep(0.5)
        
        # Generate test numbers
        print("\nGenerating 5 test random numbers:")
        print("-" * 30)
        
        for i in range(5):
            random_num = rng.generate_random_number()
            print(f"Random number {i+1}: {random_num}")
        
        print("\nTest completed successfully!")
        
    finally:
        rng.stop_entropy_collection()

if __name__ == "__main__":
    test_rng()