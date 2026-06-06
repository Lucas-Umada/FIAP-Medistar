# Medistar BDDI — Pipeline de Dados com Apache Airflow

O **Medistar** é uma solução de telemedicina e vigilância em saúde para regiões isoladas.

Este projeto representa a entrega da disciplina **Big Data Architecture & Data Integration**, com foco na criação de um pipeline de dados automatizado utilizando **Apache Airflow**, **Python**, **Pandas**, **OpenWeather API** e **Oracle Database**.

O pipeline integra dados de pacientes, comunidades remotas e clima para gerar uma classificação de prioridade de atendimento e possíveis alertas comunitários.

---

## Tecnologias utilizadas

- Python
- Pandas
- Requests
- Python-dotenv
- Oracledb
- Apache Airflow
- Docker
- Oracle Database
- OpenWeather API

---

## Estrutura do projeto

```text
medistar-bddi/
│
├── airflow/
│   ├── dags/
│   │   └── medistar_pipeline_dag.py
│   ├── logs/
│   ├── plugins/
│   ├── config/
│   ├── docker-compose.yaml
│   └── .env
│
├── data/
│   ├── raw/
│   │   ├── fonte_1_pacientes_atendimentos.csv
│   │   └── fonte_2_comunidades_remotas.csv
│   │
│   ├── silver/
│   └── gold/
│
├── scripts/
│   ├── setup_database.py
│   ├── transform_medistar.py
│   └── load_database.py
│
├── sql/
│   ├── create_tables.sql
│   ├── drop_tables.sql
│   └── analytics_queries.sql
│
├── .env
├── requirements.txt
└── README.md
```

---

## Fontes de dados

O projeto utiliza três fontes principais.

### Fonte 1 — Pacientes e atendimentos

Arquivo:

```text
data/raw/fonte_1_pacientes_atendimentos.csv
```

Contém dados básicos dos pacientes, sintomas, temperatura corporal, dias com sintomas e urgência informada pelo agente de saúde.

### Fonte 2 — Comunidades remotas

Arquivo:

```text
data/raw/fonte_2_comunidades_remotas.csv
```

Contém dados territoriais das comunidades, como latitude, longitude, distância até hospital, tempo de deslocamento, transporte disponível e nível de isolamento.

### Fonte 3 — OpenWeather API

A API OpenWeather é utilizada para buscar dados climáticos reais com base na latitude e longitude das comunidades.

O pipeline gera automaticamente o arquivo:

```text
data/raw/fonte_3_clima_openweather.csv
```

Para evitar excesso de chamadas na API, o script utiliza cache local. Se já existir clima coletado no dia atual para uma comunidade, o pipeline reutiliza o dado salvo.

---

## Pré-requisitos

Antes de rodar o projeto, instale:

- Python
- Docker Desktop
- DBeaver ou Oracle SQL Developer
- Conta e chave da OpenWeather API
- Acesso ao Oracle Database da FIAP

---

## Configuração do ambiente Python

Na raiz do projeto, crie um ambiente virtual:

```powershell
py -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Caso ainda não exista o `requirements.txt`, instale manualmente:

```powershell
python -m pip install pandas requests python-dotenv oracledb
```

Depois gere o arquivo:

```powershell
python -m pip freeze > requirements.txt
```

---

## Configuração das variáveis de ambiente do projeto

Na raiz do projeto, crie o arquivo:

```text
.env
```

Adicione as variáveis:

```env
OPENWEATHER_API_KEY=sua_chave_openweather

ORACLE_USER=seu_usuario_fiap
ORACLE_PASSWORD=sua_senha_fiap
ORACLE_HOST=oracle.fiap.com.br
ORACLE_PORT=1521
ORACLE_SID=ORCL
```

Esse arquivo é utilizado pelos scripts Python para acessar a OpenWeather API e o Oracle Database.

---

## Scripts principais

### `scripts/setup_database.py`

Configura automaticamente o banco de dados.

Esse script lê o arquivo:

```text
sql/create_tables.sql
```

Ele verifica se as tabelas necessárias já existem no Oracle. Caso alguma tabela ainda não exista, o script executa os comandos de criação automaticamente.

Tabelas criadas:

```text
TB_COMUNIDADE
TB_ATENDIMENTO
TB_CLIMA
TB_TRIAGEM_PRIORIDADE
TB_ALERTA_COMUNITARIO
```

### `scripts/transform_medistar.py`

Executa a transformação dos dados.

Esse script realiza:

- Leitura dos CSVs de entrada.
- Consulta à API OpenWeather.
- Uso de cache para evitar chamadas repetidas.
- Limpeza dos dados.
- Padronização de textos.
- Conversão de datas e números.
- Cálculo dos scores de prioridade.
- Geração de alertas comunitários.

Arquivos gerados:

```text
data/silver/pacientes_limpos.csv
data/silver/comunidades_limpas.csv
data/silver/clima_limpo.csv

