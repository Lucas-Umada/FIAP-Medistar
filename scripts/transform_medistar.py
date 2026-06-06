from pathlib import Path
from datetime import date
import time

import pandas as pd
import requests
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"

SILVER_DIR.mkdir(parents=True, exist_ok=True)
GOLD_DIR.mkdir(parents=True, exist_ok=True)

PACIENTES_PATH = RAW_DIR / "fonte_1_pacientes_atendimentos.csv"
COMUNIDADES_PATH = RAW_DIR / "fonte_2_comunidades_remotas.csv"
CLIMA_OPENWEATHER_PATH = RAW_DIR / "fonte_3_clima_openweather.csv"

load_dotenv(BASE_DIR / ".env")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path, encoding="utf-8-sig")


def normalize_text(value):
    if pd.isna(value):
        return value

    return str(value).strip().lower()


def clean_pacientes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    text_columns = [
        "nome_paciente",
        "sexo",
        "sintoma_principal",
        "grupo_sintoma",
        "urgencia_informada_agente",
    ]

    for col in text_columns:
        df[col] = df[col].apply(normalize_text)

    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"], errors="coerce")

    numeric_columns = [
        "id_atendimento",
        "id_paciente",
        "idade",
        "id_comunidade",
        "temperatura_corporal",
        "dias_com_sintomas",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=[
            "id_atendimento",
            "id_paciente",
            "id_comunidade",
            "data_atendimento",
        ]
    )

    df = df.drop_duplicates(subset=["id_atendimento"])

    return df


