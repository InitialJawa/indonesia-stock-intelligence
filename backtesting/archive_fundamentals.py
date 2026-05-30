from pathlib import Path
from datetime import datetime
import shutil

month = datetime.today().strftime("%Y-%m")

target = Path("snapshots/fundamentals")
target.mkdir(parents=True, exist_ok=True)

shutil.copy2(
    "output/raw/fundamentals.json",
    target / f"{month}.json"
)

print(f"Archived fundamentals {month}")