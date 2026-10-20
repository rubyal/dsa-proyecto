"""Descarga un rango de fechas de NYC 311 (Azure Open Datasets, Safety) a s3.

Uso (desde la raiz del repo):
    python scripts/descargar_nyc_safety.py --desde 2023-01-01 --hasta 2023-12-31

"""
import argparse
from datetime import datetime
from pathlib import Path

import adlfs
import pyarrow.dataset as ds
import pyarrow.parquet as pq

CUENTA = "azureopendatastorage"
RUTA = "citydatacontainer/Safety/Release/city=NewYorkCity"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--desde", default="2023-01-01", help="AAAA-MM-DD (incluida)")
    p.add_argument("--hasta", default="2023-12-31", help="AAAA-MM-DD (incluida)")
    p.add_argument("--salida", default="data/raw/nyc_311_safety.parquet")
    a = p.parse_args()

    desde = datetime.fromisoformat(a.desde)
    hasta = datetime.fromisoformat(a.hasta).replace(hour=23, minute=59, second=59)

    fs = adlfs.AzureBlobFileSystem(account_name=CUENTA, anon=True)  # acceso publico, sin credenciales
    dataset = ds.dataset(RUTA, filesystem=fs, format="parquet")
    print("Columnas disponibles:", dataset.schema.names)

    filtro = (ds.field("dateTime") >= desde) & (ds.field("dateTime") <= hasta)
    tabla = dataset.to_table(filter=filtro)
    print(f"Filas entre {a.desde} y {a.hasta}: {tabla.num_rows:,}")

    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(tabla, salida)
    print(f"Guardado en {salida} ({salida.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
