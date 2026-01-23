import json
import random

sectors_data = {
    "HR": {"ops": ["Payroll", "End of Service"], "errs": ["FRM-40735", "Data Mismatch"]},
    "Finance": {"ops": ["Month Close", "Reconciliation"], "errs": ["ORA-01403", "Budget Exceeded"]},
    "Supply": {"ops": ["PO Creation", "Inventory Count"], "errs": ["APP-SQLAP-10000", "Quantity Error"]}
}

data = []
print("Generating 10k Specialized Records...")

for i in range(10000):
    sect_name = random.choice(list(sectors_data.keys()))
    op = random.choice(sectors_data[sect_name]["ops"])
    
    # محاكاة سيناريوهات معقدة (User asks about error -> Assistant solves it)
    if random.random() > 0.3: 
        err = random.choice(sectors_data[sect_name]["errs"])
        user = f"Error {err} in {sect_name} module during {op}. System stuck."
        assist = f"The error {err} in {sect_name} typically indicates missing mandatory fields in {op}. Check the transaction date and validation status."
    else:
        user = f"Best practice for {op} in Saudi Oracle {sect_name}?"
        assist = f"For {op}, ensure you follow the local statutory requirements. In {sect_name}, verify the approval workflow is active."

    data.append({
        "conversations": [
            {"from": "system", "value": "You are a Saudi Oracle ERP Expert Assistant."},
            {"from": "human", "value": user},
            {"from": "gpt", "value": assist}
        ]
    })

with open("Oracle_Saudi_Specialized_10k.jsonl", "w") as f:
    for item in data:
        f.write(json.dumps(item) + "\n")
print("Done! Oracle_Saudi_Specialized_10k.jsonl is ready.")
