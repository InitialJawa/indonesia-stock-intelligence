def validate_number(
    value
):

    if value is None:
        return False

    try:

        float(value)

        return True

    except Exception:

        return False