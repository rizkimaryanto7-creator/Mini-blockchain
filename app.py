import sys
import os
import time
from flask import Flask, jsonify, request, render_template
from src.blockchain import Blockchain
from src.transaction import Transaction
from argparse import ArgumentParser

app = Flask(__name__)

# --- UTILITY FUNCTIONS ---
def get_attr(obj, attr, default=None):
    """Helper untuk ambil atribut baik dari Object maupun Dict"""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mine', methods=['GET'])
def mine():
    miner_address = request.args.get('address')
    if not miner_address:
        return jsonify({"error": "Alamat penambang wajib diisi"}), 400

    try:
        # Proses mining memaketkan Coinbase + Mempool
        block = blockchain.mine_mempool(miner_address)

        if block:
            # FIX: Akses atribut object secara aman
            diff = get_attr(block, 'difficulty_bits', blockchain.difficulty_bits)
            txs = get_attr(block, 'transactions', [])

            return jsonify({
                "status": "success",
                "message": "Blok baru berhasil ditambang!",
                "block_index": get_attr(block, 'index'),
                "hash": get_attr(block, 'hash'),
                "transactions_count": len(txs),
                "merkle_root": get_attr(block, 'merkle_root'),
                "nonce": get_attr(block, 'nonce'),
                "difficulty_used": hex(diff)
            }), 200
    except Exception as e:
        print(f"DEBUG MINING ERROR: {e}") # Muncul di terminal S24 kamu
        return jsonify({"error": f"Mining terhenti: {str(e)}"}), 500

    return jsonify({"message": "Mining gagal atau mempool kosong"}), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    if not values:
        return jsonify({"error": "Data JSON tidak ditemukan"}), 400

    required = ['sender_public_key', 'receiver', 'amount', 'signature']
    if not all(k in values for k in required):
        return jsonify({"error": "Data tidak lengkap"}), 400

    tx = Transaction(
        sender_public_key=values['sender_public_key'],
        receiver_address=values['receiver'],
        amount_satoshi=values['amount'],
        signature=values['signature']
    )

    success, msg = blockchain.add_transaction(tx)
    if not success:
        return jsonify({"error": msg}), 400

    return jsonify({"message": f"Berhasil! Transaksi masuk Mempool. Target blok: {len(blockchain.chain)}"}), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    try:
        # Konversi object ke dict agar bisa di-serialize ke JSON
        chain_data = []
        for b in blockchain.chain:
            if hasattr(b, 'to_dict'):
                chain_data.append(b.to_dict())
            else:
                chain_data.append(vars(b)) # Fallback ke vars jika to_dict absen
                
        return jsonify({
            'chain': chain_data,
            'length': len(blockchain.chain),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Address diperlukan"}), 400

    balance = blockchain.get_balance(address)
    return jsonify({
        "address": address,
        "balance_satoshi": balance,
        "balance_btc": balance / 100_000_000
    }), 200

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    if not blockchain.chain:
        return jsonify({"error": "Blockchain offline"}), 500

    try:
        last_block = blockchain.chain[-1]
        total_satoshi = 0
        
        for b in blockchain.chain:
            # FIX: Penanganan dinamis untuk Object vs Dict
            txs = get_attr(b, 'transactions', [])
            if txs:
                first_tx = txs[0]
                # Coinbase amount access
                total_satoshi += get_attr(first_tx, 'amount', 0)

        return jsonify({
            "total_supply": total_satoshi / 100_000_000,
            "total_blocks": len(blockchain.chain),
            "pending_tx": len(blockchain.mempool),
            "difficulty": hex(blockchain.difficulty_bits),
            "last_block_hash": get_attr(last_block, 'hash')
        }), 200
    except Exception as e:
        return jsonify({"error": f"Stats error: {str(e)}"}), 503

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=3000, type=int)
    args = parser.parse_args()

    blockchain = Blockchain(port=args.port)

    print(f"\n🔥 TERMUX RIZKI NODE ONLINE 🔥")
    print(f"Running on port: {args.port}\n")

    app.run(host='0.0.0.0', port=args.port, threaded=True, debug=False)
