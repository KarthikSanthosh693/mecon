def simulate_maintenance(predictions):
    """
    Compares two maintenance strategies:

    Scenario A — Immediate preventive maintenance
    Scenario B — Delayed (run-to-failure) maintenance

    Uses ML failure probability to estimate expected impact.

    This directly satisfies MECON Phase 4 requirements.
    """

    results = []

    # =====================================================
    # COST PARAMETERS (can be tuned later)
    # =====================================================
    PREVENTIVE_COST = 500              # cost of planned maintenance
    CORRECTIVE_COST = 2000             # cost if machine fails
    DOWNTIME_COST_PER_HOUR = 100       # production loss cost/hour
    REPLACEMENT_COST = 5000            # (reserved for future use)

    # Loop through each machine prediction
    for p in predictions:

        # ML-predicted probability of failure
        failure_prob = p.failure_probability

        # =====================================================
        # SCENARIO A — Immediate Maintenance ⭐
        # =====================================================
        # Assumption:
        # If we maintain now → small planned downtime
        immediate_downtime = 2  # hours (controlled shutdown)

        # Total cost = preventive cost + downtime cost
        immediate_cost = PREVENTIVE_COST + (
            immediate_downtime * DOWNTIME_COST_PER_HOUR
        )

        # Estimated production loss during planned stop
        # (50 units/hour assumed throughput)
        immediate_prod_loss = immediate_downtime * 50

        # =====================================================
        # SCENARIO B — Delayed Maintenance ⭐⭐⭐
        # =====================================================
        # Expected failure probability from ML
        expected_failure = failure_prob

        # Expected downtime (probabilistic)
        # If failure occurs → assume 6 hours outage
        delayed_downtime = 6 * expected_failure

        # Expected corrective cost weighted by failure risk
        delayed_cost = (
            expected_failure * CORRECTIVE_COST
            + delayed_downtime * DOWNTIME_COST_PER_HOUR
        )

        # Higher production loss assumed during breakdown
        # (80 units/hour because failures are more disruptive)
        delayed_prod_loss = delayed_downtime * 80

        # =====================================================
        # STORE RESULTS
        # =====================================================
        results.append({
            "Machine_ID": p.Machine_ID,

            # Preventive strategy results
            "immediate": {
                "cost": round(immediate_cost, 2),
                "downtime": round(immediate_downtime, 2),
                "production_loss": round(immediate_prod_loss, 2),
            },

            # Run-to-failure strategy results
            "delayed": {
                "cost": round(delayed_cost, 2),
                "downtime": round(delayed_downtime, 2),
                "production_loss": round(delayed_prod_loss, 2),
            },
        })

    return results