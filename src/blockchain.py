import json
import os
import hashlib
import binascii
import time  # Ditambahkan untuk menghitung waktu blok
from .block import Block
from .transaction import Transaction

class Blockchain:
    def __init__(self, port=5000):
        self.db_path = f'data/blockchain_{port}.json'
        self.chain, self.mempool, self.nodes = [], [], set()

        # --- KONFIGURASI DIFFICULTY OTOMATIS ---
        self.difficulty_bits = 0x1e0ffff0  # Start di level SEDANG
        self.target_block_time = 15        # Target: 1 blok per 15 detik
        self.adjustment_interval = 10      # Evaluasi setiap 10 blok
        # ---------------------------------------

        self.mining_reward = 50 * 100_000_000 # 50 BTC dalam Satoshis

        if not os.path.exists('data'):
            os.makedirs('data')

        if not self.load():
            self.create_genesis_block()

    def get_current_difficulty(self):
        """Logika Penyesuaian Kesulitan Otomatis (Retargeting)"""
        # Kita lakukan evaluasi setiap kali mencapai interval (blok ke-10, 20, dst)
        if len(self.chain) > 0 and len(self.chain) % self.adjustment_interval == 0:
            # Ambil blok di awal interval dan blok terakhir
            first_block = self.chain[-self.adjustment_interval]
            last_block = self.chain[-1]
            
            # Hitung waktu yang sebenarnya dihabiskan
            actual_time = last_block['timestamp'] - first_block['timestamp']
            expected_time = self.target_block_time * self.adjustment_interval

            print(f"--- Evaluasi Jaringan: Waktu Aktual {actual_time}s vs Target {expected_time}s ---")

            # Jika terlalu cepat (S24 Ultra kamu terlalu overpower), naikkan kesulitan
            if actual_time < (expected_time / 2):
                # Mengurangi target (membuat mining lebih sulit)
                self.difficulty_bits -= 0x00100000 
                print(f"--- DIFFICULTY NAIK: {hex(self.difficulty_bits)} ---")
            
            # Jika terlalu lambat, turunkan kesulitan
            elif actual_time > (expected_time * 2):
                # Menambah target (membuat mining lebih mudah)
                self.difficulty_bits += 0x00100000
                print(f"--- DIFFICULTY TURUN: {hex(self.difficulty_bits)} ---")
        
        return self.difficulty_bits

    def mine_mempool(self, miner_address):
        """Packing transaksi ke dalam blok baru dengan difficulty dinamis."""
        # 1. Ambil difficulty terbaru sebelum mining
        current_diff = self.get_current_difficulty()
        
        coinbase = Transaction("0", miner_address, self.mining_reward).to_dict()
        valid_txs = [coinbase] + self.mempool

        last_block = self.chain[-1]
        last_hash = last_block['hash'] if isinstance(last_block, dict) else last_block.hash

        # 2. Gunakan difficulty hasil perhitungan otomatis
        new_block = Block(len(self.chain), valid_txs, last_hash, current_diff)

        print(f"Mining Block #{new_block.index} dengan Difficulty {hex(current_diff)}...")
        if new_block.mine():
            self.chain.append(new_block)
            self.mempool = []
            self.save()
            return new_block
        return None

    # --- SISA FUNGSI DIBAWAH TETAP SAMA ---
    def bits_to_target(self, bits):
        exp = bits >> 24
        mant = bits & 0xffffff
        return mant * (256 ** (exp - 3))

    def hash160_from_pubkey(self, pubkey_hex):
        from .wallet import Wallet
        temp_wallet = Wallet(private_key_hex=None)
        pub_bytes = binascii.unhexlify(pubkey_hex)
        sha = hashlib.sha256(pub_bytes).digest()
        h160 = hashlib.new('ripemd160', sha).digest()
        payload = b'\x00' + h160
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return temp_wallet._base58_encode(payload + checksum)

    def get_utxos(self, address):
        unspent = []
        spent_txs = set()
        for block in reversed(self.chain):
            txs = block['transactions'] if isinstance(block, dict) else block.transactions
            for tx in txs:
                tx_id = tx.get('signature', 'coinbase_' + str(block['index'] if isinstance(block, dict) else block.index))
                if tx['receiver'] == address:
                    if tx_id not in spent_txs: unspent.append(tx)
                if tx['sender_public_key'] != "0": spent_txs.add(tx.get('signature'))
        return unspent

    def get_balance(self, address):
        utxos = self.get_utxos(address)
        return sum(tx['amount'] for tx in utxos)

    def create_genesis_block(self):
        print("Membuat Genesis Block...")
        genesis_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        tx = Transaction("0", genesis_addr, self.mining_reward).to_dict()
        genesis = Block(0, [tx], "00" * 32, self.difficulty_bits)
        genesis.mine()
        self.chain.append(genesis)
        self.save()

    def add_transaction(self, tx):
        if not tx.is_valid(): return False, "Signature tidak valid"
        sender_address = self.hash160_from_pubkey(tx.sender_public_key)
        if self.get_balance(sender_address) < tx.amount: return False, "Saldo tidak mencukupi"
        self.mempool.append(tx.to_dict())
        return True, "Berhasil masuk mempool"

    def save(self):
        try:
            with open(self.db_path, 'w') as f:
                chain_data = [b.to_dict() if hasattr(b, 'to_dict') else b for b in self.chain]
                json.dump(chain_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Save error: {e}"); return False

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self.chain = json.load(f); return True
            except Exception as e:
                print(f"Load error: {e}"); return False
        return False
