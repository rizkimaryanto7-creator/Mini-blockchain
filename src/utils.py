import hashlib
import json

def double_sha256(data):
    """Standar Bitcoin hash256: SHA256(SHA256(data))"""
    if isinstance(data, str): data = data.encode()
    return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()

def compute_merkle_root(transactions):
    """Merkle Root menggunakan Double SHA-256 (Deterministik)"""
    if not transactions:
        return double_sha256("empty")
    
    # Hash dasar dari setiap transaksi (binary-like hashing)
    hashes = [double_sha256(json.dumps(tx, sort_keys=True)) for tx in transactions]
    
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        new_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i+1]
            new_level.append(double_sha256(combined))
        hashes = new_level
    return hashes[0]
