import time
import struct
import binascii
from .utils import double_sha256, compute_merkle_root

class Block:
    def __init__(self, index, transactions, previous_hash, difficulty, nonce=0, timestamp=None, version=1):
        """
        Inisialisasi Blok.
        :param difficulty: nBits (contoh: 0x207fffff untuk testing atau 0x1e00ffff untuk mainnet)
        """
        self.index = index
        self.version = version
        self.difficulty = difficulty
        self.nonce = nonce
        self.timestamp = timestamp or int(time.time())
        self.transactions = transactions
        self.previous_hash = previous_hash
        
        # Hitung Merkle Root dari daftar transaksi
        self.merkle_root = compute_merkle_root(self.transactions)
        
        # Hitung hash awal
        self.hash = self.compute_hash()

    def serialize_header(self):
        """
        Serialisasi header blok menjadi format biner 80-byte (Standar Bitcoin).
        Format: Version(4), PrevHash(32), Merkle(32), Time(4), Bits(4), Nonce(4)
        """
        return struct.pack(
            "<I32s32sIII", 
            self.version, 
            binascii.unhexlify(self.previous_hash),
            binascii.unhexlify(self.merkle_root), 
            self.timestamp, 
            self.difficulty, 
            self.nonce
        )

    def compute_hash(self):
        """Menghasilkan Double SHA-256 Hash dalam format Hex String."""
        return double_sha256(self.serialize_header())

    def mine(self):
        """
        Proses Proof of Work (Mining) menggunakan logika nBits Target.
        """
        # 1. Konversi nBits ke Target 256-bit (Integer)
        exp = self.difficulty >> 24
        mant = self.difficulty & 0xffffff
        target = int(mant * (256 ** (exp - 3)))
        
        print(f"\n[Mining] Memulai blok {self.index}")
        print(f"[Mining] Target: {hex(target)}")
        
        # 2. Loop Nonce: Cari hash yang nilai integernya di bawah target
        # Kita gunakan int(self.hash, 16) untuk konversi hex ke angka bulat
        while int(self.hash, 16) > target:
            self.nonce += 1
            
            # Jika nonce mencapai batas 32-bit, reset dan update timestamp
            if self.nonce > 0xFFFFFFFF:
                self.nonce = 0
                self.timestamp = int(time.time())
            
            self.hash = self.compute_hash()
            
            # (Opsional) Biar gak terlalu sepi di terminal kalau difficulty tinggi
            if self.nonce % 100000 == 0:
                print(f"[Mining] Nonce saat ini: {self.nonce}", end='\r')

        print(f"\n[Mining] Berhasil! Hash: {self.hash}")
        return True

    def to_dict(self):
        """Mengubah objek blok ke dictionary untuk disimpan ke JSON atau dikirim via API."""
        return {
            "index": self.index,
            "version": self.version,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }
