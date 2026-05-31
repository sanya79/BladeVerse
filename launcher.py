#!/usr/bin/env python3
"""
Fruit Ninja - Game Launcher with Dependency Check
This script verifies all dependencies are installed before launching the game.
"""

import sys
import subprocess
import os
from pathlib import Path

REQUIRED_PACKAGES = {
    'cv2': 'opencv-python',
    'mediapipe': 'mediapipe',
    'pygame': 'pygame',
    'numpy': 'numpy',
}

def check_python_version():
    """Verify Python 3.10+ is installed"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ ERROR: Python 3.10+ required. You have Python {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor} OK")

def check_dependencies():
    """Verify all required packages are installed"""
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} NOT installed")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr run:")
        print('  pip install -r "requirements (1).txt"')
        sys.exit(1)

def check_directories():
    """Verify required directories exist"""
    dirs = ['assets', 'assets/fonts', 'assets/sounds', 'assets/images', 'saves']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f"✓ Directories OK")

def print_controls():
    """Print in-game controls"""
    print("\n" + "="*60)
    print("⚡ BLADE HAND - Gesture-Controlled Fruit Ninja")
    print("="*60)
    print("\n🎮 GAMEPLAY:")
    print("  • Point INDEX FINGER at webcam and move to slice fruits")
    print("  • Make a FIST to activate shield")
    print("  • Show TWO FINGERS for combo mode")
    print("  • Open PALM for slow-motion")
    print("\n⌨️ KEYBOARD CONTROLS:")
    print("  ESC     - Pause/Unpause")
    print("  F3      - Toggle FPS counter")
    print("  F4      - Toggle debug mode (hand landmarks)")
    print("  F11     - Toggle fullscreen")
    print("\n" + "="*60 + "\n")

def main():
    """Main launcher"""
    print("🔍 Checking system...")
    print("-" * 60)
    
    try:
        check_python_version()
        check_dependencies()
        check_directories()
        print("-" * 60)
        print_controls()
        
        print("🎮 Starting game...\n")
        
        # Import and run main game
        from main import main as run_game
        run_game()
        
    except KeyboardInterrupt:
        print("\n\n👋 Game closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
