# main.py
"""
Entry point for the OpenCart Python Billing System.

Adds the repository root to sys.path so that src.* imports resolve
correctly, then instantiates and runs the MainApplication GUI window.

Usage:
    uv run python main.py
"""
import sys
import os

# Ensure the root workspace is added to the import search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui.app import MainApplication

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
