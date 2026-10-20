"""Start / stop / status for the streaming VM, from the LiveVision app.

A Cloud Run function (`./gcp.sh control-deploy`) that stays reachable while
the VM is stopped, so the app can see that it's stopped and start it. Its
service account may only get / start / stop obs-irl, and every call needs the
bearer token gcp.sh generated (the app gets it via `./gcp.sh companion`).

  GET  /         -> {"status": "RUNNING" | "TERMINATED" | ..., "ip", "machine_type"}
  POST /start    -> starts the VM (returns at once; poll GET for RUNNING)
  POST /stop     -> stops it
"""
import hmac
import os

import functions_framework
from google.cloud import compute_v1

PROJECT = os.environ["PROJECT"]
ZONE = os.environ["ZONE"]
NAME = os.environ["NAME"]
TOKEN = os.environ["CONTROL_TOKEN"]

instances = compute_v1.InstancesClient()


def _status() -> dict:
    vm = instances.get(project=PROJECT, zone=ZONE, instance=NAME)
    ip = ""
    for nic in vm.network_interfaces:
        for ac in nic.access_configs:
            ip = ip or ac.nat_i_p
    return {"name": NAME, "status": vm.status, "ip": ip,
            "machine_type": vm.machine_type.rsplit("/", 1)[-1]}


@functions_framework.http
def control(request):
    if not hmac.compare_digest(request.headers.get("Authorization", ""), f"Bearer {TOKEN}"):
        return {"error": "unauthorized"}, 401
    action = request.path.strip("/")
    if action in ("start", "stop"):
        if request.method != "POST":
            return {"error": "POST only"}, 405
        # don't wait for the operation: a start takes ~30 s and the app polls
        getattr(instances, action)(project=PROJECT, zone=ZONE, instance=NAME)
        return {"ok": True, "action": action, **_status()}
    if action:
        return {"error": "unknown action"}, 404
    return _status()
