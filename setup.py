#!/usr/bin/env python3
"""
Setup script for Obsidian Geode migration to google-genai SDK
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages from requirements.txt"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Successfully installed requirements")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def main():
    """Main setup routine"""
    print("🔧 Setting up Obsidian Geode with google-genai SDK...")
    
    if not check_python_version():
        return False
    
    if not install_requirements():
        return False
    
    print("🎉 Setup complete! You can now run the application with:")
    print("   python3 geode_gui.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)