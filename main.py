
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def simulate_battery_degradation(
    initial_capacity,
    total_cycles,
    temperature,
    dod,
    c_rate
):
    # Illustrative model parameters, not experimentally calibrated
    base_loss_per_cycle = 0.0002

    # Assumed stress factors
    temperature_factor = np.exp(
        0.025 * (temperature - 25)
    )

    dod_factor = dod / 50.0

    c_rate_factor = 1 + 0.25 * (c_rate - 0.5)

    loss_per_cycle = (
        base_loss_per_cycle
        * temperature_factor
        * dod_factor
        * c_rate_factor
    )

    cycles = np.arange(total_cycles + 1)

    # Simplified linear capacity-fade equation
    capacity = initial_capacity * (
        1 - loss_per_cycle * cycles
    )

    capacity = np.maximum(capacity, 0)

    soh = capacity / initial_capacity * 100

    results = pd.DataFrame({
        "Cycle": cycles,
        "Capacity_Ah": capacity,
        "SOH_Percent": soh
    })

    return results


if __name__ == "__main__":
    print("\nBATTERY DEGRADATION SIMULATOR")
    print("=" * 40)

    initial_capacity = float(
        input("Enter initial capacity (Ah) [2.0]: ") or 2.0
    )
    total_cycles = int(
        input("Enter total cycles [1000]: ") or 1000
    )
    temperature = float(
        input("Enter temperature in Celsius [25]: ") or 25
    )
    dod = float(
        input("Enter Depth of Discharge (%) [50]: ") or 50
    )
    c_rate = float(
        input("Enter C-rate [0.5]: ") or 0.5
    )

    if initial_capacity <= 0:
        raise ValueError("Capacity must be greater than zero.")

    if total_cycles < 0:
        raise ValueError("Cycles cannot be negative.")

    if not 0 < dod <= 100:
        raise ValueError("DoD must be greater than 0 and at most 100.")

    if temperature <= -273.15:
        raise ValueError("Temperature must be above absolute zero.")

    if c_rate <= 0:
        raise ValueError("C-rate must be greater than zero.")

    results = simulate_battery_degradation(
        initial_capacity,
        total_cycles,
        temperature,
        dod,
        c_rate
    )

    print("\nSIMULATION RESULTS")
    print("=" * 40)
    print(results.head().to_string(index=False))

    final_result = results.iloc[-1]

    print("\nFinal Capacity:", round(final_result["Capacity_Ah"], 3), "Ah")
    print("Final SOH:", round(final_result["SOH_Percent"], 2), "%")

    # Estimate when capacity first reaches 80% SOH
    eol_rows = results[results["SOH_Percent"] <= 80]

    if not eol_rows.empty:
        print("Estimated 80% SOH threshold cycle:",
              int(eol_rows.iloc[0]["Cycle"]))
    else:
        print("80% SOH threshold was not reached in this simulation.")

    results.to_csv("simulation_results.csv", index=False)
    print("\nResults saved to simulation_results.csv")

    # Plot 1: Capacity degradation
    plt.figure(figsize=(10, 5))
    plt.plot(
        results["Cycle"],
        results["Capacity_Ah"],
        label="Capacity (Ah)"
    )
    plt.xlabel("Charge-Discharge Cycles")
    plt.ylabel("Capacity (Ah)")
    plt.title("Battery Capacity Degradation")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("capacity_degradation.png", dpi=150)

    # Plot 2: State of Health
    plt.figure(figsize=(10, 5))
    plt.plot(
        results["Cycle"],
        results["SOH_Percent"],
        label="SOH (%)"
    )
    plt.axhline(
        80,
        linestyle="--",
        label="Illustrative 80% threshold"
    )
    plt.xlabel("Charge-Discharge Cycles")
    plt.ylabel("State of Health (%)")
    plt.title("Battery State of Health")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("battery_soh.png", dpi=150)

    print("Graphs saved successfully.")

    plt.show()
