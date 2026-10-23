"""
cache_olap.py — Pre-cacheia dados OLAP (Receita Federal) para o Raio-X.

Busca dados do Observatorio Sebrae para nivel nacional e 27 estados.
Salva em data/rf_cache.json para carregamento rapido no dashboard.
APIs IBGE/BCB sao publicas e rapidas, nao precisam de cache.

Uso: python scripts/cache_olap.py
"""
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

OLAP = "https://apiv2-observatorio.sebrae.com.br/tesseract/data.jsonrecords"
TOKEN = os.getenv("OBSERVATORIO_TOKEN", "f38eaf2bd57685d925db8db0a91979db")
RF_MAND = "Registration%20Status=2&Sebrae%20Commercial%20Company%20Indicator=1"

ESTADOS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def fetch_json(url, timeout=30):
    try:
        req = Request(url, headers={"User-Agent": "PIPPA-RaioX/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERRO: {e}")
        return None


def rf_url(drilldowns, territory_filter=""):
    url = f"{OLAP}?token={TOKEN}&cube=RF&drilldowns={drilldowns}&measures=Establishments&{RF_MAND}"
    if territory_filter:
        url += "&" + territory_filter
    return url


def cache_nacional():
    print("\n[1] Nacional — porte")
    data = fetch_json(rf_url("Sebrae Size"))
    return data.get("data", []) if data else []


def cache_nacional_setor():
    print("[2] Nacional — setor")
    data = fetch_json(rf_url("Sector"))
    return data.get("data", []) if data else []


def cache_estados_porte():
    print("[3] Estados — porte")
    data = fetch_json(rf_url("Sebrae Size,State"))
    return data.get("data", []) if data else []


def cache_estados_setor():
    print("[4] Estados — setor")
    data = fetch_json(rf_url("Sector,State"))
    return data.get("data", []) if data else []


def main():
    print(f"Cache OLAP Raio-X — {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Token: {'***' + TOKEN[-4:] if TOKEN else 'MISSING'}")

    cache = {
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nacional_porte": cache_nacional(),
        "nacional_setor": cache_nacional_setor(),
        "estados_porte": cache_estados_porte(),
        "estados_setor": cache_estados_setor(),
    }

    total = sum(len(v) for v in cache.values() if isinstance(v, list))
    print(f"\n  Total: {total} registros coletados")

    out = DATA_DIR / "rf_cache.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  Salvo: {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
