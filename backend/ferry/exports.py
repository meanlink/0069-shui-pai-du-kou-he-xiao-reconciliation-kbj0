from csv import DictWriter
from io import StringIO

COLUMNS = ("shift","route","seat_limit","scan_count","riders","duplicates","pending","capacity_pct")

def as_csv(rows):
    buffer = StringIO(newline="")
    writer = DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
