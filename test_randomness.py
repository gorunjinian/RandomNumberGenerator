#!/usr/bin/env python3
"""
Statistical tests for randomness quality of our entropy RNG
Tests various statistical properties to validate randomness
"""

import statistics
from collections import Counter
import math
from entropy_rng_gui import EntropyRNG

class RandomnessTests:
    def __init__(self, numbers):
        self.numbers = numbers
        self.n = len(numbers)
        
    def frequency_test(self):
        """Test if all numbers appear with roughly equal frequency"""
        expected_freq = self.n / 2048  # Expected frequency for uniform distribution
        counts = Counter(self.numbers)
        
        # Chi-square test
        chi_square = 0
        for i in range(2048):
            observed = counts.get(i, 0)
            chi_square += ((observed - expected_freq) ** 2) / expected_freq
        
        # Critical value for alpha=0.05, df=2047 is approximately 2107
        p_value = 1.0 if chi_square < 2107 else 0.0
        return {
            'test': 'Frequency Test',
            'chi_square': chi_square,
            'critical_value': 2107,
            'passed': chi_square < 2107,
            'p_value': f"~{p_value}"
        }
    
    def runs_test(self):
        """Test for runs (consecutive increasing/decreasing sequences)"""
        runs = 1
        for i in range(1, self.n):
            if (self.numbers[i] > self.numbers[i-1]) != (self.numbers[i-1] > self.numbers[i-2] if i > 1 else True):
                runs += 1
        
        # Expected runs for random sequence
        expected_runs = (2 * self.n - 1) / 3
        variance = (16 * self.n - 29) / 90
        
        z_score = (runs - expected_runs) / math.sqrt(variance)
        passed = abs(z_score) < 1.96  # 95% confidence interval
        
        return {
            'test': 'Runs Test',
            'runs': runs,
            'expected_runs': expected_runs,
            'z_score': z_score,
            'passed': passed
        }
    
    def serial_correlation_test(self):
        """Test for serial correlation between consecutive numbers"""
        if self.n < 2:
            return {'test': 'Serial Correlation', 'error': 'Not enough data'}
        
        # Calculate correlation coefficient
        mean_val = statistics.mean(self.numbers)
        
        numerator = sum((self.numbers[i] - mean_val) * (self.numbers[i+1] - mean_val) 
                       for i in range(self.n - 1))
        denominator = sum((x - mean_val) ** 2 for x in self.numbers[:-1])
        
        correlation = numerator / denominator if denominator != 0 else 0
        
        # For random numbers, correlation should be close to 0
        passed = abs(correlation) < 0.1
        
        return {
            'test': 'Serial Correlation',
            'correlation': correlation,
            'passed': passed,
            'threshold': 0.1
        }
    
    def gap_test(self):
        """Test gaps between occurrences of specific values"""
        # Test gaps for value 1024 (middle of range)
        target = 1024
        gaps = []
        last_occurrence = -1
        
        for i, num in enumerate(self.numbers):
            if num == target:
                if last_occurrence >= 0:
                    gaps.append(i - last_occurrence - 1)
                last_occurrence = i
        
        if not gaps:
            return {'test': 'Gap Test', 'error': f'Target value {target} not found'}
        
        # For uniform distribution, gaps should follow geometric distribution
        mean_gap = statistics.mean(gaps) if gaps else 0
        expected_gap = 2047  # Expected gap for uniform distribution over 2048 values
        
        passed = abs(mean_gap - expected_gap) < expected_gap * 0.3  # 30% tolerance
        
        return {
            'test': 'Gap Test',
            'target_value': target,
            'mean_gap': mean_gap,
            'expected_gap': expected_gap,
            'passed': passed,
            'gap_count': len(gaps)
        }
    
    def entropy_estimate(self):
        """Estimate Shannon entropy of the sequence"""
        counts = Counter(self.numbers)
        probabilities = [count / self.n for count in counts.values()]
        
        # Shannon entropy: H = -Σ(p * log2(p))
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        
        # Maximum entropy for uniform distribution over 2048 values
        max_entropy = math.log2(2048)
        entropy_ratio = entropy / max_entropy
        
        return {
            'test': 'Shannon Entropy',
            'entropy': entropy,
            'max_entropy': max_entropy,
            'entropy_ratio': entropy_ratio,
            'passed': entropy_ratio > 0.95,  # Should be close to 1.0 for uniform
            'unique_values': len(counts)
        }
    
    def run_all_tests(self):
        """Run all statistical tests"""
        tests = [
            self.frequency_test(),
            self.runs_test(),
            self.serial_correlation_test(),
            self.gap_test(),
            self.entropy_estimate()
        ]
        
        passed_count = sum(1 for test in tests if test.get('passed', False))
        total_tests = len([t for t in tests if 'error' not in t])
        
        return {
            'tests': tests,
            'summary': {
                'passed': passed_count,
                'total': total_tests,
                'pass_rate': passed_count / total_tests if total_tests > 0 else 0
            }
        }

