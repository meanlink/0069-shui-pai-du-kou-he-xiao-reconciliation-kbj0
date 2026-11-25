from collections import defaultdict

def pivot(shifts, scans):
    pockets = defaultdict(list)
    for scan in scans:
        pockets[scan["shift_code"]].append(scan)
    rows = []
    for shift in shifts:
        records = pockets[shift["code"]]
        accepted = {row["pass_code"] for row in records if row["verdict"] == "first" or row["ruling"] == "count"}
        rows.append({
            "shift": shift["code"], "route": shift["route"], "seat_limit": shift["capacity"],
            "scan_count": len(records), "riders": len(accepted),
            "duplicates": sum(row["verdict"] == "repeat" for row in records),
            "pending": sum(row["ruling"] == "open" for row in records),
            "capacity_pct": round(100 * len(accepted) / shift["capacity"], 1),
        })
    return rows
