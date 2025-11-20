# Entropy-Based Random Number Generator

A cryptographically secure random number generator that uses multiple entropy sources to generate high-quality random numbers between 0 and 2047.

## Features

- **Multiple Entropy Sources**:
  - Mouse movement patterns and timing
  - CPU scheduler tasks and process information
  - Microphone audio input (GUI version only)

- **Cryptographic Strength**: Uses SHA-256 hashing to generate random numbers from collected entropy

- **Two Versions Available**:
  - Command-line interface (CLI)
  - Graphical user interface (GUI) with real-time status display

- **Quality Assurance**: Includes statistical randomness tests to verify output quality

- **Portable Executables**: Build standalone .exe files with PyInstaller

## Requirements

### For CLI Version
```
Python 3.7+
psutil>=5.9.0
pynput>=1.7.6
```

### For GUI Version
```
Python 3.7+
psutil>=5.9.0
pynput>=1.7.6
numpy>=1.21.0
pyaudio>=0.2.11
tkinter (usually included with Python)
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd RNG
```

2. Install dependencies:

For CLI version:
```bash
pip install -r requirements.txt
```

For GUI version:
```bash
pip install -r requirements_gui.txt
```

## Usage

### Command-Line Interface

Run the CLI version:
```bash
python entropy_rng.py
```

**Instructions:**
1. The program will start collecting entropy automatically
2. Move your mouse continuously and randomly for 30 seconds
3. The countdown pauses if you stop moving the mouse
4. After collecting sufficient entropy, 10 random numbers will be generated
5. Enter interactive mode to generate more numbers on demand

### Graphical User Interface

Run the GUI version:
```bash
python entropy_rng_gui.py
```

**Instructions:**
1. Click "Start Entropy Collection"
2. Move your mouse continuously for 30 seconds
3. Make noise near your microphone to add audio entropy
4. Watch the real-time status display showing:
   - Mouse activity status (ACTIVE/INACTIVE)
   - Accumulated active movement time
   - Sample counts from each entropy source
5. Once sufficient entropy is collected, click "Generate 24 Numbers"
6. View the generated numbers in a formatted grid display

## How It Works

### Entropy Collection

The RNG collects entropy from multiple unpredictable sources:

1. **Mouse Movement Entropy**:
   - Captures X/Y coordinates
   - Records high-precision timestamps (nanosecond accuracy)
   - Calculates timing deltas between movements
   - Combines all data using XOR operations

2. **CPU Scheduler Entropy**:
   - Samples CPU times (user, system, idle)
   - Counts active processes
   - Combines with high-precision timestamps
   - Collected every 10ms

3. **Audio Entropy** (GUI only):
   - Records microphone input
   - Analyzes RMS (Root Mean Square) values
   - Extracts peak amplitudes
   - Computes variance of audio samples
   - Combines with timestamps for additional randomness

### Random Number Generation

1. Collects minimum required entropy samples (300+ mouse, 100+ audio)
2. Ensures at least 30 seconds of active mouse movement
3. Combines all entropy sources into a single pool
4. Uses SHA-256 cryptographic hash function to mix entropy
5. Converts hash output to numbers in range 0-2047
6. Each number uses unique combination of entropy data

### Security Features

- **Time-based uniqueness**: Each generation includes nanosecond-precision timestamps
- **Hash mixing**: SHA-256 ensures avalanche effect (small input changes completely change output)
- **No reuse**: Entropy pool continuously grows during collection
- **Multiple sources**: Reduces dependence on any single entropy source

## Testing Randomness Quality

Run the statistical analysis:
```bash
python test_randomness.py
```

The test suite includes:
- **Frequency Test**: Chi-square test for uniform distribution
- **Runs Test**: Checks for sequential patterns
- **Serial Correlation**: Detects correlation between consecutive numbers
- **Gap Test**: Analyzes gaps between value occurrences
- **Shannon Entropy**: Measures information content

## Building Executables

Build standalone executables using PyInstaller:

For CLI version:
```bash
pyinstaller entropy_rng.spec
```

For GUI version:
```bash
pyinstaller entropy_rng_gui.spec
```

Executables will be created in the `dist/` directory.

## Project Structure

```
RNG/
├── entropy_rng.py           # CLI version
├── entropy_rng_gui.py       # GUI version with audio entropy
├── test_entropy_rng.py      # Simple test script
├── test_randomness.py       # Statistical randomness tests
├── requirements.txt         # CLI dependencies
├── requirements_gui.txt     # GUI dependencies
├── entropy_rng.spec         # PyInstaller spec for CLI
├── entropy_rng_gui.spec     # PyInstaller spec for GUI
└── README.md               # This file
```

## Technical Details

- **Output Range**: 0 to 2047 (11 bits of entropy per number)
- **Entropy Pool Size**: Up to 2000 samples per source (configurable)
- **Collection Rate**: ~100 Hz for mouse movements, ~100 Hz for CPU, ~43 Hz for audio
- **Hash Algorithm**: SHA-256 (256-bit output)
- **Mouse Activity Timeout**: 2.0 seconds of inactivity before pausing

## Limitations

- Requires user interaction (mouse movement) for entropy collection
- Audio entropy requires working microphone (GUI version)
- Not suitable for generating large volumes of random numbers quickly
- Best used when high-quality entropy is more important than generation speed

## Use Cases

- Cryptographic key generation
- Secure password generation
- Lottery number selection
- Gaming random events requiring provable fairness
- Educational purposes to understand entropy-based RNGs
- Situations requiring verifiable randomness sources

## Security Considerations

- **Mouse movement patterns** can be influenced by user habits
- **CPU scheduler entropy** may be predictable on idle systems
- Best results when multiple entropy sources are used together
- Not a replacement for OS-level cryptographic RNGs for production systems
- Suitable for scenarios where entropy source transparency is important

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Acknowledgments

- Uses `psutil` for CPU monitoring
- Uses `pynput` for mouse event capture
- Uses `pyaudio` and `numpy` for audio processing
- Inspired by hardware random number generators and entropy collection techniques
