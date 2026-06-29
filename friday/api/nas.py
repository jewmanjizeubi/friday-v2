"""
Friday — Monitoring NAS Synology
Récupère l'état du NAS via l'API DSM
"""

import requests
from fastapi import APIRouter
from config.settings import settings

router = APIRouter(prefix="/nas", tags=["nas"])

NAS_HOST = "192.168.1.233"
NAS_PORT = 5000


def _login() -> str | None:
    """Login DSM et retourne le SID"""
    try:
        r = requests.post(
            f"http://{NAS_HOST}:{NAS_PORT}/webapi/auth.cgi",
            data={
                "api": "SYNO.API.Auth",
                "version": "3",
                "method": "login",
                "account": settings.NAS_USERNAME,
                "passwd": settings.NAS_PASSWORD,
                "session": "FridayMonitoring",
                "format": "sid"
            },
            timeout=5
        )
        data = r.json()
        if data.get("success"):
            return data["data"]["sid"]
    except Exception as e:
        print(f"[NAS] Login error: {e}")
    return None

def _logout(sid: str):
    """Déconnexion"""
    try:
        requests.get(
            f"http://{NAS_HOST}:{NAS_PORT}/webapi/auth.cgi",
            params={
                "api": "SYNO.API.Auth",
                "version": "1",
                "method": "logout",
                "session": "FridayMonitoring",
                "_sid": sid
            },
            timeout=3
        )
    except Exception:
        pass


def _api_call(sid: str, api: str, method: str, version: str = "1", **extra) -> dict:
    """Appel générique à l'API DSM"""
    try:
        params = {
            "api": api,
            "version": version,
            "method": method,
            "_sid": sid,
            **extra
        }
        r = requests.get(
            f"http://{NAS_HOST}:{NAS_PORT}/webapi/entry.cgi",
            params=params,
            timeout=5
        )
        return r.json().get("data", {})
    except Exception as e:
        return {"error": str(e)}


@router.get("/status")
def get_nas_status():
    """Retourne l'état complet du NAS"""
    sid = _login()
    if not sid:
        return {"error": "Login NAS échoué", "online": False}

    try:
        # Infos système
        system = _api_call(sid, "SYNO.Core.System", "info", version="3")

        # État des volumes
        volumes = _api_call(sid, "SYNO.Storage.CGI.Storage", "load_info", version="1")

        # Utilisation CPU/RAM
        utilisation = _api_call(sid, "SYNO.Core.System.Utilization", "get", version="1")

        # Formatage
        result = {
            "online": True,
            "hostname": system.get("hostname", "N/A"),
            "model": system.get("model", "N/A"),
            "dsm_version": system.get("firmware_ver", "N/A"),
            "uptime_seconds": system.get("up_time", 0),
            "temperature": system.get("sys_temp", "N/A"),
        }

        # Volumes
        if "volumes" in volumes:
            result["volumes"] = []
            for v in volumes["volumes"]:
                size_total = int(v.get("size", {}).get("total", 0))
                size_used = int(v.get("size", {}).get("used", 0))
                result["volumes"].append({
                    "id": v.get("id"),
                    "status": v.get("status"),
                    "total_gb": round(size_total / 1e9, 1),
                    "used_gb": round(size_used / 1e9, 1),
                    "free_gb": round((size_total - size_used) / 1e9, 1),
                    "percent": round((size_used / size_total * 100), 1) if size_total else 0
                })

        # Disques
        if "disks" in volumes:
            result["disks"] = []
            for d in volumes["disks"]:
                result["disks"].append({
                    "name": d.get("id"),
                    "model": d.get("model", "N/A"),
                    "status": d.get("status"),
                    "smart_status": d.get("smart_status", "N/A"),
                    "temp": d.get("temp"),
                    "size_gb": round(int(d.get("size_total", 0)) / 1e9, 1)
                })

        # Utilisation
        if utilisation:
            result["cpu_percent"] = utilisation.get("cpu", {}).get("user_load", 0)
            mem = utilisation.get("memory", {})
            result["memory_percent"] = mem.get("real_usage", 0)

        return result

    finally:
        _logout(sid)


@router.get("/health")
def health():
    """Test rapide de connexion au NAS"""
    sid = _login()
    if sid:
        _logout(sid)
        return {"online": True}
    return {"online": False}
