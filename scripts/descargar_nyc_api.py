import argparse
import os
import time

import pandas as pd
import requests

URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGINA = 50_000


def pedir(params, headers, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(URL, params=params, headers=headers, timeout=180)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  reintento {i + 1}/{intentos}: {e}")
            time.sleep(5 * (i + 1))
    raise SystemExit("El API no respondió; no se guarda nada.")


def descargar_anio(anio, headers):
    params_base = {
        "$select": "borough, date_trunc_ymd(created_date) as dia, "
                   "complaint_type, count(*) as n",
        "$where": f"created_date >= '{anio}-01-01T00:00:00' "
                  f"AND created_date < '{anio + 1}-01-01T00:00:00'",
        "$group": "borough, dia, complaint_type",
        "$order": "dia, borough, complaint_type",
        "$limit": PAGINA,
    }
    partes, offset = [], 0
    while True:
        datos = pedir({**params_base, "$offset": offset}, headers)
        if not datos:
            break
        partes.append(pd.DataFrame(datos))
        offset += PAGINA
        print(f"  {anio}: {offset:,} filas agregadas leídas")
        if len(datos) < PAGINA:
            break
        time.sleep(0.5)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def main(anios, salida):
    headers = {}
    token = os.getenv("SOCRATA_APP_TOKEN")  # opcional
    if token:
        headers["X-App-Token"] = token

    todos = []
    for anio in anios:
        print(f"Año {anio}...")
        df = descargar_anio(anio, headers)
        if df.empty:
            print(f"  {anio}: sin filas")
            continue
        print(f"  {anio}: {len(df):,} filas, {int(df['n'].astype(int).sum()):,} solicitudes")
        todos.append(df)

    if not todos:
        raise SystemExit("La consulta no devolvió filas; no se guarda nada.")

    df = pd.concat(todos, ignore_index=True)
    df["dia"] = pd.to_datetime(df["dia"])
    df["n"] = df["n"].astype(int)
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    df.to_parquet(salida, index=False)
    print(f"Guardado {len(df):,} filas en {salida}")
    print(f"Total de solicitudes: {df['n'].sum():,}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--anios", type=int, nargs="+", default=[2022, 2023, 2024, 2025])
    p.add_argument("--salida", default="data/raw/nyc311_diario_borough_tipo.parquet")
    a = p.parse_args()
    main(a.anios, a.salida)