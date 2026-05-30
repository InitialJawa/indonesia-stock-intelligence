def min_max_normalize(values):
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [100 for _ in values]

    return [
        ((v - min_v) / (max_v - min_v)) * 100
        for v in values
    ]