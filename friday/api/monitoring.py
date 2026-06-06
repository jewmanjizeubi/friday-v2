"""
Friday — Monitoring système
CPU, RAM, température, Docker, uptime
"""

import psutil
import subprocess
import docker
from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def _get_uptime() -> str:
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        parts = []
        if days:
            parts.append(f"{days}j")
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{mins}m")
        return " ".join(parts)
    except Exception:
        return "N/A"


def _get_cpu_temp() -> float | None:
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True, text=True, timeout=2
        )
        temp_str = result.stdout.strip().replace("temp=", "").replace("'C", "")
        return float(temp_str)
    except Exception:
        try:
            temps = psutil.sensors_temperatures()
            for key in ["cpu_thermal", "coretemp"]:
                if key in temps and temps[key]:
                    return temps[key][0].current
        except Exception:
            return None


def _get_docker_containers() -> list:
    try:
        client = docker.from_env()
        containers = []
        for c in client.containers.list(all=True):
            ports = []
            for port, bindings in (c.ports or {}).items():
                if bindings:
                    ports.append(f"{bindings[0]['HostPort']}→{port}")
            containers.append({
                "name": c.name,
                "status": c.status,
                "running": c.status == "running",
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "ports": ", ".join(ports)
            })
        return containers
    except Exception:
        return []


@router.get("")
@router.get("/")
def get_monitoring():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu": {
            "percent": cpu_percent,
            "temp_celsius": _get_cpu_temp()
        },
        "memory": {
            "percent": mem.percent,
            "used_gb": round(mem.used / 1e9, 1),
            "total_gb": round(mem.total / 1e9, 1)
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / 1e9, 1),
            "total_gb": round(disk.total / 1e9, 1)
        },
        "uptime": _get_uptime(),
        "docker": _get_docker_containers(),
        "alerts": []
    }


@router.get("/health")
def health():
    return {"status": "ok"}