def clean_comunidades(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    text_columns = [
        "nome_comunidade",
        "estado",
        "tipo_regiao",
        "tem_posto_apoio",
        "tem_transporte_disponivel",
        "barreira_natural",
        "nivel_isolamento",
    ]

    for col in text_columns:
        df[col] = df[col].apply(normalize_text)

    numeric_columns = [
        "id_comunidade",
        "latitude",
        "longitude",
        "distancia_hospital_km",
        "tempo_deslocamento_min",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["id_comunidade", "latitude", "longitude"])
    df = df.drop_duplicates(subset=["id_comunidade"])

    return df


def classify_climate_risk(chuva_mm, velocidade_vento, weather_main):
    weather_main = normalize_text(weather_main)

    if chuva_mm >= 30 or velocidade_vento >= 40 or weather_main in ["thunderstorm", "extreme"]:
        return "alto"

    if chuva_mm >= 10 or velocidade_vento >= 25 or weather_main == "rain":
        return "medio"

    return "baixo"


def load_weather_cache() -> pd.DataFrame:
    if CLIMA_OPENWEATHER_PATH.exists():
        return pd.read_csv(CLIMA_OPENWEATHER_PATH, encoding="utf-8-sig")

    return pd.DataFrame(
        columns=[
            "id_comunidade",
            "data_coleta",
            "chuva_mm",
            "temperatura_ambiente",
            "velocidade_vento",
            "umidade",
            "risco_climatico",
        ]
    )


def fetch_weather_from_openweather(row):
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY não encontrada no arquivo .env")

    params = {
        "lat": row["latitude"],
        "lon": row["longitude"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "pt_br",
    }

    response = requests.get(OPENWEATHER_URL, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(
            f"Erro ao buscar clima da comunidade {row['id_comunidade']}: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    weather = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    rain = data.get("rain", {})

    chuva_mm = rain.get("1h", 0)

    temperatura_ambiente = main.get("temp")
    velocidade_vento = wind.get("speed", 0)
    umidade = main.get("humidity")
    weather_main = weather.get("main", "")

    risco_climatico = classify_climate_risk(
        chuva_mm=chuva_mm,
        velocidade_vento=velocidade_vento,
        weather_main=weather_main,
    )

    return {
        "id_comunidade": int(row["id_comunidade"]),
        "data_coleta": str(date.today()),
        "chuva_mm": chuva_mm,
        "temperatura_ambiente": temperatura_ambiente,
        "velocidade_vento": velocidade_vento,
        "umidade": umidade,
        "risco_climatico": risco_climatico,
    }


def get_weather_data(comunidades: pd.DataFrame) -> pd.DataFrame:
    cache = load_weather_cache()
    today = str(date.today())

    if not cache.empty:
        cache["data_coleta"] = cache["data_coleta"].astype(str)

    new_weather_rows = []

    for _, comunidade in comunidades.iterrows():
        id_comunidade = int(comunidade["id_comunidade"])

        cached_today = cache[
            (cache["id_comunidade"].astype(int) == id_comunidade)
            & (cache["data_coleta"] == today)
        ]

        if not cached_today.empty:
            print(f"Usando cache de clima para comunidade {id_comunidade}")
            continue

        print(f"Consultando OpenWeather para comunidade {id_comunidade}")

        weather_row = fetch_weather_from_openweather(comunidade)
        new_weather_rows.append(weather_row)

        # Pequena pausa para evitar chamadas muito rápidas em sequência.
        time.sleep(1)

    if new_weather_rows:
        new_weather_df = pd.DataFrame(new_weather_rows)
        cache = pd.concat([cache, new_weather_df], ignore_index=True)

        cache = cache.drop_duplicates(
            subset=["id_comunidade", "data_coleta"],
            keep="last"
        )

        cache.to_csv(CLIMA_OPENWEATHER_PATH, index=False, encoding="utf-8-sig")

    clima_hoje = cache[cache["data_coleta"] == today].copy()

    return clima_hoje


def clean_clima(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["risco_climatico"] = df["risco_climatico"].apply(normalize_text)
    df["data_coleta"] = pd.to_datetime(df["data_coleta"], errors="coerce")

    numeric_columns = [
        "id_comunidade",
        "chuva_mm",
        "temperatura_ambiente",
        "velocidade_vento",
        "umidade",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["id_comunidade", "data_coleta"])
    df = df.drop_duplicates(subset=["id_comunidade", "data_coleta"])

    return df


def calculate_clinical_score(row) -> int:
    score = 0

    temperatura = row["temperatura_corporal"]
    idade = row["idade"]
    dias = row["dias_com_sintomas"]
    urgencia = row["urgencia_informada_agente"]

    if temperatura >= 39:
        score += 30
    elif temperatura >= 38:
        score += 20
    elif temperatura >= 37.5:
        score += 10

    if idade >= 60:
        score += 10

    if dias >= 5:
        score += 15
    elif dias >= 3:
        score += 10

    if urgencia == "alta":
        score += 20
    elif urgencia == "media":
        score += 10

    return score


def calculate_territorial_score(row) -> int:
    score = 0

    distancia = row["distancia_hospital_km"]
    tempo = row["tempo_deslocamento_min"]
    isolamento = row["nivel_isolamento"]
    transporte = row["tem_transporte_disponivel"]
    barreira = row["barreira_natural"]

    if distancia > 150:
        score += 25
    elif distancia >= 100:
        score += 20
    elif distancia >= 70:
        score += 10

    if tempo > 300:
        score += 20
    elif tempo >= 180:
        score += 10

    if isolamento == "alto":
        score += 20
    elif isolamento == "medio":
        score += 10

    if transporte == "n":
        score += 15

    if barreira != "nenhum":
        score += 10

    return score


def calculate_climate_score(row) -> int:
    score = 0

    risco = row["risco_climatico"]
    chuva = row["chuva_mm"]
    vento = row["velocidade_vento"]
    umidade = row["umidade"]

    if risco == "alto":
        score += 25
    elif risco == "medio":
        score += 10

    if chuva >= 30:
        score += 20
    elif chuva >= 10:
        score += 10

    if vento >= 40:
        score += 15
    elif vento >= 25:
        score += 10

    if umidade >= 90:
        score += 5

    return score


def classify_priority(score_total: int) -> str:
    if score_total <= 35:
        return "baixo risco"

    if score_total <= 70:
        return "atencao"

    if score_total <= 110:
        return "alta prioridade"

    return "critico territorial"


def build_priority_reason(row) -> str:
    reasons = []

    if row["score_clinico"] >= 50:
        reasons.append("sinais clinicos relevantes")

    if row["score_territorial"] >= 60:
        reasons.append("barreira territorial elevada")

    if row["score_climatico"] >= 45:
        reasons.append("risco climatico elevado")

    if not reasons:
        reasons.append("risco moderado ou baixo conforme dados integrados")

    return " + ".join(reasons)


def generate_triagem(pacientes, comunidades, clima) -> pd.DataFrame:
    df = pacientes.merge(
        comunidades,
        on="id_comunidade",
        how="left"
    )

    df = df.merge(
        clima,
        on="id_comunidade",
        how="left"
    )

    df["score_clinico"] = df.apply(calculate_clinical_score, axis=1)
    df["score_territorial"] = df.apply(calculate_territorial_score, axis=1)
    df["score_climatico"] = df.apply(calculate_climate_score, axis=1)

    df["score_total"] = (
        df["score_clinico"]
        + df["score_territorial"]
        + df["score_climatico"]
    )

    df["classificacao_prioridade"] = df["score_total"].apply(classify_priority)
    df["motivo_prioridade"] = df.apply(build_priority_reason, axis=1)
    df["data_processamento"] = pd.Timestamp.today().normalize()

    triagem = df[
        [
            "id_atendimento",
            "id_comunidade",
            "score_clinico",
            "score_territorial",
            "score_climatico",
            "score_total",
            "classificacao_prioridade",
            "motivo_prioridade",
            "data_processamento",
        ]
    ].copy()

    triagem.insert(0, "id_triagem", range(1, len(triagem) + 1))

    return triagem


def generate_alertas(pacientes: pd.DataFrame) -> pd.DataFrame:
    max_date = pacientes["data_atendimento"].max()
    start_date = max_date - pd.Timedelta(days=1)

    recentes = pacientes[
        pacientes["data_atendimento"].between(start_date, max_date)
    ]

    grouped = (
        recentes
        .groupby(["id_comunidade", "grupo_sintoma"])
        .size()
        .reset_index(name="quantidade_casos")
    )

    alertas = grouped[grouped["quantidade_casos"] >= 5].copy()

    if alertas.empty:
        return pd.DataFrame(
            columns=[
                "id_alerta",
                "id_comunidade",
                "grupo_sintoma",
                "quantidade_casos",
                "periodo_dias",
                "nivel_alerta",
                "descricao_alerta",
                "data_alerta",
            ]
        )

    alertas.insert(0, "id_alerta", range(1, len(alertas) + 1))
    alertas["periodo_dias"] = 2
    alertas["nivel_alerta"] = "alto"
    alertas["descricao_alerta"] = alertas.apply(
        lambda row: (
            f"{row['quantidade_casos']} casos do grupo {row['grupo_sintoma']} "
            f"na mesma comunidade em 2 dias"
        ),
        axis=1,
    )
    alertas["data_alerta"] = pd.Timestamp.today().normalize()

    return alertas


def main():
    print("Iniciando transformação dos dados do Medistar...")

    pacientes = read_csv(PACIENTES_PATH)
    comunidades = read_csv(COMUNIDADES_PATH)

    pacientes_limpos = clean_pacientes(pacientes)
    comunidades_limpas = clean_comunidades(comunidades)

    print("Coletando dados climáticos da OpenWeather...")
    clima_api = get_weather_data(comunidades_limpas)
    clima_limpo = clean_clima(clima_api)

    pacientes_limpos.to_csv(
        SILVER_DIR / "pacientes_limpos.csv",
        index=False,
        encoding="utf-8-sig"
    )

    comunidades_limpas.to_csv(
        SILVER_DIR / "comunidades_limpas.csv",
        index=False,
        encoding="utf-8-sig"
    )

    clima_limpo.to_csv(
        SILVER_DIR / "clima_limpo.csv",
        index=False,
        encoding="utf-8-sig"
    )

    triagem = generate_triagem(
        pacientes_limpos,
        comunidades_limpas,
        clima_limpo
    )

    alertas = generate_alertas(pacientes_limpos)

    triagem.to_csv(
        GOLD_DIR / "triagem_prioridade.csv",
        index=False,
        encoding="utf-8-sig"
    )

    alertas.to_csv(
        GOLD_DIR / "alertas_comunitarios.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("Transformação finalizada com sucesso.")
    print(f"Registros de pacientes limpos: {len(pacientes_limpos)}")
    print(f"Registros de comunidades limpas: {len(comunidades_limpas)}")
    print(f"Registros de clima limpos: {len(clima_limpo)}")
    print(f"Registros de triagem gerados: {len(triagem)}")
    print(f"Alertas comunitários gerados: {len(alertas)}")


if __name__ == "__main__":
    main()