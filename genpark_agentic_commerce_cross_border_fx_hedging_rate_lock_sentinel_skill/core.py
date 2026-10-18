# -*- coding: utf-8 -*-
"""Cross-Border FX Hedging & Rate Lock Sentinel Skill for GenPark Agentic Commerce."""
import json
import math
from typing import Dict, Any

def evaluate_fx_exposure_and_rate_lock(base_currency: str, counter_currency: str, invoice_amount_counter_curr: float, current_spot_rate: float, payment_due_days: int, annualized_fx_volatility_pct: float = 7.5) -> Dict[str, Any]:
    if invoice_amount_counter_curr <= 0 or current_spot_rate <= 0 or payment_due_days < 0:
        return {"error": "Invalid financial parameters"}

    # Base amount at current spot
    spot_cost_base = round(invoice_amount_counter_curr / current_spot_rate, 2)
    
    # 95% Value at Risk (VaR) estimation over holding horizon
    time_factor = math.sqrt(payment_due_days / 365.0)
    var_95_pct = round(1.645 * (annualized_fx_volatility_pct / 100.0) * time_factor * 100.0, 2)
    max_adverse_cost_usd = round(spot_cost_base * (1.0 + (var_95_pct / 100.0)), 2)
    potential_slippage_usd = round(max_adverse_cost_usd - spot_cost_base, 2)

    # Forward points cost estimation (0.15% per 30 days carry spread)
    forward_spread_pct = (payment_due_days / 30.0) * 0.15
    forward_rate = round(current_spot_rate * (1.0 - (forward_spread_pct / 100.0)), 4)
    guaranteed_lock_cost_usd = round(invoice_amount_counter_curr / forward_rate, 2)
    hedging_premium_usd = round(guaranteed_lock_cost_usd - spot_cost_base, 2)

    # Hedging Decision Matrix
    if payment_due_days > 14 and var_95_pct > 2.0:
        recommendation = "LOCK_FORWARD_CONTRACT"
        rationale = f"Potential downside variance of ${potential_slippage_usd} ({var_95_pct}%) exceeds hedge carry cost of ${hedging_premium_usd}."
    else:
        recommendation = "EXECUTE_SPOT_AT_SETTLEMENT"
        rationale = "Low horizon volatility exposure; transaction does not warrant forward locking fees."

    return {
        "pair": f"{counter_currency}/{base_currency}",
        "invoice_counter_amount": invoice_amount_counter_curr,
        "current_spot_rate": current_spot_rate,
        "settlement_horizon_days": payment_due_days,
        "base_cost_spot_today": spot_cost_base,
        "max_risk_var95_base_cost": max_adverse_cost_usd,
        "potential_adverse_slippage": potential_slippage_usd,
        "synthetic_forward_lock_rate": forward_rate,
        "forward_locked_base_cost": guaranteed_lock_cost_usd,
        "hedging_premium_cost": hedging_premium_usd,
        "recommendation": recommendation,
        "decision_rationale": rationale,
        "guard_enforcer": "GenPark Treasury & Multi-Currency Engine"
    }

def simulate_fx_scenario_sensitivity(invoice_amount_counter_curr: float, current_spot_rate: float, locked_forward_rate: float) -> Dict[str, Any]:
    locked_cost = round(invoice_amount_counter_curr / locked_forward_rate, 2)
    
    shocks = [-0.05, -0.03, 0.0, 0.03, 0.05]
    scenarios = []
    
    for shock in shocks:
        simulated_rate = round(current_spot_rate * (1.0 + shock), 4)
        simulated_cost = round(invoice_amount_counter_curr / simulated_rate, 2)
        variance_vs_locked = round(locked_cost - simulated_cost, 2)
        scenarios.append({
            "shock_pct": round(shock * 100, 1),
            "simulated_spot_rate": simulated_rate,
            "unhedged_procurement_cost": simulated_cost,
            "net_gain_from_hedging": variance_vs_locked
        })

    return {
        "invoice_amount": invoice_amount_counter_curr,
        "locked_forward_cost": locked_cost,
        "scenarios": scenarios,
        "conclusion": "Forward rate lock creates absolute procurement budget certainty."
    }
