import math

def need(obj, *keys):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ValueError("Missing fields: " + ", ".join(missing))

def number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a measurement")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Measurements must be finite")
    return value

def unique_ids(rows, key="id"):
    ids = [r[key] for r in rows]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("IDs must be nonempty unique strings")

