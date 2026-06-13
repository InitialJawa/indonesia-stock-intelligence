import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_settings():
    path = os.path.join(BASE_DIR, "config", "settings.json")
    with open(path, "r") as f:
        return json.load(f)


def load_universe(universe_key=None):
    path = os.path.join(BASE_DIR, "config", "universe.json")
    with open(path, "r") as f:
        config = json.load(f)

    if universe_key is None:
        universe_key = config.get("default", "IDX30")

    universe_info = config["universes"].get(universe_key, config["universes"]["IDX30"])
    universe_file = universe_info["file"]
    if not os.path.isabs(universe_file):
        universe_file = os.path.join(BASE_DIR, universe_file)

    with open(universe_file, "r") as f:
        return json.load(f)
