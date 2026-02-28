def optimize_schedule(machines, jobs, predictions,
                      w_throughput=0.4,
                      w_risk=0.3,
                      w_cost=0.3):
    """
    Multi-objective greedy scheduling engine.

    Goals:
    - Maximize revenue (throughput)
    - Prefer healthier machines (risk-aware scheduling)
    - Penalize deadline violations (cost control)

    Weight parameters allow dynamic trade-offs and will later
    be controlled by frontend sliders (important for MECON).
    """

    # =====================================================
    # STEP 1 — Build machine availability state
    # =====================================================
    # For each machine we track:
    #   • its type
    #   • when it becomes free
    #   • its assigned job timeline

    machine_state = {}

    for m in machines:
        machine_state[m["Machine_ID"]] = {
            "type": m["Machine_Type"],   # machine capability
            "available_time": 0,         # next free time
            "schedule": []               # assigned jobs list
        }

    # =====================================================
    # STEP 2 — Build risk lookup from ML predictions ⭐
    # =====================================================
    # Convert predictions into quick lookup:
    # Machine_ID → health_score
    # This connects ML output to scheduling decisions.

    risk_map = {
        p.Machine_ID: p.health_score
        for p in predictions
    }

    # =====================================================
    # STEP 3 — Sort jobs by business importance
    # =====================================================
    # Priority logic:
    #   1. Higher Priority_Level first
    #   2. Earlier deadlines first

    jobs_sorted = sorted(
        jobs,
        key=lambda j: (-j["Priority_Level"], j["Deadline_Hours"])
    )

    # List to track jobs that couldn't be scheduled
    unassigned = []

    # =====================================================
    # STEP 4 — Main greedy assignment loop ⭐⭐⭐
    # =====================================================
    for job in jobs_sorted:

        best_machine = None
        best_score = -1e9  # initialize with very small number

        # Try placing job on every machine
        for mid, mstate in machine_state.items():

            # -------------------------------------------------
            # HARD CONSTRAINT: machine type must match
            # -------------------------------------------------
            if mstate["type"] != job["Required_Machine_Type"]:
                continue

            # Tentative schedule timing
            start_time = mstate["available_time"]
            finish_time = start_time + job["Processing_Time_Hours"]

            # -------------------------------------------------
            # Deadline penalty (soft constraint)
            # -------------------------------------------------
            # If job finishes late → apply penalty
            deadline_penalty = max(0, finish_time - job["Deadline_Hours"])

            # Get machine health from ML predictions
            # Default = 50 if prediction missing
            health = risk_map.get(mid, 50)

            # =================================================
            # MULTI-OBJECTIVE SCORING FUNCTION ⭐⭐⭐
            # =================================================
            # Higher score = better assignment
            score = (
                w_throughput * job["Revenue_Per_Job"]  # reward revenue
                + w_risk * health                      # reward healthy machines
                - w_cost * deadline_penalty * 10       # penalize lateness
            )

            # Keep the best machine choice
            if score > best_score:
                best_score = score
                best_machine = mid

        # -----------------------------------------------------
        # If no suitable machine found
        # -----------------------------------------------------
        if best_machine is None:
            unassigned.append(job["Job_ID"])
            continue

        # =====================================================
        # STEP 5 — Assign job to selected machine
        # =====================================================
        start_time = machine_state[best_machine]["available_time"]
        finish_time = start_time + job["Processing_Time_Hours"]

        machine_state[best_machine]["schedule"].append({
            "Job_ID": job["Job_ID"],
            "start": start_time,
            "end": finish_time,
        })

        # Update machine availability
        machine_state[best_machine]["available_time"] = finish_time

    # =====================================================
    # FINAL OUTPUT
    # =====================================================
    return {
        "machine_schedules": machine_state,
        "unassigned_jobs": unassigned
    }