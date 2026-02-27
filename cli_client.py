import requests
import json
import os
from src.wallet import Wallet
from src.transaction import Transaction

NODE_URL = "http://localhost:3000"

def create_wallet():
    wallet = Wallet()
    wallet_data = {
        "private_key": wallet.private_key_hex,
        "public_key": wallet.public_key_hex,
        "address": wallet.address
    }
    with open("my_wallet.json", "w") as f:
        json.dump(wallet_data, f, indent=4)
    print(f"--- Wallet Created ---\nAddress: {wallet.address}\nSaved to: my_wallet.json")

def get_balance(address):
    response = requests.get(f"{NODE_URL}/balance?address={address}")
    print(f"Balance: {response.json()['balance_satoshi']} Satoshis")

def send_coin(receiver, amount):
    if not os.path.exists("my_wallet.json"):
        print("Error: No wallet found. Create one first.")
        return

    with open("my_wallet.json", "r") as f:
        w_data = json.load(f)

    # Load Wallet & Buat Transaksi
    wallet = Wallet(private_key_hex=w_data['private_key'])
    tx = Transaction(wallet.public_key_hex, receiver, amount)
    
    # Sign Transaksi
    tx.sign_transaction(wallet)
    
    # Kirim ke Node
    response = requests.post(f"{NODE_URL}/transactions/new", json=tx.to_dict())
    print(response.json())

if __name__ == "__main__":
    print("1. Create Wallet\n2. Check Balance\n3. Send Coins\n4. Mine Mempool")
    choice = input("Choice: ")

    if choice == "1":
        create_wallet()
    elif choice == "2":
        addr = input("Enter Address: ")
        get_balance(addr)
    elif choice == "3":
        to = input("Receiver Address: ")
        amt = int(input("Amount (Satoshi): "))
        send_coin(to, amt)
    elif choice == "4":
        addr = input("Miner Reward Address: ")
        res = requests.get(f"{NODE_URL}/mine?address={addr}")
        print(res.json())
