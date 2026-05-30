from pathlib import Path
from datetime import datetime
import shutil

ARCHIVE_DIR = Path(
    "archives/rankings"
)

ARCHIVE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def archive_current_ranking():

    current_month = (
        datetime.today()
        .strftime("%Y-%m")
    )

    source = Path(
        "output/scores/final_ranking.json"
    )

    destination = (
        ARCHIVE_DIR
        / f"{current_month}.json"
    )

    shutil.copy2(
        source,
        destination
    )

    print(
        f"Archived -> {destination}"
    )


if __name__ == "__main__":
    archive_current_ranking()