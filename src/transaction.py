import struct
import binascii
from .utils import double_sha256

class Transaction:
    def __init__(self, sender_public_key, receiver_address, amount_satoshi, signature=None):
        self.sender_public_key = sender_public_key
        self.receiver = receiver_address
        self.amount = int(amount_satoshi)
        self.signature = signature

    def to_bytes(self):
        """Serialisasi transaksi ke bytes."""
        spk_b = self.sender_public_key.encode()
        recv_b = self.receiver.encode()
        return struct.pack(f"<I{len(spk_b)}sI{len(recv_b)}sQ",
                           len(spk_b), spk_b, len(recv_b), recv_b, self.amount)

    def compute_hash(self):
        """Menghasilkan hash transaksi (format HEX string untuk sinkron ke wallet)."""
        # Wallet.py kamu minta hexlify untuk sign/verify
        raw_hash = double_sha256(self.to_bytes())
        # Jika double_sha256 sudah return string, langsung pakai. 
        # Jika return bytes, kita hexlify.
        if isinstance(raw_hash, bytes):
            return binascii.hexlify(raw_hash).decode()
        return raw_hash

    def sign_transaction(self, wallet):
        """Menandatangani transaksi dengan wallet."""
        if wallet.public_key_hex != self.sender_public_key:
            return False
        
        # Ambil hash (hex string) dan kirim ke wallet.sign
        tx_hash = self.compute_hash()
        self.signature = wallet.sign(tx_hash)
        return True

    def is_valid(self):
        """Verifikasi validitas transaksi."""
        if self.sender_public_key == "0": 
            return True
        if not self.signature: 
            return False
            
        from .wallet import Wallet
        # Memanggil static method verify dari wallet.py kamu
        return Wallet.verify(self.sender_public_key, self.signature, self.compute_hash())

    def to_dict(self):
        return {
            "sender_public_key": self.sender_public_key, 
            "receiver": self.receiver,
            "amount": self.amount, 
            "signature": self.signature
        }
