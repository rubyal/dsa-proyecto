"""Etapa de limpieza (DVC): diario por borough/tipo -> semanal por borough.

Entrada : data/raw/nyc311_diario_borough_tipo.parquet
Salida  : data/processed/nyc311_semanal_borough.parquet
          reports/limpieza_resumen.json

Decisiones tomadas en el EDA (notebooks/01_eda_calidad_api.ipynb):
  - Se normalizan los tipos (minúsculas/espacios): 239 -> 224 tipos.
  - Se excluye el borough 'Unspecified' (0,11 %).
  - Se descartan semanas parciales (semanas lunes-domingo completas).
  - Los tipos con < MIN_SOLICITUDES_TIPO solicitudes se agrupan en 'otros'.
  - Se conserva `n_noise_residencial` para comparar el modelo con y sin ese tipo.
"""
import json
from pathlib import Path

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data/raw/nyc311_diario_borough_tipo.parquet"
SALIDA = RAIZ / "data/processed/nyc311_semanal_borough.parquet"
RESUMEN = RAIZ / "reports/limpieza_resumen.json"

MIN_SOLICITUDES_TIPO = 1_000

# PROVISIONAL: la lista final de "no urgentes" la define el equipo.
NO_URGENTES = {
    "illegal parking", "blocked driveway", "abandoned vehicle",
    "derelict vehicles", "dirty condition", "missed collection",
    "noise - residential", "noise - street/sidewalk", "noise - commercial",
    "noise - vehicle", "noise",
}
NOISE_RESIDENCIAL = "noise - residential"


def main() -> None:
    df = pd.read_parquet(ENTRADA)
    resumen = {"filas_entrada": int(len(df)), "solicitudes_entrada": int(df["n"].sum())}

    # 1. Normalización
    df["complaint_type"] = df["complaint_type"].str.lower().str.strip()
    df["borough"] = df["borough"].str.strip().str.title()
    df["dia"] = pd.to_datetime(df["dia"])
    resumen["tipos_normalizados"] = int(df["complaint_type"].nunique())

    # 2. Excluir Unspecified
    antes = df["n"].sum()
    df = df[df["borough"].str.lower() != "unspecified"]
    resumen["solicitudes_excluidas_unspecified"] = int(antes - df["n"].sum())

    # 3. Duplicados por clave -> sumar
    df = df.groupby(["borough", "dia", "complaint_type"], as_index=False)["n"].sum()

    # 4. Tipos raros -> 'otros'
    tot_tipo = df.groupby("complaint_type")["n"].sum()
    raros = tot_tipo[tot_tipo < MIN_SOLICITUDES_TIPO].index
    resumen["tipos_agrupados_en_otros"] = int(len(raros))
    df["complaint_type"] = df["complaint_type"].where(~df["complaint_type"].isin(raros), "otros")

    # 5. Marcas
    df["es_no_urgente"] = df["complaint_type"].isin(NO_URGENTES)
    df["es_noise_res"] = df["complaint_type"].eq(NOISE_RESIDENCIAL)
    df["n_no_urg"] = df["n"].where(df["es_no_urgente"], 0)
    df["n_noise_res"] = df["n"].where(df["es_noise_res"], 0)

    # 6. Semana lunes-domingo, solo completas
    df["semana"] = df["dia"].dt.to_period("W-SUN").dt.start_time
    dias_por_semana = df.groupby("semana")["dia"].nunique()
    completas = dias_por_semana[dias_por_semana == 7].index
    resumen["semanas_parciales_descartadas"] = int((dias_por_semana < 7).sum())
    df = df[df["semana"].isin(completas)]

    sem = (df.groupby(["borough", "semana"], as_index=False)
             .agg(n_total=("n", "sum"), n_no_urgentes=("n_no_urg", "sum"),
                  n_noise_residencial=("n_noise_res", "sum"))
             .sort_values(["borough", "semana"]).reset_index(drop=True))
    sem["pct_no_urgentes"] = sem["n_no_urgentes"] / sem["n_total"]

    # 7. Calendario y feriados federales (semana con al menos un feriado)
    fer = USFederalHolidayCalendar().holidays(sem["semana"].min(),
                                              sem["semana"].max() + pd.Timedelta(days=6))
    sem_fer = set(fer.to_period("W-SUN").start_time)
    sem["semana_con_feriado"] = sem["semana"].isin(sem_fer).astype(int)
    sem["mes"] = sem["semana"].dt.month
    sem["semana_anio"] = sem["semana"].dt.isocalendar().week.astype(int)
    sem["anio"] = sem["semana"].dt.year

    # 8. Validaciones
    assert not sem.duplicated(["borough", "semana"]).any(), "duplicados borough-semana"
    assert sem[["n_total", "n_no_urgentes"]].ge(0).all().all(), "conteos negativos"
    assert (sem["n_no_urgentes"] <= sem["n_total"]).all(), "no urgentes > total"
    assert sem.groupby("borough")["semana"].count().nunique() == 1, "boroughs con distinto nº de semanas"

    resumen.update(filas_salida=int(len(sem)), boroughs=sorted(sem["borough"].unique().tolist()),
                   semanas_por_borough=int(sem.groupby("borough")["semana"].count().iloc[0]))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    RESUMEN.parent.mkdir(parents=True, exist_ok=True)
    sem.to_parquet(SALIDA, index=False)
    RESUMEN.write_text(json.dumps(resumen, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(resumen, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
