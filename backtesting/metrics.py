import numpy as np

PERIODS_PER_YEAR = 12
RISK_FREE_RATE = 0.05


def calculate_cagr(returns):

    cumulative = (1 + returns).prod()

    years = len(returns) / PERIODS_PER_YEAR

    if years <= 0:
        return 0

    return cumulative ** (1 / years) - 1


def calculate_volatility(returns):

    return (
        returns.std()
        * np.sqrt(PERIODS_PER_YEAR)
    )


def calculate_sharpe(returns):

    cagr = calculate_cagr(returns)

    vol = calculate_volatility(returns)

    if vol == 0:
        return 0

    return (
        cagr - RISK_FREE_RATE
    ) / vol


def calculate_drawdown(returns):

    cumulative = (
        1 + returns
    ).cumprod()

    running_max = (
        cumulative.cummax()
    )

    return (
        cumulative
        / running_max
        - 1
    )


def calculate_max_drawdown(
    returns
):
    return (
        calculate_drawdown(
            returns
        ).min()
    )


def calculate_metrics(
    returns
):
    return {
        "cagr": round(
            calculate_cagr(
                returns
            ),
            4
        ),
        "volatility": round(
            calculate_volatility(
                returns
            ),
            4
        ),
        "sharpe": round(
            calculate_sharpe(
                returns
            ),
            4
        ),
        "max_drawdown": round(
            calculate_max_drawdown(
                returns
            ),
            4
        )
    }