def generate_test_data(count=1000):
    """Generate test data using our RNG (requires manual entropy collection)"""
    print(f"Generating {count} test numbers...")
    print("Note: This requires manual entropy collection through the GUI")
    print("Please run the GUI version and collect sufficient entropy first.")
    
    # For testing purposes, we'll use a simplified approach
    # In practice, you'd collect this through the GUI
    return None

def analyze_existing_numbers():
    """Analyze a sample set of numbers for demonstration"""
    # Sample numbers that would come from our RNG
    sample_numbers = [
        1298, 1809, 342, 1229, 425, 891, 1456, 723, 1987, 156,
        445, 1678, 892, 234, 1567, 789, 345, 1890, 567, 123,
        1456, 789, 345, 1234, 567, 890, 123, 1789, 456, 234,
        1567, 890, 345, 1234, 678, 901, 234, 1567, 789, 345,
        1234, 567, 890, 123, 1456, 789, 234, 1567, 890, 345
    ]
    
    tests = RandomnessTests(sample_numbers)
    results = tests.run_all_tests()
    
    print("\n" + "="*60)
    print("RANDOMNESS QUALITY ANALYSIS")
    print("="*60)
    
    for test in results['tests']:
        if 'error' in test:
            print(f"\n{test['test']}: ERROR - {test['error']}")
            continue
            
        print(f"\n{test['test']}:")
        print(f"  Status: {'PASS' if test.get('passed') else 'FAIL'}")
        
        # Print test-specific details
        if 'chi_square' in test:
            print(f"  Chi-square: {test['chi_square']:.2f} (critical: {test['critical_value']})")
        elif 'z_score' in test:
            print(f"  Z-score: {test['z_score']:.3f} (|z| should be < 1.96)")
        elif 'correlation' in test:
            print(f"  Correlation: {test['correlation']:.4f} (should be near 0)")
        elif 'entropy_ratio' in test:
            print(f"  Entropy ratio: {test['entropy_ratio']:.4f} (should be near 1.0)")
            print(f"  Unique values: {test['unique_values']}/{len(sample_numbers)}")
    
    print(f"\n" + "-"*40)
    summary = results['summary']
    print(f"OVERALL SCORE: {summary['passed']}/{summary['total']} tests passed")
    print(f"PASS RATE: {summary['pass_rate']:.1%}")
    
    if summary['pass_rate'] >= 0.8:
        print("VERDICT: GOOD randomness quality")
    elif summary['pass_rate'] >= 0.6:
        print("VERDICT: ACCEPTABLE randomness quality")
    else:
        print("VERDICT: POOR randomness quality - needs improvement")

if __name__ == "__main__":
    print("Entropy RNG Randomness Analysis")
    print("="*40)
    
    print("\nAnalyzing sample data...")
    analyze_existing_numbers()
    
    print(f"\n\nTo test your actual RNG output:")
    print("1. Generate many numbers using the GUI (recommend 1000+)")
    print("2. Save them to a file")
    print("3. Load and analyze them with this script")
    
    print(f"\nNote: More numbers = more reliable statistical tests")
    print("Professional RNG testing uses millions of samples")