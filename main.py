"""Entry point — selects platform adapter and runs the game."""
import sys
import os

# Ensure project root is on the path regardless of how we're invoked
sys.path.insert(0, os.path.dirname(__file__))

from adapters.pygame_adapter.game_loop import run

if __name__ == "__main__":
    run()
