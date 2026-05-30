from pathlib import Path
from datetime import datetime
import shutil

SNAPSHOT_ROOT = Path("snapshots")


def current_month():
    return datetime.today().strftime(
        "%Y-%m"
    )


def create_snapshot():
    month = current_month()

    fundamentals_src = Path(
        "output/raw/fundamentals.json"
    )

    growth_src = Path(
        "output/raw/growth.json"
    )

    ranking_src = Path(
        "output/scores/final_ranking.json"
    )

    fundamentals_dst = (
        SNAPSHOT_ROOT
        / "fundamentals"
        / f"{month}.json"
    )

    growth_dst = (
        SNAPSHOT_ROOT
        / "growth"
        / f"{month}.json"
    )

    ranking_dst = (
        SNAPSHOT_ROOT
        / "rankings"
        / f"{month}.json"
    )

    fundamentals_dst.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    growth_dst.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ranking_dst.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        fundamentals_src,
        fundamentals_dst
    )

    shutil.copy2(
        growth_src,
        growth_dst
    )

    shutil.copy2(
        ranking_src,
        ranking_dst
    )

    print(
        f"Snapshot saved -> {month}"
    )


if __name__ == "__main__":
    create_snapshot()