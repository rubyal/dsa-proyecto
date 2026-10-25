import argparse
import time

import pandas as pd
import requests

URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
META = "https://data.cityofnewyork.us/api/views/erm2-nwe9.json"
NO_URGENTES_EJEMPLO = []  # se define después en el EDA


def get(params, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(URL, params=params, timeout=180)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  reintento {i + 1}/{intentos}: {e}")
            time.sleep(5 * (i + 1))
    raise SystemExit("El API no respondió.")


def rango(desde, hasta):
    return (f"created_date >= '{desde}-01-01T00:00:00' "
            f"AND created_date < '{hasta + 1}-01-01T00:00:00'")


def contar(where):
    return int(get({"$select": "count(*) as n", "$where": where})[0]["n"])


def main(desde, hasta):
    w = rango(desde, hasta)
    print(f"=== VALIDACIÓN NYC 311 | {desde} a {hasta} ===\n")

    # 1. Columnas del dataset
    print("1. COLUMNAS")
    meta = requests.get(META, timeout=60).json()
    cols = [c["fieldName"] for c in meta["columns"] if not c["fieldName"].startswith(":@")]
    print(f"   {len(cols)} columnas")
    necesarias = ["created_date", "closed_date", "due_date", "borough",
                  "complaint_type", "descriptor", "agency", "status"]
    for c in necesarias:
        print(f"   {'OK ' if c in cols else 'FALTA'} {c}")

    # 2. Total y por año
    print("\n2. REGISTROS POR AÑO")
    por_anio = get({"$select": "date_extract_y(created_date) as anio, count(*) as n",
                    "$where": w, "$group": "anio", "$order": "anio"})
    total = 0
    for f in por_anio:
        print(f"   {f['anio']}: {int(f['n']):,}")
        total += int(f["n"])
    print(f"   TOTAL: {total:,}")

    # 3. Por borough
    print("\n3. REGISTROS POR BOROUGH")
    por_b = get({"$select": "borough, count(*) as n", "$where": w,
                 "$group": "borough", "$order": "n DESC"})
    for f in por_b:
        pct = int(f["n"]) / total * 100
        print(f"   {f.get('borough', '(nulo)'):<15} {int(f['n']):>10,}  {pct:5.2f}%")

    # 4. Nulos en campos clave
    print("\n4. NULOS EN CAMPOS CLAVE (en el rango)")
    for c in ["created_date", "borough", "complaint_type", "closed_date", "due_date"]:
        n = contar(f"({w}) AND {c} IS NULL")
        print(f"   {c:<15} {n:>10,}  {n / total * 100:6.2f}%")

    # 5. Tipos de queja
    print("\n5. TIPOS DE QUEJA")
    tipos = get({"$select": "complaint_type, count(*) as n", "$where": w,
                 "$group": "complaint_type", "$order": "n DESC", "$limit": 500})
    print(f"   {len(tipos)} tipos distintos. Los 25 más frecuentes:")
    for f in tipos[:25]:
        print(f"   {f['complaint_type'][:45]:<45} {int(f['n']):>10,}")

    # 6. Conteo mensual (huecos y estabilidad)
    print("\n6. CONTEO MENSUAL")
    mens = get({"$select": "date_extract_y(created_date) as a, "
                           "date_extract_m(created_date) as m, count(*) as n",
                "$where": w, "$group": "a, m", "$order": "a, m", "$limit": 1000})
    dm = pd.DataFrame(mens).astype(int)
    esperados = (hasta - desde + 1) * 12
    print(f"   {len(dm)} meses con datos (esperados: {esperados})")
    print(f"   mínimo mensual: {dm.n.min():,} | máximo: {dm.n.max():,} | "
          f"mediana: {int(dm.n.median()):,}")
    print(dm.pivot(index="a", columns="m", values="n").to_string())

    # 7. Estimación de filas de la tabla agregada
    print("\n7. ESTIMACIÓN DE FILAS DE LA TABLA AGREGADA")
    muestra = get({
        "$select": "borough, date_trunc_ymd(created_date) as dia, "
                   "complaint_type, count(*) as n",
        "$where": "created_date >= '2023-06-01T00:00:00' "
                  "AND created_date < '2023-07-01T00:00:00'",
        "$group": "borough, dia, complaint_type",
        "$limit": 50000,
    })
    n_mes = len(muestra)
    meses = (hasta - desde + 1) * 12
    print(f"   junio 2023 agregado: {n_mes:,} filas")
    print(f"   estimado para {meses} meses: ~{n_mes * meses:,} filas")
    print(f"   suma de n en la muestra: {sum(int(f['n']) for f in muestra):,}")
    semanas = (hasta - desde + 1) * 52
    print(f"   tabla semanal por borough: ~{semanas * 5:,} filas "
          f"({semanas} semanas x 5 boroughs)")

    # 8. Registro de ejemplo
    print("\n8. EJEMPLO DE REGISTRO CERRADO")
    ej = get({"$where": f"({w}) AND closed_date IS NOT NULL", "$limit": 1})
    if ej:
        for k, v in ej[0].items():
            print(f"   {k}: {v}")

    print("\n=== FIN: no se descargó ni guardó ningún dato ===")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--desde", type=int, default=2022)
    p.add_argument("--hasta", type=int, default=2025)
    a = p.parse_args()
    main(a.desde, a.hasta)
