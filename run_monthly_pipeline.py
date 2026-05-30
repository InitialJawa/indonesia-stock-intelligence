import subprocess


PIPELINE = [

    "python collectors/fundamentals.py",

    "python collectors/growth.py",

    "python collectors/prices.py",

    "python scoring/quality_score.py",

    "python scoring/growth_score.py",

    "python scoring/value_score.py",

    "python scoring/final_score.py",

    "python backtesting/archive_current_state.py",

    "python backtesting/rebalance.py"
]


def run():

    for command in PIPELINE:

        print(
            f"\nRunning: {command}"
        )

        result = subprocess.run(
            command,
            shell=True
        )

        if result.returncode != 0:

            raise Exception(
                f"Failed: {command}"
            )


if __name__ == "__main__":
    run()