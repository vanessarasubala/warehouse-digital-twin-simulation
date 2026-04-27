# Warehouse Digital Twin Simulation for Receiving Workflow Optimisation

This project is a Python-based digital twin simulation that models a simplified warehouse receiving, storage, retrieval, and transport workflow. It is designed to analyse bottlenecks, queue time, throughput, resource utilisation, and processing time under different operational scenarios.

The project was developed using **Python, SimPy, Pandas, Streamlit, and Plotly**.

---

## Project Objective

Warehouse receiving operations often involve multiple sequential stages, such as unloading, document checking, quality inspection, storage, and transport. Delays in one stage can create queue build-up, increase cycle time, and reduce overall material flow efficiency.

This project aims to simulate the warehouse receiving workflow and evaluate how changes in resource capacity affect operational performance. The simulation helps identify bottlenecks and provides optimisation insights to support warehouse layout and capacity planning decisions.

---

## Digital Twin Concept

This project represents a digital twin because it creates a digital simulation of a physical warehouse workflow.

The model includes:

- A digital representation of warehouse receiving operations
- Discrete-event simulation logic using SimPy
- Adjustable operational parameters
- Scenario-based performance comparison
- Bottleneck and resource utilisation analysis
- Optimisation insights for decision-making

Instead of only displaying static data, the dashboard simulates how materials move through each workflow stage and how operational changes affect overall performance.

---

## Workflow Model

The simulated workflow follows this process:

```text
Supplier Arrival
→ Unloading
→ Document / OCR Check
→ Quality Inspection
→ Storage
→ Retrieval / Transport
→ Completed