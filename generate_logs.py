import hashlib
import json
from datetime import datetime

def find_nonce(data_to_hash: str, target_prefix: str = "000000") -> tuple[int, str]:
    nonce = 0
    # Pre-encode static data to speed up loop
    encoded_base = data_to_hash.encode() 
    
    while True:
        # Concatenate nonce and hash
        h = hashlib.sha256(encoded_base + str(nonce).encode()).hexdigest()
        if h.startswith(target_prefix):
            return nonce, h
        nonce += 1
        if nonce % 10_000_000 == 0:
            print(f"Iteration: {nonce}")

def create_transaction(amount, notes, to_user, from_user, prev_hash, balance):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_data = f"{timestamp}{from_user}{to_user}{amount}{notes}{prev_hash}"
    
    print(f"Mining block (6 zeros) for: {notes}...")
    nonce, current_hash = find_nonce(base_data)
    
    return {
        "Timestamp": timestamp,
        "From": from_user,
        "To": to_user,
        "Amount": amount,
        "PropID": "N/A",
        "Balance": balance,
        "Notes": notes,
        "PrevHash": current_hash,
        "Nonce": str(nonce)
    }

# --- GENERATE YOUR DATA ---
genesis_prev_hash = "0"*64
chain = []

t1 = create_transaction(0, "Genesis Block", "Treasury", "Treasury", genesis_prev_hash, 0)
chain.append(t1)

# Block 2
t2 = create_transaction(0, "Initial Funding", "Treasury", "Treasury", t1['PrevHash'], 0)
chain.append(t2)

t3 = create_transaction(0, "Testing", "Treasury", "Treasury", t2["PrevHash"], 0)
chain.append(t3)

print("\n--- Copy these rows to Google Sheets ---")
print(json.dumps(chain, indent=2))