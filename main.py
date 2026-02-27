import sys
from flask import Flask, jsonify, request
from src.blockchain import Blockchain
from src.transaction import Transaction
from argparse import ArgumentParser

app = Flask(__name__)

@app.route('/mine', methods=['GET'])
def mine():
    miner_address = request.args.get('address')
    if not miner_address:
        return jsonify({"error": "Miner address is required"}), 400
    
    block = blockchain.mine_mempool(miner_address)
    if block:
        return jsonify({
            "message": "New Block Mined",
            "block": block.to_dict()
        }), 200
    return jsonify({"message": "Mining failed"}), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender_public_key', 'receiver', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    tx = Transaction(
        values['sender_public_key'],
        values['receiver'],
        values['amount'],
        values['signature']
    )
    
    success, msg = blockchain.add_transaction(tx)
    if not success:
        return jsonify({"message": msg}), 400

    return jsonify({"message": f"Transaction will be added to Block {len(blockchain.chain)}"}), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': [b.to_dict() if hasattr(b, 'to_dict') else b for b in blockchain.chain],
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    balance = blockchain.get_balance(address)
    return jsonify({"address": address, "balance_satoshi": balance}), 200

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    blockchain = Blockchain(port=port)
    app.run(host='0.0.0.0', port=port)
