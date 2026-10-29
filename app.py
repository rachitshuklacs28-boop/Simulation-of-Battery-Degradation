
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Battery Degradation Simulator",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 Battery Degradation Simulator")

st.write(
    "Explore battery capacity fade using a simplified mathematical "
    "model and compare its degradation trend with NASA battery measurements."
)

st.warning(
    "Educational simulation only. The model coefficients are illustrative "
    "and have not been calibrated against experimental battery data."
)

# --------------------------------------------------
# 1. SIMULATION INPUTS
# --------------------------------------------------

st.sidebar.header("Battery Parameters")

initial_capacity = st.sidebar.number_input(
    "Initial capacity (Ah)",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1
)

total_cycles = st.sidebar.slider(
    "Total cycles",
    min_value=0,
    max_value=3000,
    value=1000,
    step=100
)

temperature = st.sidebar.slider(
    "Temperature (°C)",
    min_value=0,
    max_value=60,
    value=25
)

dod = st.sidebar.slider(
    "Depth of Discharge (%)",
    min_value=10,
    max_value=100,
    value=50
)

c_rate = st.sidebar.slider(
    "C-rate",
    min_value=0.5,
    max_value=3.0,
    value=0.5,
    step=0.5
)

# --------------------------------------------------
# 2. ILLUSTRATIVE CAPACITY-FADE MODEL
# --------------------------------------------------

base_loss_per_cycle = 0.0002

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

capacity = initial_capacity * (
    1 - loss_per_cycle * cycles
)

capacity = np.maximum(capacity, 0)

soh = capacity / initial_capacity * 100

results = pd.DataFrame({
    "Cycle": cycles,
    "Capacity (Ah)": capacity,
    "SOH (%)": soh
})

final_capacity = float(capacity[-1])
final_soh = float(soh[-1])

# --------------------------------------------------
# 3. SIMULATION SUMMARY
# --------------------------------------------------

st.header("Simulation Results")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Initial Capacity",
    f"{initial_capacity:.2f} Ah"
)

col2.metric(
    "Final Capacity",
    f"{final_capacity:.3f} Ah"
)

col3.metric(
    "Final SOH",
    f"{final_soh:.2f}%"
)

eol = results[results["SOH (%)"] <= 80]

if not eol.empty:
    st.info(
        f"The illustrative model reaches the 80% SOH threshold "
        f"at cycle {int(eol.iloc[0]['Cycle'])}."
    )
else:
    st.info(
        "The illustrative model does not reach the 80% SOH threshold "
        "within the selected cycle range."
    )

# --------------------------------------------------
# 4. SIMULATED CAPACITY AND SOH GRAPHS
# --------------------------------------------------

st.subheader("Simulated Capacity Degradation")

st.line_chart(
    results,
    x="Cycle",
    y="Capacity (Ah)",
    x_label="Simulation Cycle",
    y_label="Capacity (Ah)"
)

st.subheader("Simulated Battery State of Health")

st.line_chart(
    results,
    x="Cycle",
    y="SOH (%)",
    x_label="Simulation Cycle",
    y_label="SOH (%)"
)

st.subheader("Simulation Data")

st.dataframe(
    results.head(10),
    use_container_width=True
)

st.download_button(
    "Download Simulation Results (CSV)",
    data=results.to_csv(index=False).encode("utf-8"),
    file_name="simulation_results.csv",
    mime="text/csv"
)

# --------------------------------------------------
# 5. LOAD NASA B0005 MEASUREMENTS
# --------------------------------------------------

st.divider()
st.header("NASA Real Battery Data")

nasa_csv_path = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "NASA_B0005_capacity.csv"
)

if not nasa_csv_path.exists():
    st.error(
        "NASA CSV not found. Run process_nasa_data.py first."
    )
    st.stop()

nasa_df = pd.read_csv(nasa_csv_path)

required_columns = {
    "Discharge_Cycle",
    "Capacity_Ah"
}

if not required_columns.issubset(nasa_df.columns):
    st.error(
        "NASA CSV is missing required columns: "
        "Discharge_Cycle and Capacity_Ah."
    )
    st.stop()

nasa_df = nasa_df.dropna(
    subset=["Discharge_Cycle", "Capacity_Ah"]
).copy()

nasa_df = nasa_df[
    np.isfinite(nasa_df["Discharge_Cycle"])
    & np.isfinite(nasa_df["Capacity_Ah"])
    & (nasa_df["Capacity_Ah"] > 0)
].sort_values("Discharge_Cycle")

if nasa_df.empty:
    st.error("No valid NASA capacity measurements were found.")
    st.stop()

