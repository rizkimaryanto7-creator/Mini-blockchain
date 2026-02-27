import binascii, hashlib
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError

class Wallet:
    B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def __init__(self, private_key_hex=None, version_byte=b'\x00'):
        self.version_byte = version_byte
        if private_key_hex:
            self._private_key = SigningKey.from_string(binascii.unhexlify(private_key_hex), curve=SECP256k1)
        else:
            self._private_key = SigningKey.generate(curve=SECP256k1)
        
        self._public_key = self._private_key.get_verifying_key()
        self.public_key_hex = binascii.hexlify(self._public_key.to_string()).decode()
        self.address = self._generate_address(self._public_key.to_string())

    def _generate_address(self, pubkey_bytes):
        # SHA256 -> RIPEMD160
        sha256_h = hashlib.sha256(pubkey_bytes).digest()
        h160 = hashlib.new('ripemd160', sha256_h).digest()
        # Base58Check: Add Version + Checksum
        payload = self.version_byte + h160
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return self._base58_encode(payload + checksum)

    def _base58_encode(self, b):
        n = int.from_bytes(b, 'big')
        res = ""
        while n > 0:
            n, r = divmod(n, 58)
            res = self.B58_ALPHABET[r] + res
        pad = 0
        for byte in b:
            if byte == 0: pad += 1
            else: break
        return (self.B58_ALPHABET[0] * pad) + res

    @property
    def private_key_hex(self):
        return binascii.hexlify(self._private_key.to_string()).decode()

    def sign(self, message_hash):
        return binascii.hexlify(self._private_key.sign_deterministic(
            binascii.unhexlify(message_hash), hashfunc=hashlib.sha256)).decode()

    @staticmethod
    def verify(public_key_hex, signature_hex, message_hash):
        try:
            vk = VerifyingKey.from_string(binascii.unhexlify(public_key_hex), curve=SECP256k1)
            return vk.verify(binascii.unhexlify(signature_hex), binascii.unhexlify(message_hash), hashfunc=hashlib.sha256)
        except: return False
