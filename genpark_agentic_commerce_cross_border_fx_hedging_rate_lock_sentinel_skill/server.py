# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Cross-Border FX Hedging & Rate Lock Sentinel Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "evaluate_fx_exposure_and_rate_lock",
    "description": "Evaluate purchasing currency exposure risk against historic volatility and recommend optimal forward rate lock vs spot execution.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "base_currency": {
          "type": "string",
          "description": "e.g. USD"
        },
        "counter_currency": {
          "type": "string",
          "description": "e.g. EUR, JPY, GBP"
        },
        "invoice_amount_counter_curr": {
          "type": "number"
        },
        "current_spot_rate": {
          "type": "number"
        },
        "payment_due_days": {
          "type": "integer"
        },
        "annualized_fx_volatility_pct": {
          "type": "number",
          "description": "e.g. 8.5 for 8.5%"
        }
      },
      "required": [
        "base_currency",
        "counter_currency",
        "invoice_amount_counter_curr",
        "current_spot_rate",
        "payment_due_days"
      ]
    }
  },
  {
    "name": "simulate_fx_scenario_sensitivity",
    "description": "Simulate procurement budget variance under +/- 3% and +/- 5% FX currency shocks.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "invoice_amount_counter_curr": {
          "type": "number"
        },
        "current_spot_rate": {
          "type": "number"
        },
        "locked_forward_rate": {
          "type": "number"
        }
      },
      "required": [
        "invoice_amount_counter_curr",
        "current_spot_rate",
        "locked_forward_rate"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-agentic-commerce-cross-border-fx-hedging-rate-lock-sentinel-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-agentic-commerce-cross-border-fx-hedging-rate-lock-sentinel-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "evaluate_fx_exposure_and_rate_lock",
            "arguments": {
                "base_currency": "USD",
                "counter_currency": "EUR",
                "invoice_amount_counter_curr": 50000.0,
                "current_spot_rate": 1.085,
                "payment_due_days": 45
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: evaluate_fx_exposure_and_rate_lock")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