data/gold/triagem_prioridade.csv
data/gold/alertas_comunitarios.csv
```

### `scripts/load_database.py`

Carrega os dados tratados no Oracle Database.

Esse script insere os dados nas tabelas:

```text
TB_COMUNIDADE
TB_ATENDIMENTO
TB_CLIMA
TB_TRIAGEM_PRIORIDADE
TB_ALERTA_COMUNITARIO
```

---

## Testando o pipeline manualmente

Antes de rodar pelo Airflow, é possível testar os scripts manualmente.

### 1. Configurar o banco automaticamente

```powershell
python scripts/setup_database.py
```

### 2. Rodar a transformação dos dados

```powershell
python scripts/transform_medistar.py
```

### 3. Carregar os dados no Oracle

```powershell
python scripts/load_database.py
```

---

## Configuração do Apache Airflow

O Airflow fica dentro da pasta:

```text
airflow/
```

Entre nessa pasta:

```powershell
cd airflow
```

Crie o arquivo `.env` dentro da pasta `airflow` com o seguinte conteúdo:

```env
AIRFLOW_UID=50000
AIRFLOW_GID=0
_PIP_ADDITIONAL_REQUIREMENTS=pandas requests python-dotenv oracledb
```

Esse arquivo é usado apenas pelo Docker/Airflow.

---

## Volumes no Docker Compose

No arquivo:

```text
airflow/docker-compose.yaml
```

Os volumes devem incluir as pastas do projeto:

```yaml
volumes:
  - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
  - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
  - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
  - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
  - ../scripts:/opt/airflow/scripts
  - ../data:/opt/airflow/data
  - ../sql:/opt/airflow/sql
  - ../.env:/opt/airflow/.env
```

Esses volumes permitem que o Airflow acesse os scripts Python, arquivos CSV, scripts SQL e variáveis de ambiente do projeto.

---

## Subindo o Airflow

Antes de executar os comandos, abra o **Docker Desktop** e aguarde o Docker Engine iniciar.

Dentro da pasta `airflow`, execute a inicialização:

```powershell
docker compose up -d
```

Verifique se os containers estão rodando:

```powershell
docker compose ps
```

---

## Acessando o Airflow

Abra no navegador:

```text
http://localhost:8080
```

Login padrão:

```text
Usuário: airflow
Senha: airflow
```

---

## Executando a DAG

No Airflow, procure a DAG:

```text
medistar_pipeline
```

Ative a DAG e clique em **Trigger DAG**.

O fluxo executado é:

```text
inicio
↓
validar_arquivos
↓
configurar_banco
↓
transformar_dados
↓
carregar_oracle
↓
validar_saida
↓
fim
```

---

## O que cada task faz

### `inicio`

Marca o início do pipeline.

### `validar_arquivos`

Verifica se os arquivos CSV obrigatórios existem na pasta `data/raw`.

### `configurar_banco`

Executa o script `setup_database.py`.

Essa etapa verifica se as tabelas necessárias já existem no Oracle Database. Caso ainda não existam, as tabelas são criadas automaticamente com base no arquivo `sql/create_tables.sql`.

### `transformar_dados`

Executa o script `transform_medistar.py`, responsável por tratar os dados, consultar a OpenWeather e gerar os arquivos processados.

### `carregar_oracle`

Executa o script `load_database.py`, responsável por carregar os dados tratados no Oracle Database.

### `validar_saida`

Lista os arquivos gerados nas pastas `data/silver` e `data/gold`.

### `fim`

Marca o fim do pipeline.

---

## Consultas analíticas

Após a carga no banco, execute o arquivo:

```text
sql/analytics_queries.sql
```

As consultas analisam:

- Quantidade de atendimentos por prioridade.
- Comunidades com maior score médio.
- Casos críticos em comunidades distantes.
- Sintomas mais frequentes por comunidade.
- Alertas comunitários gerados.
- Relação entre clima e prioridade.
- Ranking de barreira de acesso.
- Pacientes com maior prioridade individual.

---

## Parando o Airflow

Para parar os containers:

```powershell
docker compose down
```

Caso queira subir novamente:

```powershell
docker compose up -d
```

---

## Resultado esperado

Ao final da execução, o pipeline deve:

- Validar os arquivos CSV de entrada.
- Configurar automaticamente as tabelas no Oracle, caso ainda não existam.
- Ler os dados de pacientes e comunidades.
- Consultar dados climáticos reais pela OpenWeather.
- Gerar arquivos tratados nas camadas `silver` e `gold`.
- Calcular prioridade de atendimento.
- Gerar possíveis alertas comunitários.
- Carregar os dados no Oracle Database.
- Permitir análises por meio das consultas SQL.
