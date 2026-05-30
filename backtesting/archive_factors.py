from pathlib import Path
from datetime import datetime
import shutil

MONTH = datetime.today().strftime("%Y-%m")

FILES = {
    "quality": "output/scores/quality_ranking.json",
    "value": "output/scores/value_ranking.json",
    "momentum": "output/scores/momentum_ranking.json",
    "growth": "output/scores/growth_ranking.json"
}

for factor, source_file in FILES.items():

    target_dir = Path(f"snapshots/{factor}")
    target_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = (
        target_dir /
        f"{MONTH}.json"
    )

    shutil.copy2(
        source_file,
        destination
    )

    print(
        f"{factor} -> {destination}"
    )