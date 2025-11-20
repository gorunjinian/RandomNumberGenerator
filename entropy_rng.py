#!/usr/bin/env python3
"""
Entropy-based Random Number Generator
Uses mouse movement and CPU scheduler tasks as entropy sources
Generates random numbers between 0 and 2047
"""

import time
import hashlib
import threading
import queue
from collections import deque
import psutil
from pynput import mouse

class EntropyCollector:
    def __init__(self):
        self.mouse_entropy = deque(maxlen=2000)
        self.cpu_entropy = deque(maxlen=2000)
        self.collecting = False
        self.entropy_queue = queue.Queue()
        self.collection_start_time = None
        self.mouse_movement_start = None
        self.last_mouse_activity = None
        self.total_active_movement_time = 0.0
        self.mouse_activity_timeout = 2.0  # Consider mouse inactive after 2 seconds
        
    def on_mouse_move(self, x, y):
        if self.collecting:
            timestamp = time.time_ns()
            current_time = time.time()
            
            # Update mouse activity tracking
            if self.last_mouse_activity is not None:
                # Add time since last activity to total if mouse was recently active
                time_since_last = current_time - self.last_mouse_activity
                if time_since_last <= self.mouse_activity_timeout:
                    self.total_active_movement_time += time_since_last
            
            self.last_mouse_activity = current_time
            
            # Record when mouse movement started
            if self.mouse_movement_start is None:
                self.mouse_movement_start = current_time
            
            # Combine coordinates with high-precision timestamp for better entropy
            entropy_data = (x ^ y ^ (timestamp & 0xFFFFFFFF)) & 0xFFFF
            
            # Add additional entropy from timing between movements
            if len(self.mouse_entropy) > 0:
                time_delta = int((timestamp % 1000000) * 1000)  # Microsecond precision
                entropy_data ^= time_delta
            
            self.mouse_entropy.append(entropy_data)
            self.entropy_queue.put(('mouse', entropy_data))
    
    def collect_cpu_entropy(self):
        while self.collecting:
            try:
                # Get CPU times and process information
                cpu_times = psutil.cpu_times()
                processes = len(psutil.pids())
                
                # Create entropy from CPU scheduler data
                entropy_data = int((cpu_times.user * 1000000 + 
                                 cpu_times.system * 1000000 + 
                                 cpu_times.idle * 1000000 + 
                                 processes * time.time_ns()) % (2**32))
                
                self.cpu_entropy.append(entropy_data)
                self.entropy_queue.put(('cpu', entropy_data))
                
            except Exception:
                pass
            
            time.sleep(0.01)  # 10ms collection interval
    
    def start_collection(self):
        self.collecting = True
        self.collection_start_time = time.time()
        self.mouse_movement_start = None
        self.last_mouse_activity = None
        self.total_active_movement_time = 0.0
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move)
        self.mouse_listener.start()
        
        # Start CPU entropy collection thread
        self.cpu_thread = threading.Thread(target=self.collect_cpu_entropy, daemon=True)
        self.cpu_thread.start()
    
    def stop_collection(self):
        self.collecting = False
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
    
    def get_entropy_pool(self):
        """Combine all entropy sources into a single pool"""
        entropy_pool = []
        
        # Add mouse entropy
        entropy_pool.extend(list(self.mouse_entropy))
        
        # Add CPU entropy
        entropy_pool.extend(list(self.cpu_entropy))
        
        return entropy_pool
    
    def get_mouse_movement_duration(self):
        """Get total accumulated time of active mouse movement"""
        if self.last_mouse_activity is None:
            return 0
        
        current_time = time.time()
        accumulated_time = self.total_active_movement_time
        
        # Add current session if mouse is currently active
        if current_time - self.last_mouse_activity <= self.mouse_activity_timeout:
            accumulated_time += current_time - self.last_mouse_activity
        
        return accumulated_time
    
    def is_mouse_currently_active(self):
        """Check if mouse is currently being moved (within timeout)"""
        if self.last_mouse_activity is None:
            return False
        return (time.time() - self.last_mouse_activity) <= self.mouse_activity_timeout
    
    def has_sufficient_entropy(self, required_duration=30, min_mouse_samples=300):
        """Check if we have collected sufficient entropy"""
        mouse_duration = self.get_mouse_movement_duration()
        mouse_samples = len(self.mouse_entropy)
        
        return (mouse_duration >= required_duration and 
                mouse_samples >= min_mouse_samples)

