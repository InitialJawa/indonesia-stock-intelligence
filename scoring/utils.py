# file: scoring/utils.py

def min_max_normalize(values):
    """
    Legacy normalization. Rentan terhadap outlier.
    Dipertahankan sementara agar modul lain tidak rusak.
    """
    if not values:
        return []
        
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [100.0 for _ in values]

    return [
        ((v - min_v) / (max_v - min_v)) * 100
        for v in values
    ]

def percentile_normalize(values):
    """
    Rank-based normalization. Tahan terhadap outlier.
    Mengubah nilai menjadi persentil dari 0 hingga 100.
    """
    n = len(values)
    if n == 0:
        return []
    if n <= 1 or max(values) == min(values):
        # Semua nilai sama (termasuk semua 0): tidak bisa dibedakan,
        # kembalikan 50 (posisi tengah) bukan 100 agar tidak misleading.
        return [50.0 for _ in values]

    scores = []
    for v in values:
        lesser = sum(1 for x in values if x < v)
        equal = sum(1 for x in values if x == v)
        
        # Fractional ranking untuk menangani data bernilai sama (ties)
        rank = lesser + (equal - 1) / 2.0
        score = (rank / (n - 1)) * 100
        scores.append(round(score, 2))
        
    return scores