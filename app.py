import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from simulation import run_simulation, calculate_kpis, compare_scenarios


st.set_page_config(
    page_title="Warehouse Digital Twin Simulation",
    layout="wide"
)


# -----------------------------
# Helper Functions
# -----------------------------

def show_workflow_stage(stage_name, status, metric):
    stage_name = stage_name.replace("\n", "<br>")

    if status == "Bottleneck":
        background_color = "#FDE2E2"
        border_color = "#E74C3C"
        status_color = "#C0392B"
    elif status == "High Utilisation":
        background_color = "#FFF3CD"
        border_color = "#F1C40F"
        status_color = "#B7950B"
    else:
        background_color = "#EAF7EA"
        border_color = "#2E7D32"
        status_color = "#2E7D32"

    html = (
        f'<div style="'
        f'border: 2px solid {border_color};'
        f'background-color: {background_color};'
        f'border-radius: 14px;'
        f'padding: 18px 12px;'
        f'text-align: center;'
        f'min-height: 150px;'
        f'display: flex;'
        f'flex-direction: column;'
        f'justify-content: center;'
        f'align-items: center;'
        f'box-sizing: border-box;'
        f'">'
        f'<div style="font-size: 22px; font-weight: 700; line-height: 1.2; color: #2E3440; margin-bottom: 14px;">'
        f'{stage_name}'
        f'</div>'
        f'<div style="font-size: 14px; font-weight: 500; color: {status_color}; margin-bottom: 10px;">'
        f'{status}'
        f'</div>'
        f'<div style="font-size: 13px; font-weight: 700; color: #2E3440;">'
        f'{metric}'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)




def clean_waiting_index(waiting_series):
    cleaned = waiting_series.copy()
    cleaned.index = (
        cleaned.index
        .str.replace("_wait", "", regex=False)
        .str.replace("_", " ", regex=False)
        .str.title()
    )
    return cleaned


# -----------------------------
# Header
# -----------------------------

st.title("Warehouse Digital Twin Simulation")
st.subheader("Receiving Workflow Optimisation")

st.write(
    """
    This project simulates a warehouse receiving workflow using a discrete-event 
    simulation model. It analyses queue time, cycle time, throughput, resource 
    utilisation, and bottleneck behaviour under different operational scenarios.
    """
)

st.markdown(
    """
    **Workflow model:** Supplier Arrival → Unloading → Document Check → Quality Inspection → Storage → Transport → Completed
    """
)


# -----------------------------
# Sidebar Inputs
# -----------------------------

st.sidebar.header("Baseline Scenario Parameters")

num_shipments = st.sidebar.slider(
    "Number of Shipments",
    min_value=10,
    max_value=200,
    value=50,
    step=10
)

arrival_interval = st.sidebar.slider(
    "Arrival Interval (minutes)",
    min_value=1,
    max_value=20,
    value=5
)

unloading_staff = st.sidebar.slider(
    "Unloading Staff",
    min_value=1,
    max_value=5,
    value=2
)

document_staff = st.sidebar.slider(
    "Document / OCR Check Staff",
    min_value=1,
    max_value=5,
    value=1
)

inspection_staff = st.sidebar.slider(
    "Quality Inspection Staff",
    min_value=1,
    max_value=5,
    value=1
)

storage_staff = st.sidebar.slider(
    "Storage Staff",
    min_value=1,
    max_value=5,
    value=1
)

transport_staff = st.sidebar.slider(
    "Transport Staff",
    min_value=1,
    max_value=5,
    value=2
)

st.sidebar.divider()

st.sidebar.header("Improved Scenario Parameters")

improved_inspection_staff = st.sidebar.slider(
    "Improved Inspection Staff",
    min_value=1,
    max_value=5,
    value=2
)

improved_transport_staff = st.sidebar.slider(
    "Improved Transport Staff",
    min_value=1,
    max_value=5,
    value=2
)

run_button = st.sidebar.button("Run Digital Twin Simulation")


# -----------------------------
# Main App Logic
# -----------------------------

