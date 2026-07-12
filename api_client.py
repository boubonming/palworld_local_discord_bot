import os
import subprocess
import json
import base64
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("PALWORLD_ADMIN_PASSWORD")
API_PORT = os.getenv("PALWORLD_API_PORT")

def is_server_process_running():
    try:
        output = subprocess.check_output("tasklist", shell=True).decode("utf-8", errors="ignore")
        return "PalServer.exe" in output or "PalServer-Win64" in output
    except Exception:
        return False

def call_palworld_api(endpoint, method="POST", payload=None):
    url = f"http://127.0.0.1:{API_PORT}/v1/api/{endpoint}"
    
    auth_str = f"admin:{ADMIN_PASSWORD}"
    auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    headers = {"Authorization": f"Basic {auth_bytes}"}
    
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=10) as response:
        status_code = response.getcode()
        if method == "GET" and status_code == 200:
            return json.loads(response.read().decode("utf-8"))
        return status_code