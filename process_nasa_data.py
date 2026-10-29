
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat
import matplotlib.pyplot as plt


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def process_battery(battery_file):
    battery_name = battery_file.stem

    csv_path = OUTPUT_DIR / f"NASA_{battery_name}_capacity.csv"
    graph_path = OUTPUT_DIR / f"NASA_{battery_name}_capacity.png"

    # Preserve existing outputs instead of overwriting them.
    if csv_path.exists() and graph_path.exists():
        print(f"\nSkipping {battery_name}: outputs already exist.")
        return

    print(f"\nLoading NASA battery {battery_name}...")

    mat = loadmat(
        battery_file,
        squeeze_me=True,
        struct_as_record=False
    )

    if battery_name not in mat:
        raise KeyError(
            f"Battery variable '{battery_name}' not found in {battery_file.name}"
        )

    battery = mat[battery_name]
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
            f"No valid discharge capacity measurements found for {battery_name}."
        )

    df = pd.DataFrame(records)

    initial_capacity = df["Capacity_Ah"].iloc[0]
    df["SOH_Percent"] = (
        df["Capacity_Ah"] / initial_capacity * 100
    )

    df.to_csv(csv_path, index=False)

    plt.figure(figsize=(10, 5))
    plt.plot(
        df["Discharge_Cycle"],
        df["Capacity_Ah"],
        marker=".",
        markersize=4,
        label=f"NASA {battery_name} measured capacity"
    )

    plt.xlabel("Discharge Measurement Number")
    plt.ylabel("Capacity (Ah)")
    plt.title(f"NASA Battery {battery_name} - Capacity Degradation")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(graph_path, dpi=150)
    plt.close()

    print(f"Measurements: {len(df)}")
    print(f"Initial capacity: {initial_capacity:.4f} Ah")
    print(f"Final capacity: {df['Capacity_Ah'].iloc[-1]:.4f} Ah")
    print(f"Final SOH: {df['SOH_Percent'].iloc[-1]:.2f}%")
    print(f"CSV saved: {csv_path.name}")
    print(f"Graph saved: {graph_path.name}")


def main():
    battery_files = sorted(DATA_DIR.glob("B*.mat"))

    if not battery_files:
        raise FileNotFoundError(
            f"No NASA .mat files found in {DATA_DIR}"
        )

    print(f"Found {len(battery_files)} NASA battery files.")

    for battery_file in battery_files:
        try:
            process_battery(battery_file)
        except Exception as error:
            print(f"ERROR processing {battery_file.name}: {error}")

    print("\nNASA data processing finished.")
    print("Check data/processed for CSV files and graphs.")


if __name__ == "__main__":
    main()
