
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ------------------------------------------------------------------
# Configuração geral da página
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Análise de Mercado - Setor de Defesa",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Análise de Ações do Setor de Defesa")
st.markdown(
    '''

    Ele permite analisar o comportamento de preço de cinco grandes empresas do setor de defesa:

    - General Dynamics  
    - Lockheed Martin  
    - Northrop Grumman  
    - RTX Corp  
    - Boeing  

    A ideia é que qualquer pessoa – mesmo sem experiência em programação – consiga:

    1. **Enviar os arquivos CSV** com o histórico de preços.  
    2. **Filtrar períodos e empresas** de interesse.  
    3. **Visualizar gráficos de preço e de retorno (volatilidade)**.  
    4. **Identificar momentos de “DIP” (quedas fortes) e “Momentum” (altas fortes)**.  
    5. **Ler insights numéricos resumidos** para apoiar a análise de mercado.
    '''
)

st.info(
    "💡 Dica: este app funciona melhor quando você envia os cinco arquivos de uma vez, "
    "cada um com o nome da empresa no arquivo (por exemplo: `Boeing Stock Price History.csv`)."
)

# ------------------------------------------------------------------
# Funções auxiliares de ETL
# ------------------------------------------------------------------

COMPANY_LABELS = {
    "general dynamics": "General Dynamics",
    "lockheed martin": "Lockheed Martin",
    "northrop grumman": "Northrop Grumman",
    "rtx corp": "RTX Corp",
    "boeing": "Boeing",
}


def infer_company_name(filename: str) -> str:
    """Tenta descobrir o nome da empresa a partir do nome do arquivo."""
    lower_name = filename.lower()
    for key, label in COMPANY_LABELS.items():
        if key in lower_name:
            return label
    # Caso não consiga inferir, usa o próprio nome do arquivo (sem extensão)
    return filename.rsplit(".", 1)[0]


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """Limpa colunas numéricas que vêm como texto com vírgulas, pontos e símbolos."""
    s = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=True)  # espaço estranho comum em dados da web
        .str.replace(" ", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
    )
    return pd.to_numeric(s, errors="coerce")


def load_and_transform(files) -> pd.DataFrame:
    """Lê todos os arquivos CSV enviados e devolve um único DataFrame consolidado.

    Saída com colunas padronizadas:
    - company: nome da empresa
    - date: data (datetime)
    - price: preço de fechamento
    - return_pct: retorno percentual em relação ao período anterior
    """
    frames = []

    for uploaded in files:
        try:
            df = pd.read_csv(uploaded)
        except Exception:
            # tenta com outro encoding
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding="latin-1")

        # Normaliza nomes de colunas para evitar problemas de espaços
        df.columns = [c.strip() for c in df.columns]

        required_cols = {"Date", "Price"}
        if not required_cols.issubset(df.columns):
            st.warning(
                f"O arquivo **{uploaded.name}** não possui as colunas mínimas exigidas "
                f"({', '.join(required_cols)}). Ele será ignorado."
            )
            continue

        company = infer_company_name(uploaded.name)

        # Conversão de datas
        date = pd.to_datetime(
            df["Date"],
            errors="coerce",
        )

        # Limpeza do preço
        price = clean_numeric_column(df["Price"])

        temp = pd.DataFrame(
            {
                "company": company,
                "date": date,
                "price": price,
            }
        )

        # Remove linhas sem data ou preço
        temp = temp.dropna(subset=["date", "price"])

        frames.append(temp)

    if not frames:
        return pd.DataFrame(columns=["company", "date", "price", "return_pct"])

    data = pd.concat(frames, ignore_index=True)

    # Garante ordenação por empresa + data
    data = data.sort_values(["company", "date"])

    # Calcula retorno percentual por empresa
    data["return_pct"] = (
        data.groupby("company")["price"].pct_change() * 100.0
    )

    return data