class EntropyRNG:
    def __init__(self):
        self.collector = EntropyCollector()
        self.generated_numbers = []
    
    def generate_random_number(self, min_entropy_samples=300):
        """Generate a random number between 0 and 2047 using collected entropy"""
        if not self.collector.has_sufficient_entropy():
            mouse_duration = self.collector.get_mouse_movement_duration()
            mouse_samples = len(self.collector.mouse_entropy)
            raise ValueError(f"Insufficient entropy: {mouse_duration:.1f}s mouse movement, {mouse_samples} mouse samples. Need 30s+ movement with 300+ samples.")
        
        entropy_pool = self.collector.get_entropy_pool()
        
        if len(entropy_pool) < min_entropy_samples:
            raise ValueError(f"Insufficient total entropy: {len(entropy_pool)} samples, need at least {min_entropy_samples}")
        
        # Mix entropy using SHA-256
        hasher = hashlib.sha256()
        
        # Add current timestamp for additional entropy
        hasher.update(str(time.time_ns()).encode())
        
        # Add all entropy samples
        for sample in entropy_pool:
            hasher.update(sample.to_bytes(4, 'big'))
        
        # Get hash and convert to number in range 0-2047
        hash_bytes = hasher.digest()
        random_int = int.from_bytes(hash_bytes[:4], 'big')
        result = random_int % 2048
        
        self.generated_numbers.append(result)
        return result
    
    def start_entropy_collection(self):
        self.collector.start_collection()
    
    def stop_entropy_collection(self):
        self.collector.stop_collection()
    
    def get_entropy_status(self):
        """Return current entropy collection status"""
        mouse_count = len(self.collector.mouse_entropy)
        cpu_count = len(self.collector.cpu_entropy)
        return {
            'mouse_samples': mouse_count,
            'cpu_samples': cpu_count,
            'total_samples': mouse_count + cpu_count
        }

def main():
    print("Entropy-based Random Number Generator")
    print("Generates numbers between 0 and 2047")
    print("=" * 50)
    
    rng = EntropyRNG()
    
    try:
        # Start entropy collection
        print("Starting entropy collection...")
        rng.start_entropy_collection()
        
        print("\n*** ENTROPY COLLECTION PHASE ***")
        print("Please move your mouse randomly and continuously for 30 seconds!")
        print("IMPORTANT: You must keep moving the mouse - if you stop, the countdown pauses.")
        print("This ensures maximum entropy for cryptographically strong random numbers.")
        print("The program is also collecting CPU scheduler entropy automatically.")
        print("\nStarting entropy collection countdown...\n")
        
        while True:
            status = rng.get_entropy_status()
            mouse_duration = rng.collector.get_mouse_movement_duration()
            is_mouse_active = rng.collector.is_mouse_currently_active()
            
            if mouse_duration == 0:
                print("\rWaiting for mouse movement to begin... Move your mouse!", end="")
            elif not is_mouse_active:
                remaining_time = max(0, 30 - mouse_duration)
                print(f"\rMOUSE STOPPED! Continue moving... | Active time: {mouse_duration:.1f}s | Remaining: {remaining_time:.1f}s | Samples - Mouse: {status['mouse_samples']}, CPU: {status['cpu_samples']}         ", end="")
            else:
                remaining_time = max(0, 30 - mouse_duration)
                print(f"\rMouse ACTIVE | Active time: {mouse_duration:.1f}s | Remaining: {remaining_time:.1f}s | Samples - Mouse: {status['mouse_samples']}, CPU: {status['cpu_samples']}         ", end="")
            
            if rng.collector.has_sufficient_entropy():
                print("\n\n*** ENTROPY COLLECTION COMPLETE! ***")
                print(f"Collected {status['mouse_samples']} mouse samples over {mouse_duration:.1f} seconds of active movement")
                print(f"Total entropy samples: {status['total_samples']}")
                break
            
            time.sleep(0.1)
        
        # Generate and display random numbers
        print("\nGenerating random numbers...")
        print("-" * 30)
        
        for i in range(10):
            try:
                random_num = rng.generate_random_number()
                print(f"Random number {i+1}: {random_num}")
            except ValueError as e:
                print(f"Error generating number: {e}")
                break
        
        # Interactive mode
        print("\n" + "=" * 50)
        print("Interactive mode - Press Enter to generate more numbers, 'q' to quit")
        
        while True:
            user_input = input("\nPress Enter for new random number (or 'q' to quit): ")
            if user_input.lower() == 'q':
                break
            
            try:
                status = rng.get_entropy_status()
                mouse_duration = rng.collector.get_mouse_movement_duration()
                is_active = rng.collector.is_mouse_currently_active()
                activity_status = "ACTIVE" if is_active else "INACTIVE"
                print(f"Current entropy - Mouse: {status['mouse_samples']} samples ({mouse_duration:.1f}s active movement, {activity_status}), Total: {status['total_samples']}")
                
                random_num = rng.generate_random_number()
                print(f"Random number: {random_num}")
                
            except ValueError as e:
                print(f"Error: {e}")
                print("Need to collect more entropy! Move your mouse randomly and continuously for 30 seconds.")
    
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
    
    finally:
        print("Stopping entropy collection...")
        rng.stop_entropy_collection()
        print("Done!")

if __name__ == "__main__":
    main()