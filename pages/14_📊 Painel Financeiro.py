# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📊 Movimentações Simples", layout="wide")
st.title("📊 Painel Financeiro - Simples")

# 🔎 Buscar movimentações (ordenadas por data)
res = supabase.table("movimentacoes").select("*").order("data", asc=True).execute()
movs = res.data if res.data else []
if not movs:
    st.warning("Nenhuma movimentação registrada.")
    st.stop()

df = pd.DataFrame(movs)
df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y %H:%M")
df["valor"] = df["valor"].astype(float)

# 💰 Buscar saldos atuais dos times
res_saldos = supabase.table("times").select("nome, saldo").execute()
mapa_saldos = {item["nome"]: float(item["saldo"]) for item in res_saldos.data}

# 🧾 Montar nova tabela com saldos
linhas = []
saldos_atuais = mapa_saldos.copy()

for i in reversed(df.index):  # Começa do mais recente pro mais antigo
    row = df.loc[i]
    tipo = row.get("tipo", "")
    valor = row["valor"]
    origem = row.get("origem", "")
    destino = row.get("destino", "")
    data = row.get("data", "")

    if tipo.lower() in ["compra", "leilao", "multa", "roubo"]:  # Origem gasta
        if origem in saldos_atuais:
            saldo_novo = saldos_atuais[origem]
            saldo_antigo = saldo_novo + valor
            linhas.append({
                "Time": origem,
                "Movimentação": tipo,
                "Valor": f'R${valor:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Antigo": f'R${saldo_antigo:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Novo": f'R${saldo_novo:,.0f}'.replace(",", ".").replace(".", ",", 1)
            })
            saldos_atuais[origem] = saldo_antigo  # retrocedendo

    if tipo.lower() in ["venda", "leilao", "multa", "roubo"]:  # Destino recebe
        if destino in saldos_atuais:
            saldo_novo = saldos_atuais[destino]
            saldo_antigo = saldo_novo - valor if tipo != "roubo" else saldo_novo - (valor / 2)
            linhas.append({
                "Time": destino,
                "Movimentação": tipo,
                "Valor": f'R${valor:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Antigo": f'R${saldo_antigo:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Novo": f'R${saldo_novo:,.0f}'.replace(",", ".").replace(".", ",", 1)
            })
            saldos_atuais[destino] = saldo_antigo

# 📊 Exibir resultado ordenado por data
tabela_final = pd.DataFrame(linhas[::-1])  # volta pra ordem normal
st.dataframe(tabela_final, use_container_width=True)


