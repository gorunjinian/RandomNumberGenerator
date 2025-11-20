#!/usr/bin/env python3
"""
Entropy-based Random Number Generator - GUI Version
Uses mouse movement, CPU scheduler tasks, and microphone audio as entropy sources
Generates random numbers between 0 and 2047
"""

import time
import hashlib
import threading
import queue
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
from pynput import mouse
import numpy as np
import pyaudio

class EntropyCollector:
    def __init__(self):
        self.mouse_entropy = deque(maxlen=2000)
        self.cpu_entropy = deque(maxlen=2000)
        self.audio_entropy = deque(maxlen=2000)
        self.collecting = False
        self.entropy_queue = queue.Queue()
        self.collection_start_time = None
        self.mouse_movement_start = None
        self.last_mouse_activity = None
        self.total_active_movement_time = 0.0
        self.mouse_activity_timeout = 2.0
        
        # Audio recording setup
        self.audio_recording = False
        self.audio_stream = None
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk = 1024
        self.audio_p = pyaudio.PyAudio()
        
    def on_mouse_move(self, x, y):
        if self.collecting:
            timestamp = time.time_ns()
            current_time = time.time()
            
            # Update mouse activity tracking
            if self.last_mouse_activity is not None:
                time_since_last = current_time - self.last_mouse_activity
                if time_since_last <= self.mouse_activity_timeout:
                    self.total_active_movement_time += time_since_last
            
            self.last_mouse_activity = current_time
            
            if self.mouse_movement_start is None:
                self.mouse_movement_start = current_time
            
            # Combine coordinates with high-precision timestamp for better entropy
            entropy_data = (x ^ y ^ (timestamp & 0xFFFFFFFF)) & 0xFFFF
            
            # Add additional entropy from timing between movements
            if len(self.mouse_entropy) > 0:
                time_delta = int((timestamp % 1000000) * 1000)
                entropy_data ^= time_delta
            
            self.mouse_entropy.append(entropy_data)
            self.entropy_queue.put(('mouse', entropy_data))
    
    def collect_cpu_entropy(self):
        while self.collecting:
            try:
                cpu_times = psutil.cpu_times()
                processes = len(psutil.pids())
                
                entropy_data = int((cpu_times.user * 1000000 + 
                                 cpu_times.system * 1000000 + 
                                 cpu_times.idle * 1000000 + 
                                 processes * time.time_ns()) % (2**32))
                
                self.cpu_entropy.append(entropy_data)
                self.entropy_queue.put(('cpu', entropy_data))
                
            except Exception:
                pass
            
            time.sleep(0.01)
    
    def collect_audio_entropy(self):
        """Collect entropy from microphone audio input"""
        try:
            self.audio_stream = self.audio_p.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                frames_per_buffer=self.audio_chunk
            )
            
            while self.collecting and self.audio_recording:
                try:
                    # Read audio data
                    audio_data = self.audio_stream.read(self.audio_chunk, exception_on_overflow=False)
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Generate entropy from audio characteristics
                    if len(audio_array) > 0:
                        # Use RMS, peak, variance, and spectral characteristics
                        rms = int(np.sqrt(np.mean(audio_array**2))) & 0xFFFF
                        peak = int(np.max(np.abs(audio_array))) & 0xFFFF
                        variance = int(np.var(audio_array)) & 0xFFFFFFFF
                        
                        # Combine with timestamp for additional entropy
                        timestamp = time.time_ns()
                        entropy_data = (rms ^ peak ^ (variance & 0xFFFF) ^ (timestamp & 0xFFFF)) & 0xFFFF
                        
                        self.audio_entropy.append(entropy_data)
                        self.entropy_queue.put(('audio', entropy_data))
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Audio collection error: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
    
    def start_collection(self, include_audio=True):
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
        
        # Start audio entropy collection if requested
        if include_audio:
            self.audio_recording = True
            self.audio_thread = threading.Thread(target=self.collect_audio_entropy, daemon=True)
            self.audio_thread.start()
    
    def stop_collection(self):
        self.collecting = False
        self.audio_recording = False
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
    
    def get_entropy_pool(self):
        entropy_pool = []
        entropy_pool.extend(list(self.mouse_entropy))
        entropy_pool.extend(list(self.cpu_entropy))
        entropy_pool.extend(list(self.audio_entropy))
        return entropy_pool
    
    def get_mouse_movement_duration(self):
        if self.last_mouse_activity is None:
            return 0
        
        current_time = time.time()
        accumulated_time = self.total_active_movement_time
        
        if current_time - self.last_mouse_activity <= self.mouse_activity_timeout:
            accumulated_time += current_time - self.last_mouse_activity
        
        return accumulated_time
    
    def is_mouse_currently_active(self):
        if self.last_mouse_activity is None:
            return False
        return (time.time() - self.last_mouse_activity) <= self.mouse_activity_timeout
    
    def has_sufficient_entropy(self, required_duration=30, min_mouse_samples=300, min_audio_samples=100):
        mouse_duration = self.get_mouse_movement_duration()
        mouse_samples = len(self.mouse_entropy)
        audio_samples = len(self.audio_entropy)
        
        return (mouse_duration >= required_duration and 
                mouse_samples >= min_mouse_samples and
                audio_samples >= min_audio_samples)