if run_button:
    baseline_df, baseline_utilisation = run_simulation(
        num_shipments=num_shipments,
        arrival_interval=arrival_interval,
        unloading_staff=unloading_staff,
        document_staff=document_staff,
        inspection_staff=inspection_staff,
        storage_staff=storage_staff,
        transport_staff=transport_staff,
        random_seed=42
    )

    baseline_kpis, baseline_waiting = calculate_kpis(baseline_df)

    improved_df, improved_utilisation = run_simulation(
        num_shipments=num_shipments,
        arrival_interval=arrival_interval,
        unloading_staff=unloading_staff,
        document_staff=document_staff,
        inspection_staff=improved_inspection_staff,
        storage_staff=storage_staff,
        transport_staff=improved_transport_staff,
        random_seed=42
    )

    improved_kpis, improved_waiting = calculate_kpis(improved_df)
    comparison = compare_scenarios(baseline_kpis, improved_kpis)

    baseline_waiting_clean = clean_waiting_index(baseline_waiting)
    improved_waiting_clean = clean_waiting_index(improved_waiting)

    st.divider()

    # -----------------------------
    # KPI Cards
    # -----------------------------

    st.subheader("Baseline Scenario KPI Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Completed Shipments", baseline_kpis["total_completed"])
    col2.metric("Avg Cycle Time", f'{baseline_kpis["avg_cycle_time"]} min')
    col3.metric("Avg Waiting Time", f'{baseline_kpis["avg_waiting_time"]} min')
    col4.metric("Throughput", f'{baseline_kpis["throughput_per_hour"]} / hour')
    col5.metric("Bottleneck", baseline_kpis["bottleneck_stage"])

    st.divider()

    # -----------------------------
    # Digital Twin Workflow Visual
    # -----------------------------

    st.subheader("Digital Twin Workflow Status")

    max_wait_stage = baseline_kpis["bottleneck_stage"]

    utilisation_lookup = dict(
        zip(
            baseline_utilisation["resource"],
            baseline_utilisation["utilisation_percent"]
        )
    )

    workflow_cols = st.columns(5)

    stage_info = [
    ("Unloading", "Unloading"),
    ("Document\nCheck", "Document Check"),
    ("Inspection", "Inspection"),
    ("Storage", "Storage"),
    ("Transport", "Transport")
    ]

    for i, (display_name, utilisation_key) in enumerate(stage_info):
        utilisation_value = utilisation_lookup.get(utilisation_key, 0)

        if display_name == max_wait_stage:
            status = "Bottleneck"
        elif utilisation_value >= 85:
            status = "High Utilisation"
        else:
            status = "Stable"

        with workflow_cols[i]:
            show_workflow_stage(
                display_name,
                status,
                f"Utilisation: {utilisation_value}%"
            )

    st.markdown(
    """
    <div style="
        margin-top: 18px;
        font-size: 14px;
        color: #6B7280;
    ">
        <b>Note:</b> Red indicates the main bottleneck based on average waiting time. 
        Yellow indicates high resource utilisation.
    </div>
    """,
    unsafe_allow_html=True
    )

    st.divider()

    # -----------------------------
    # Scenario Comparison
    # -----------------------------

    st.subheader("Scenario Comparison: Baseline vs Improved")

    comparison_col1, comparison_col2, comparison_col3 = st.columns(3)

    comparison_col1.metric(
        "Cycle Time Reduction",
        f'{comparison["cycle_time_reduction_percent"]}%'
    )

    comparison_col2.metric(
        "Waiting Time Reduction",
        f'{comparison["waiting_time_reduction_percent"]}%'
    )

    comparison_col3.metric(
        "Throughput Increase",
        f'{comparison["throughput_increase_percent"]}%'
    )

    scenario_summary = pd.DataFrame([
        {
            "Scenario": "Baseline",
            "Inspection Staff": inspection_staff,
            "Transport Staff": transport_staff,
            "Avg Cycle Time": baseline_kpis["avg_cycle_time"],
            "Avg Waiting Time": baseline_kpis["avg_waiting_time"],
            "Throughput / Hour": baseline_kpis["throughput_per_hour"],
            "Bottleneck": baseline_kpis["bottleneck_stage"]
        },
        {
            "Scenario": "Improved",
            "Inspection Staff": improved_inspection_staff,
            "Transport Staff": improved_transport_staff,
            "Avg Cycle Time": improved_kpis["avg_cycle_time"],
            "Avg Waiting Time": improved_kpis["avg_waiting_time"],
            "Throughput / Hour": improved_kpis["throughput_per_hour"],
            "Bottleneck": improved_kpis["bottleneck_stage"]
        }
    ])

    st.dataframe(scenario_summary, use_container_width=True)

    fig_summary = px.bar(
        scenario_summary,
        x="Scenario",
        y=["Avg Cycle Time", "Avg Waiting Time", "Throughput / Hour"],
        barmode="group",
        title="Scenario KPI Comparison"
    )

    st.plotly_chart(fig_summary, use_container_width=True)

    st.divider()

    # -----------------------------
    # Waiting Time Chart
    # -----------------------------

    st.subheader("Bottleneck Analysis: Average Waiting Time by Stage")

    waiting_comparison = pd.DataFrame({
        "Stage": baseline_waiting_clean.index,
        "Baseline": baseline_waiting_clean.values,
        "Improved": improved_waiting_clean.values
    })

    waiting_long = waiting_comparison.melt(
        id_vars="Stage",
        var_name="Scenario",
        value_name="Average Waiting Time"
    )

    fig_waiting = px.bar(
        waiting_long,
        x="Stage",
        y="Average Waiting Time",
        color="Scenario",
        barmode="group",
        title="Average Waiting Time by Workflow Stage"
    )

    st.plotly_chart(fig_waiting, use_container_width=True)

    st.divider()

    # -----------------------------
    # Utilisation Chart
    # -----------------------------

    st.subheader("Resource Utilisation Analysis")

    utilisation_comparison = baseline_utilisation.merge(
        improved_utilisation,
        on="resource",
        suffixes=("_baseline", "_improved")
    )

    utilisation_chart_data = pd.DataFrame({
        "Resource": utilisation_comparison["resource"],
        "Baseline": utilisation_comparison["utilisation_percent_baseline"],
        "Improved": utilisation_comparison["utilisation_percent_improved"]
    })

    utilisation_long = utilisation_chart_data.melt(
        id_vars="Resource",
        var_name="Scenario",
        value_name="Utilisation (%)"
    )

    fig_utilisation = px.bar(
        utilisation_long,
        x="Resource",
        y="Utilisation (%)",
        color="Scenario",
        barmode="group",
        title="Resource Utilisation Comparison"
    )

    st.plotly_chart(fig_utilisation, use_container_width=True)

    st.dataframe(utilisation_comparison, use_container_width=True)

    st.divider()

    # -----------------------------
    # Cycle Time Chart
    # -----------------------------

    st.subheader("Cycle Time per Shipment")

    cycle_time_data = pd.DataFrame({
        "Shipment ID": baseline_df["shipment_id"],
        "Baseline": baseline_df["total_cycle_time"],
        "Improved": improved_df["total_cycle_time"]
    })

    cycle_time_long = cycle_time_data.melt(
        id_vars="Shipment ID",
        var_name="Scenario",
        value_name="Cycle Time"
    )

    fig_cycle = px.line(
        cycle_time_long,
        x="Shipment ID",
        y="Cycle Time",
        color="Scenario",
        markers=True,
        title="Cycle Time per Shipment"
    )

    st.plotly_chart(fig_cycle, use_container_width=True)

    st.divider()

    # -----------------------------
    # Detailed Results + CSV Export
    # -----------------------------

    st.subheader("Detailed Simulation Results")

    tab1, tab2, tab3 = st.tabs(
        ["Baseline Results", "Improved Results", "Scenario Summary"]
    )

    with tab1:
        st.dataframe(baseline_df, use_container_width=True)

        baseline_csv = baseline_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Baseline Results as CSV",
            data=baseline_csv,
            file_name="baseline_simulation_results.csv",
            mime="text/csv"
        )

    with tab2:
        st.dataframe(improved_df, use_container_width=True)

        improved_csv = improved_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Improved Results as CSV",
            data=improved_csv,
            file_name="improved_simulation_results.csv",
            mime="text/csv"
        )

    with tab3:
        st.dataframe(scenario_summary, use_container_width=True)

        summary_csv = scenario_summary.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Scenario Summary as CSV",
            data=summary_csv,
            file_name="scenario_summary.csv",
            mime="text/csv"
        )

    st.divider()

    # -----------------------------
    # Optimisation Insight
    # -----------------------------

    st.subheader("Optimisation Insight")

    baseline_bottleneck = baseline_kpis["bottleneck_stage"]
    improved_bottleneck = improved_kpis["bottleneck_stage"]

    if comparison["cycle_time_reduction_percent"] > 0:
        st.success(
            f"""
            The improved scenario reduces average cycle time by 
            **{comparison["cycle_time_reduction_percent"]}%** and average waiting time by 
            **{comparison["waiting_time_reduction_percent"]}%**.

            In the baseline scenario, the main bottleneck is **{baseline_bottleneck}**. 
            After increasing the selected resource capacity, the bottleneck changes to 
            **{improved_bottleneck}**.

            This suggests that capacity adjustment can improve material flow efficiency 
            and reduce queue build-up in the receiving workflow.
            """
        )
    else:
        st.warning(
            f"""
            The selected improvement does not significantly reduce average cycle time. 
            The baseline bottleneck is **{baseline_bottleneck}**, so the selected resource 
            change may not directly address the main constraint.

            Further improvement should focus on the stage with the highest waiting time 
            and highest utilisation.
            """
        )

else:
    st.info("Adjust the parameters on the left and click **Run Digital Twin Simulation**.")