def compute_summary_stats(data: pd.DataFrame) -> pd.DataFrame:
    """Calcula estatísticas descritivas por empresa."""
    if data.empty:
        return pd.DataFrame()

    stats = []

    for company, df_c in data.groupby("company"):
        df_c = df_c.sort_values("date")
        first_price = df_c["price"].iloc[0]
        last_price = df_c["price"].iloc[-1]
        total_return = (last_price / first_price - 1) * 100 if first_price > 0 else np.nan

        # Volatilidade: desvio padrão do retorno semanal
        vol = df_c["return_pct"].std()

        # Máxima alta e máxima queda semanais
        max_up = df_c["return_pct"].max()
        max_down = df_c["return_pct"].min()

        stats.append(
            {
                "Empresa": company,
                "Preço inicial": round(first_price, 2),
                "Preço final": round(last_price, 2),
                "Retorno total (%)": round(total_return, 2),
                "Volatilidade média (%)": round(vol, 2),
                "Maior alta semanal (%)": round(max_up, 2),
                "Maior queda semanal (%)": round(max_down, 2),
            }
        )

    return pd.DataFrame(stats)


def get_dips_and_momentum(data: pd.DataFrame, threshold: float = 10.0):
    """Identifica DIPs (quedas fortes) e Momentum (altas fortes)."""
    if data.empty:
        return (
            pd.DataFrame(columns=["date", "company", "price", "return_pct"]),
            pd.DataFrame(columns=["date", "company", "price", "return_pct"]),
        )

    dips = data[data["return_pct"] <= -abs(threshold)].copy()
    momentum = data[data["return_pct"] >= abs(threshold)].copy()

    dips = dips.sort_values(["date", "company"], ascending=[False, True])
    momentum = momentum.sort_values(["date", "company"], ascending=[False, True])

    return dips, momentum


# ------------------------------------------------------------------
# Upload de arquivos
# ------------------------------------------------------------------

st.header("1️⃣ Upload dos arquivos CSV")

uploaded_files = st.file_uploader(
    "Envie aqui os arquivos CSV (você pode selecionar todos de uma vez).",
    accept_multiple_files=True,
    type=["csv"],
)

if not uploaded_files:
    st.warning("Envie ao menos um arquivo CSV para iniciar a análise.")
    st.stop()

data = load_and_transform(uploaded_files)

if data.empty:
    st.error("Não foi possível carregar dados válidos dos arquivos enviados.")
    st.stop()

# ------------------------------------------------------------------
# Filtros na barra lateral
# ------------------------------------------------------------------

st.sidebar.title("⚙️ Filtros de análise")

companies = sorted(data["company"].unique().tolist())
selected_companies = st.sidebar.multiselect(
    "Selecione as empresas:",
    options=companies,
    default=companies,
)

if not selected_companies:
    st.sidebar.error("Selecione ao menos uma empresa.")
    st.stop()

data = data[data["company"].isin(selected_companies)]

min_date = data["date"].min().date()
max_date = data["date"].max().date()

date_range = st.sidebar.date_input(
    "Período de análise:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (data["date"].dt.date >= start_date) & (data["date"].dt.date <= end_date)
data = data[mask]

if data.empty:
    st.error("Nenhum dado no intervalo selecionado. Ajuste as datas ou as empresas.")
    st.stop()

st.success(
    f"Dados carregados com sucesso para **{len(selected_companies)}** empresa(s) "
    f"no período de **{start_date}** até **{end_date}**."
)

# ------------------------------------------------------------------
# Seção 2: Gráficos de preços e retornos
# ------------------------------------------------------------------

st.header("2️⃣ Gráficos de Preços e Retornos")

col_price, col_return = st.columns(2)

with col_price:
    st.subheader("Preço ao longo do tempo")

    price_chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Data"),
            y=alt.Y("price:Q", title="Preço de fechamento"),
            color=alt.Color("company:N", title="Empresa"),
            tooltip=["date:T", "company:N", "price:Q", "return_pct:Q"],
        )
        .properties(height=400)
        .interactive()
    )

    st.altair_chart(price_chart, use_container_width=True)

with col_return:
    st.subheader("Retornos semanais (%)")

    return_chart = (
        alt.Chart(data.dropna(subset=["return_pct"]))
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Data"),
            y=alt.Y("return_pct:Q", title="Retorno (%)"),
            color=alt.Color("company:N", title="Empresa"),
            tooltip=["date:T", "company:N", "price:Q", "return_pct:Q"],
        )
        .properties(height=400)
        .interactive()
    )

    st.altair_chart(return_chart, use_container_width=True)