class EntropyRNG:
    def __init__(self):
        self.collector = EntropyCollector()
        self.generated_numbers = []
    
    def generate_random_numbers(self, count=24, min_entropy_samples=400):
        """Generate multiple random numbers between 0 and 2047"""
        if not self.collector.has_sufficient_entropy():
            mouse_duration = self.collector.get_mouse_movement_duration()
            mouse_samples = len(self.collector.mouse_entropy)
            audio_samples = len(self.collector.audio_entropy)
            raise ValueError(f"Insufficient entropy: {mouse_duration:.1f}s mouse, {mouse_samples} mouse samples, {audio_samples} audio samples")
        
        entropy_pool = self.collector.get_entropy_pool()
        
        if len(entropy_pool) < min_entropy_samples:
            raise ValueError(f"Insufficient total entropy: {len(entropy_pool)} samples, need at least {min_entropy_samples}")
        
        numbers = []
        for i in range(count):
            # Create unique hash for each number by including the index
            hasher = hashlib.sha256()
            hasher.update(str(time.time_ns() + i).encode())
            hasher.update(str(i).encode())
            
            # Add all entropy samples
            for j, sample in enumerate(entropy_pool):
                hasher.update((sample ^ i ^ j).to_bytes(4, 'big'))
            
            # Get hash and convert to number in range 0-2047
            hash_bytes = hasher.digest()
            random_int = int.from_bytes(hash_bytes[:4], 'big')
            result = random_int % 2048
            numbers.append(result)
        
        self.generated_numbers.extend(numbers)
        return numbers
    
    def start_entropy_collection(self, include_audio=True):
        self.collector.start_collection(include_audio)
    
    def stop_entropy_collection(self):
        self.collector.stop_collection()
    
    def get_entropy_status(self):
        mouse_count = len(self.collector.mouse_entropy)
        cpu_count = len(self.collector.cpu_entropy)
        audio_count = len(self.collector.audio_entropy)
        return {
            'mouse_samples': mouse_count,
            'cpu_samples': cpu_count,
            'audio_samples': audio_count,
            'total_samples': mouse_count + cpu_count + audio_count
        }

class EntropyRNGGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Entropy Random Number Generator")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        self.rng = EntropyRNG()
        self.collecting = False
        self.collection_thread = None
        
        self.create_widgets()
        self.update_status()
    
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Entropy Random Number Generator", 
                              font=('Arial', 18, 'bold'), fg='#ffffff', bg='#2b2b2b')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(self.root, text="Generates cryptographically secure random numbers (0-2047)", 
                                font=('Arial', 10), fg='#cccccc', bg='#2b2b2b')
        subtitle_label.pack(pady=(0, 20))
        
        # Status Frame
        status_frame = tk.Frame(self.root, bg='#3b3b3b', relief='raised', bd=1)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(status_frame, text="Entropy Collection Status", font=('Arial', 12, 'bold'), 
                fg='#ffffff', bg='#3b3b3b').pack(pady=10)
        
        self.status_label = tk.Label(status_frame, text="Not collecting entropy", 
                                   font=('Arial', 10), fg='#ffaa00', bg='#3b3b3b')
        self.status_label.pack(pady=5)
        
        self.entropy_label = tk.Label(status_frame, text="", font=('Arial', 9), 
                                    fg='#cccccc', bg='#3b3b3b')
        self.entropy_label.pack(pady=5)
        
        # Control Buttons
        button_frame = tk.Frame(self.root, bg='#2b2b2b')
        button_frame.pack(pady=20)
        
        self.collect_button = tk.Button(button_frame, text="Start Entropy Collection", 
                                      command=self.toggle_collection, font=('Arial', 12),
                                      bg='#4CAF50', fg='white', padx=20, pady=10)
        self.collect_button.pack(side='left', padx=10)
        
        self.generate_button = tk.Button(button_frame, text="Generate 24 Numbers", 
                                       command=self.generate_numbers, font=('Arial', 12),
                                       bg='#2196F3', fg='white', padx=20, pady=10, state='disabled')
        self.generate_button.pack(side='left', padx=10)
        
        # Results Frame
        results_frame = tk.Frame(self.root, bg='#3b3b3b', relief='raised', bd=1)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(results_frame, text="Generated Numbers", font=('Arial', 12, 'bold'), 
                fg='#ffffff', bg='#3b3b3b').pack(pady=10)
        
        # Text widget for results with scrollbar
        text_frame = tk.Frame(results_frame, bg='#3b3b3b')
        text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.results_text = tk.Text(text_frame, font=('Consolas', 11), bg='#1e1e1e', 
                                  fg='#00ff00', insertbackground='#ffffff', wrap='word')
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Initial message
        self.results_text.insert('end', "Welcome to the Entropy RNG!\n\n")
        self.results_text.insert('end', "Instructions:\n")
        self.results_text.insert('end', "1. Click 'Start Entropy Collection'\n")
        self.results_text.insert('end', "2. Move your mouse continuously for 30 seconds\n")
        self.results_text.insert('end', "3. Make some noise near your microphone\n")
        self.results_text.insert('end', "4. Click 'Generate 24 Numbers' when ready\n\n")
        self.results_text.config(state='disabled')
    
    def toggle_collection(self):
        if not self.collecting:
            self.start_collection()
        else:
            self.stop_collection()
    
    def start_collection(self):
        try:
            self.collecting = True
            self.collect_button.config(text="Stop Collection", bg='#f44336')
            self.status_label.config(text="Collecting entropy...", fg='#00ff00')
            self.rng.start_entropy_collection(include_audio=True)
            
            # Add message to results
            self.results_text.config(state='normal')
            self.results_text.insert('end', f"[{time.strftime('%H:%M:%S')}] Started entropy collection\n")
            self.results_text.insert('end', "Move your mouse and make noise!\n\n")
            self.results_text.config(state='disabled')
            self.results_text.see('end')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start collection: {e}")
            self.collecting = False
    
    def stop_collection(self):
        self.collecting = False
        self.collect_button.config(text="Start Entropy Collection", bg='#4CAF50')
        self.status_label.config(text="Collection stopped", fg='#ffaa00')
        self.rng.stop_entropy_collection()
        
        self.results_text.config(state='normal')
        self.results_text.insert('end', f"[{time.strftime('%H:%M:%S')}] Stopped entropy collection\n\n")
        self.results_text.config(state='disabled')
        self.results_text.see('end')
    
    def generate_numbers(self):
        try:
            numbers = self.rng.generate_random_numbers(24)
            
            self.results_text.config(state='normal')
            self.results_text.insert('end', f"[{time.strftime('%H:%M:%S')}] Generated 24 random numbers:\n")
            
            # Display numbers in a grid format (6x4)
            for i in range(0, len(numbers), 6):
                row = numbers[i:i+6]
                row_text = " | ".join(f"{num:4d}" for num in row)
                self.results_text.insert('end', f"{row_text}\n")
            
            self.results_text.insert('end', "\n" + "="*50 + "\n\n")
            self.results_text.config(state='disabled')
            self.results_text.see('end')
            
        except ValueError as e:
            messagebox.showwarning("Insufficient Entropy", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate numbers: {e}")
    
    def update_status(self):
        if self.collecting:
            status = self.rng.get_entropy_status()
            mouse_duration = self.rng.collector.get_mouse_movement_duration()
            is_mouse_active = self.rng.collector.is_mouse_currently_active()
            
            mouse_status = "ACTIVE" if is_mouse_active else "INACTIVE"
            remaining_time = max(0, 30 - mouse_duration)
            
            status_text = f"Mouse: {mouse_status} | Active time: {mouse_duration:.1f}s | Remaining: {remaining_time:.1f}s"
            entropy_text = f"Samples - Mouse: {status['mouse_samples']}, CPU: {status['cpu_samples']}, Audio: {status['audio_samples']}"
            
            self.status_label.config(text=status_text)
            self.entropy_label.config(text=entropy_text)
            
            # Enable generate button if sufficient entropy
            if self.rng.collector.has_sufficient_entropy():
                self.generate_button.config(state='normal')
                self.status_label.config(fg='#00ff00')
            else:
                self.generate_button.config(state='disabled')
                self.status_label.config(fg='#ffaa00')
        else:
            self.generate_button.config(state='disabled')
        
        # Schedule next update
        self.root.after(100, self.update_status)

def main():
    root = tk.Tk()
    app = EntropyRNGGUI(root)
    
    def on_closing():
        if app.collecting:
            app.stop_collection()
        if hasattr(app.rng.collector, 'audio_p'):
            app.rng.collector.audio_p.terminate()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()