# Calculate SOH relative to the first valid measured capacity.
nasa_initial_capacity = float(nasa_df["Capacity_Ah"].iloc[0])

nasa_df["SOH_Percent"] = (
    nasa_df["Capacity_Ah"]
    / nasa_initial_capacity
    * 100
)

nasa_final_capacity = float(nasa_df["Capacity_Ah"].iloc[-1])
nasa_final_soh = float(nasa_df["SOH_Percent"].iloc[-1])

col1, col2, col3 = st.columns(3)

col1.metric(
    "NASA Measurements",
    f"{len(nasa_df)}"
)

col2.metric(
    "First Measured Capacity",
    f"{nasa_initial_capacity:.4f} Ah"
)

col3.metric(
    "Last Measured SOH",
    f"{nasa_final_soh:.2f}%"
)

st.caption(
    "NASA Battery B0005 measurements. SOH is calculated relative "
    "to the first valid discharge capacity in this dataset."
)

st.subheader("NASA Measured Capacity")

st.line_chart(
    nasa_df,
    x="Discharge_Cycle",
    y="Capacity_Ah",
    x_label="Discharge Measurement Number",
    y_label="Measured Capacity (Ah)"
)

st.subheader("NASA Measured State of Health")

st.line_chart(
    nasa_df,
    x="Discharge_Cycle",
    y="SOH_Percent",
    x_label="Discharge Measurement Number",
    y_label="SOH (%)"
)

st.subheader("NASA Measurement Data")

st.dataframe(
    nasa_df.head(10),
    use_container_width=True
)

st.download_button(
    "Download NASA Measured Data (CSV)",
    data=nasa_df.to_csv(index=False).encode("utf-8"),
    file_name="NASA_B0005_capacity.csv",
    mime="text/csv"
)

# --------------------------------------------------
# 6. NORMALIZED DEGRADATION-TREND COMPARISON
# --------------------------------------------------

st.divider()
st.header("Simulation vs NASA: Degradation Trend")

st.write(
    "Compare the relative capacity-retention trends of the "
    "illustrative simulation and NASA B0005 measurements."
)

st.warning(
    "This is a descriptive trend comparison, not a validated prediction. "
    "NASA discharge measurement numbers and simulation cycle numbers "
    "are not assumed to be equivalent. Both records are aligned by "
    "normalized progress from 0% to 100% of their respective records. "
    "The model has not been calibrated against NASA data."
)

# Create a common progress axis for comparing curve shapes.
progress_grid = np.linspace(0, 100, 101)

nasa_progress = np.linspace(
    0,
    100,
    len(nasa_df)
)

simulation_progress = np.linspace(
    0,
    100,
    len(results)
)

nasa_soh_aligned = np.interp(
    progress_grid,
    nasa_progress,
    nasa_df["SOH_Percent"].to_numpy()
)

simulation_soh_aligned = np.interp(
    progress_grid,
    simulation_progress,
    results["SOH (%)"].to_numpy()
)

comparison_df = pd.DataFrame({
    "Progress (%)": progress_grid,
    "NASA Measured SOH (%)": nasa_soh_aligned,
    "Simulated SOH (%)": simulation_soh_aligned
})

st.subheader("Relative SOH Trend Comparison")

st.line_chart(
    comparison_df,
    x="Progress (%)",
    y=[
        "NASA Measured SOH (%)",
        "Simulated SOH (%)"
    ],
    x_label="Normalized Record Progress (%)",
    y_label="SOH (%)"
)

# Descriptive errors between the aligned curves.
errors = (
    simulation_soh_aligned
    - nasa_soh_aligned
)

mae = float(np.mean(np.abs(errors)))
rmse = float(np.sqrt(np.mean(errors ** 2)))

col1, col2 = st.columns(2)

col1.metric(
    "Aligned-Curve MAE",
    f"{mae:.2f} percentage points"
)

col2.metric(
    "Aligned-Curve RMSE",
    f"{rmse:.2f} percentage points"
)

st.caption(
    "These errors describe differences between interpolated SOH curve "
    "shapes on a normalized progress axis. They are not cycle-by-cycle "
    "prediction errors and must not be presented as validated predictive "
    "accuracy."
)

with st.expander("View aligned comparison data"):
    st.dataframe(
        comparison_df,
        use_container_width=True
    )

    st.download_button(
        "Download Aligned Comparison (CSV)",
        data=comparison_df.to_csv(index=False).encode("utf-8"),
        file_name="nasa_simulation_trend_comparison.csv",
        mime="text/csv"
    )
