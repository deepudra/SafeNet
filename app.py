from flask import Flask, render_template, request, jsonify, session
from web3 import Web3
import hashlib

app = Flask(__name__)
app.secret_key = "safenet_pro_secure_key_99"

# --- BLOCKCHAIN CONFIG ---
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# Paste your details from Remix here:
CONTRACT_ADDRESS = "0x9d28068B0E3fD5cf81d9ffA711683d4077C8631D"
CONTRACT_ABI = [
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_url",
				"type": "string"
			},
			{
				"internalType": "bytes32",
				"name": "_codeHash",
				"type": "bytes32"
			},
			{
				"internalType": "string",
				"name": "_name",
				"type": "string"
			}
		],
		"name": "reportThreat",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_url",
				"type": "string"
			}
		],
		"name": "verifyThreat",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "allUrlList",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "balances",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getAllUrls",
		"outputs": [
			{
				"internalType": "string[]",
				"name": "",
				"type": "string[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_url",
				"type": "string"
			}
		],
		"name": "getVerifiers",
		"outputs": [
			{
				"internalType": "address[]",
				"name": "",
				"type": "address[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "hasVerified",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "threats",
		"outputs": [
			{
				"internalType": "string",
				"name": "url",
				"type": "string"
			},
			{
				"internalType": "bytes32",
				"name": "codeHash",
				"type": "bytes32"
			},
			{
				"internalType": "address",
				"name": "reporter",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "reporterName",
				"type": "string"
			},
			{
				"internalType": "bool",
				"name": "isBlacklisted",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# --- USER DATABASE (Match these to your Ganache account addresses) ---
USERS = {
    "admin": {"password": "123", "address": w3.eth.accounts[0]},
    "user1": {"password": "123", "address": w3.eth.accounts[1]},
    "user2": {"password": "123", "address": w3.eth.accounts[2]}
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = USERS.get(data.get('username'))
    if user and user['password'] == data.get('password'):
        session['user'] = data.get('username')
        session['address'] = user['address']
        return jsonify({"status": "success", "username": session['user'], "address": session['address']})
    return jsonify({"status": "error"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route('/threats', methods=['GET'])
def get_threats():
    try:
        urls = contract.functions.getAllUrls().call()
        threat_list = []
        for url in urls:
            # threats(url) returns [url, hash, reporter_addr, reporter_name, isBlacklisted]
            data = contract.functions.threats(url).call()
            # getVerifiers(url) returns address[]
            verifiers = contract.functions.getVerifiers(url).call()
            
            threat_list.append({
                "url": data[0],
                "reporter": data[2],
                "reporterName": data[3],
                "verifiers": verifiers,
                "isBlacklisted": data[4]
            })
        return jsonify(threat_list)
    except Exception as e:
        return jsonify([])

@app.route('/report', methods=['POST'])
def report():
    if 'address' not in session: return jsonify({"error": "Auth failed"}), 401
    url = request.json.get('url')
    code_hash = w3.to_bytes(hexstr=hashlib.sha256(url.encode()).hexdigest())
    
    tx = contract.functions.reportThreat(url, code_hash, session['user']).transact({'from': session['address']})
    w3.eth.wait_for_transaction_receipt(tx)
    return jsonify({"status": "success"})

@app.route('/verify', methods=['POST'])
def verify():
    if 'address' not in session: return jsonify({"error": "Auth failed"}), 401
    url = request.json.get('url')
    tx = contract.functions.verifyThreat(url).transact({'from': session['address']})
    w3.eth.wait_for_transaction_receipt(tx)
    return jsonify({"status": "success"})

@app.route('/stats', methods=['GET'])
def stats():
    addr = session.get('address', '0x0')
    bal = contract.functions.balances(addr).call() if addr != '0x0' else 0
    return jsonify({"balance": bal, "address": addr})

if __name__ == '__main__':
    app.run(debug=True)