st.caption(
    "⚠️ Retorno (%) é a variação percentual do preço em relação ao período imediatamente anterior "
    "(por exemplo, de uma semana para a outra)."
)

# ------------------------------------------------------------------
# Seção 3: Tabelas de DIPs e Momentum
# ------------------------------------------------------------------

st.header("3️⃣ Tabelas de DIPs (quedas fortes) e Momentum (altas fortes)")

threshold = st.slider(
    "Defina o limite de variação forte (em %):",
    min_value=5,
    max_value=30,
    value=10,
    step=1,
    help="Por exemplo, 10% significa que serão consideradas quedas/altas iguais ou maiores que 10% em valor absoluto.",
)

dips, momentum = get_dips_and_momentum(data, threshold=threshold)

col_dip, col_mom = st.columns(2)

with col_dip:
    st.subheader(f"DIPs – Quedas ≥ {threshold}%")
    if dips.empty:
        st.info("Não foram encontradas quedas tão fortes no período/empresas selecionados.")
    else:
        dips_view = dips[["date", "company", "price", "return_pct"]].copy()
        dips_view["date"] = dips_view["date"].dt.date
        dips_view = dips_view.rename(
            columns={
                "date": "Data",
                "company": "Empresa",
                "price": "Preço",
                "return_pct": "Retorno (%)",
            }
        )
        st.dataframe(dips_view, use_container_width=True)

with col_mom:
    st.subheader(f"Momentum – Altas ≥ {threshold}%")
    if momentum.empty:
        st.info("Não foram encontradas altas tão fortes no período/empresas selecionados.")
    else:
        mom_view = momentum[["date", "company", "price", "return_pct"]].copy()
        mom_view["date"] = mom_view["date"].dt.date
        mom_view = mom_view.rename(
            columns={
                "date": "Data",
                "company": "Empresa",
                "price": "Preço",
                "return_pct": "Retorno (%)",
            }
        )
        st.dataframe(mom_view, use_container_width=True)

# ------------------------------------------------------------------
# Seção 4: Estatísticas Resumidas
# ------------------------------------------------------------------

st.header("4️⃣ Estatísticas Resumidas por Empresa")

stats_df = compute_summary_stats(data)

if stats_df.empty:
    st.info("Sem dados suficientes para calcular estatísticas.")
else:
    st.dataframe(stats_df, use_container_width=True)

    st.markdown(
        '''
        **Como interpretar:**  
        - *Retorno total (%)* indica quanto o preço variou do início ao fim do período filtrado.  
        - *Volatilidade média (%)* está ligada ao risco: quanto maior, mais o preço oscila.  
        - *Maior alta / maior queda semanal (%)* mostram extremos de movimento de curto prazo.  
        '''
    )

# ------------------------------------------------------------------
# Seção 5: Considerações de Comércio Exterior
# ------------------------------------------------------------------

st.header("5️⃣ Possíveis Leituras para Comércio Exterior")

st.markdown(
    '''
    Este aplicativo não oferece recomendações de investimento, mas ajuda a conectar **movimentos de mercado** com 

    **decisões de comércio exterior**, por exemplo:

    - Empresas com **alta volatilidade** podem estar mais expostas a choques geopolíticos, contratos governamentais 

      ou notícias regulatórias.

    - **DIPs** podem representar momentos de forte aversão a risco ou notícias negativas relevantes, que afetam 

      a percepção de segurança do setor.

    - Períodos de **Momentum positivo** podem estar associados a novos contratos internacionais, aumento de demanda 

      por equipamentos de defesa ou mudanças na política externa.


    Na análise de comércio exterior, é interessante cruzar estes movimentos de preço com:

    - Decisões de compra de armamentos entre países;

    - Alterações em sanções econômicas e embargos;

    - Conflitos regionais ou aumento de tensões diplomáticas.


    A partir dos gráficos e tabelas gerados, o aluno pode construir narrativas como:

    > "No período em que a empresa X apresentou forte Momentum, houve anúncio de novos contratos com o país Y, 

    > indicando como decisões de política externa influenciam o valor de mercado de grandes fabricantes de defesa."
    '''
)
