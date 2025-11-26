
# 📈 Análise de Ações do Setor de Defesa  

Este repositório contém um aplicativo interativo desenvolvido em **Streamlit** para analisar o comportamento de mercado de cinco grandes empresas do setor de Defesa dos EUA:

- **General Dynamics**
- **Lockheed Martin**
- **Northrop Grumman**
- **RTX Corp**
- **Boeing**

O objetivo é fornecer uma ferramenta acessível, intuitiva e visual para estudantes e professores da UNIFOR explorarem como fatores geopolíticos, comerciais e estratégicos impactam o valor de mercado de empresas ligadas à indústria de defesa.

O app pode ser acessado facilmente após o deploy no **Streamlit Community Cloud**, sem necessidade de instalar nada ou de conhecimentos de programação.

## 🚀 Funcionalidades Principais

### Upload intuitivo de CSVs
O usuário faz upload dos arquivos CSV contendo o histórico das empresas. O aplicativo identifica automaticamente cada empresa pelo nome do arquivo.

### ETL completo e automático
O app realiza:
- Conversão de datas  
- Limpeza de preços  
- Padronização dos dados  
- Consolidação de todos os CSVs  
- Cálculo de retornos semanais (%)

### Visualizações interativas
Inclui gráficos dinâmicos produzidos com **Altair**:
- Preço ao longo do tempo
- Retornos semanais (%)

### Identificação de DIPs e Momentum
O aplicativo encontra automaticamente:
- DIPs (quedas ≥ X%)
- Momentums (altas ≥ X%)

### Estatísticas avançadas por empresa
São calculados:
- Preço inicial  
- Preço final  
- Retorno total (%)  
- Volatilidade média (%)  
- Maior alta semanal (%)  
- Maior queda semanal (%)

### Conexão com Comércio Exterior
O app inclui uma seção interpretativa relacionando resultados com:
- geopolítica,
- contratos internacionais,
- embargos,
- sanções,
- demanda militar global.

## 📂 Estrutura do Repositório

```
/
├── app.py          # Código do aplicativo Streamlit
└── README.md       # Documento atual
```

## 🛠️ Execução Local (Opcional)

```bash
pip install streamlit pandas numpy altair
streamlit run app.py
```

## ☁️ Deploy no Streamlit Cloud

1. Acesse https://share.streamlit.io  
2. Clique em “New app”  
3. Selecione o repositório  
4. Escolha o arquivo `app.py`  
5. Deploy

A URL pública será algo como:

```
https://seu-projeto.streamlit.app
```

## 📜 Licença

Projeto educacional aberto. Pode ser reutilizado para fins acadêmicos.
