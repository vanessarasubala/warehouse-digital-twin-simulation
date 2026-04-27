import simpy
import pandas as pd
import random


def run_simulation(
    num_shipments=50,
    arrival_interval=5,
    unloading_staff=2,
    document_staff=1,
    inspection_staff=1,
    storage_staff=1,
    transport_staff=2,
    unloading_time_range=(8, 15),
    document_time_range=(3, 7),
    inspection_time_range=(10, 20),
    storage_time_range=(5, 10),
    transport_time_range=(8, 18),
    random_seed=42
):
    random.seed(random_seed)

    results = []
    resource_busy_time = {
        "Unloading": 0,
        "Document Check": 0,
        "Inspection": 0,
        "Storage": 0,
        "Transport": 0
    }

    env = simpy.Environment()

    unloading = simpy.Resource(env, capacity=unloading_staff)
    document_check = simpy.Resource(env, capacity=document_staff)
    inspection = simpy.Resource(env, capacity=inspection_staff)
    storage = simpy.Resource(env, capacity=storage_staff)
    transport = simpy.Resource(env, capacity=transport_staff)

    def process_shipment(env, shipment_id):
        arrival_time = env.now

        shipment_data = {
            "shipment_id": f"SHP-{shipment_id:03d}",
            "arrival_time": arrival_time
        }

        # 1. Unloading
        with unloading.request() as request:
            yield request
            unloading_start = env.now
            unloading_wait = unloading_start - arrival_time
            unloading_time = random.randint(*unloading_time_range)
            resource_busy_time["Unloading"] += unloading_time
            yield env.timeout(unloading_time)
            unloading_end = env.now

        # 2. Document / OCR Check
        with document_check.request() as request:
            yield request
            document_start = env.now
            document_wait = document_start - unloading_end
            document_time = random.randint(*document_time_range)
            resource_busy_time["Document Check"] += document_time
            yield env.timeout(document_time)
            document_end = env.now

        # 3. Quality Inspection
        with inspection.request() as request:
            yield request
            inspection_start = env.now
            inspection_wait = inspection_start - document_end
            inspection_time = random.randint(*inspection_time_range)
            resource_busy_time["Inspection"] += inspection_time
            yield env.timeout(inspection_time)
            inspection_end = env.now

        # 4. Storage
        with storage.request() as request:
            yield request
            storage_start = env.now
            storage_wait = storage_start - inspection_end
            storage_time = random.randint(*storage_time_range)
            resource_busy_time["Storage"] += storage_time
            yield env.timeout(storage_time)
            storage_end = env.now

        # 5. Retrieval / Transport
        with transport.request() as request:
            yield request
            transport_start = env.now
            transport_wait = transport_start - storage_end
            transport_time = random.randint(*transport_time_range)
            resource_busy_time["Transport"] += transport_time
            yield env.timeout(transport_time)
            transport_end = env.now

        total_cycle_time = transport_end - arrival_time

        shipment_data.update({
            "unloading_start": unloading_start,
            "unloading_end": unloading_end,
            "document_start": document_start,
            "document_end": document_end,
            "inspection_start": inspection_start,
            "inspection_end": inspection_end,
            "storage_start": storage_start,
            "storage_end": storage_end,
            "transport_start": transport_start,
            "transport_end": transport_end,

            "unloading_time": unloading_time,
            "document_time": document_time,
            "inspection_time": inspection_time,
            "storage_time": storage_time,
            "transport_time": transport_time,

            "unloading_wait": unloading_wait,
            "document_wait": document_wait,
            "inspection_wait": inspection_wait,
            "storage_wait": storage_wait,
            "transport_wait": transport_wait,

            "total_cycle_time": total_cycle_time
        })

        results.append(shipment_data)

    def shipment_arrival_generator(env):
        for shipment_id in range(1, num_shipments + 1):
            env.process(process_shipment(env, shipment_id))
            yield env.timeout(arrival_interval)

    env.process(shipment_arrival_generator(env))
    env.run()

    df = pd.DataFrame(results)

    simulation_end_time = df["transport_end"].max()

    resource_capacity = {
        "Unloading": unloading_staff,
        "Document Check": document_staff,
        "Inspection": inspection_staff,
        "Storage": storage_staff,
        "Transport": transport_staff
    }

    utilisation_data = []

    for resource_name, busy_time in resource_busy_time.items():
        capacity = resource_capacity[resource_name]
        available_time = simulation_end_time * capacity
        utilisation = (busy_time / available_time) * 100 if available_time > 0 else 0

        utilisation_data.append({
            "resource": resource_name,
            "busy_time": round(busy_time, 2),
            "available_time": round(available_time, 2),
            "utilisation_percent": round(utilisation, 2)
        })

    utilisation_df = pd.DataFrame(utilisation_data)

    return df, utilisation_df


def calculate_kpis(df):
    wait_columns = [
        "unloading_wait",
        "document_wait",
        "inspection_wait",
        "storage_wait",
        "transport_wait"
    ]

    avg_waiting_by_stage = df[wait_columns].mean()

    bottleneck_column = avg_waiting_by_stage.idxmax()
    bottleneck_stage = bottleneck_column.replace("_wait", "").replace("_", " ").title()

    total_completed = len(df)
    avg_cycle_time = df["total_cycle_time"].mean()
    avg_waiting_time = df[wait_columns].sum(axis=1).mean()
    throughput = total_completed / df["transport_end"].max() * 60

    kpis = {
        "total_completed": total_completed,
        "avg_cycle_time": round(avg_cycle_time, 2),
        "avg_waiting_time": round(avg_waiting_time, 2),
        "throughput_per_hour": round(throughput, 2),
        "bottleneck_stage": bottleneck_stage
    }

    return kpis, avg_waiting_by_stage


def compare_scenarios(baseline_kpis, improved_kpis):
    cycle_time_reduction = (
        (baseline_kpis["avg_cycle_time"] - improved_kpis["avg_cycle_time"])
        / baseline_kpis["avg_cycle_time"]
    ) * 100

    waiting_time_reduction = (
        (baseline_kpis["avg_waiting_time"] - improved_kpis["avg_waiting_time"])
        / baseline_kpis["avg_waiting_time"]
    ) * 100

    throughput_increase = (
        (improved_kpis["throughput_per_hour"] - baseline_kpis["throughput_per_hour"])
        / baseline_kpis["throughput_per_hour"]
    ) * 100

    comparison = {
        "cycle_time_reduction_percent": round(cycle_time_reduction, 2),
        "waiting_time_reduction_percent": round(waiting_time_reduction, 2),
        "throughput_increase_percent": round(throughput_increase, 2)
    }

    return comparison