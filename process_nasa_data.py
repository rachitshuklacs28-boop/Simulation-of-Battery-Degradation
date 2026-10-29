
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat
import matplotlib.pyplot as plt


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

battery_file = DATA_DIR / "B0005.mat"

if not battery_file.exists():
    raise FileNotFoundError(
        f"NASA file not found: {battery_file}"
    )

print("Loading NASA battery data...")
mat = loadmat(
    battery_file,
    squeeze_me=True,
    struct_as_record=False
)

battery = mat["B0005"]
cycles = np.atleast_1d(battery.cycle)

records = []
discharge_number = 0

for item in cycles:
    operation = str(item.type).strip().lower()

    if operation != "discharge":
        continue

    data = item.data
    capacity_value = getattr(data, "Capacity", None)

    if capacity_value is None:
        continue

    capacity = float(np.asarray(capacity_value).squeeze())

    if not np.isfinite(capacity) or capacity <= 0:
        continue

    discharge_number += 1

    records.append({
        "Discharge_Cycle": discharge_number,
        "Capacity_Ah": capacity
    })

if not records:
    raise ValueError(
        "No valid discharge capacity measurements found."
    )

df = pd.DataFrame(records)

initial_capacity = df["Capacity_Ah"].iloc[0]
df["SOH_Percent"] = (
    df["Capacity_Ah"] / initial_capacity * 100
)

csv_path = OUTPUT_DIR / "NASA_B0005_capacity.csv"
df.to_csv(csv_path, index=False)

print("\nNASA Battery B0005 - Real Measurements")
print("-" * 45)
print(df.head().to_string(index=False))

print("\nNumber of discharge measurements:", len(df))
print("First measured capacity:", round(initial_capacity, 4), "Ah")
print("Last measured capacity:", round(df["Capacity_Ah"].iloc[-1], 4), "Ah")
print("Last measured SOH:", round(df["SOH_Percent"].iloc[-1], 2), "%")
print("CSV saved to:", csv_path)

plt.figure(figsize=(10, 5))
plt.plot(
    df["Discharge_Cycle"],
    df["Capacity_Ah"],
    marker=".",
    markersize=4,
    label="NASA B0005 measured capacity"
)

plt.xlabel("Discharge Measurement Number")
plt.ylabel("Capacity (Ah)")
plt.title("NASA Battery B0005 - Measured Capacity Degradation")
plt.grid(True)
plt.legend()
plt.tight_layout()

graph_path = OUTPUT_DIR / "NASA_B0005_capacity.png"
plt.savefig(graph_path, dpi=150)
plt.show()

print("Graph saved to:", graph_path)
