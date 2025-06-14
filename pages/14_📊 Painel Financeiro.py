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

# 🔎 Buscar movimentações (ordenadas por data crescente)
res = supabase.table("movimentacoes").select("*").order("data", desc=False).limit(500).execute()
movs = res.data if res.data else []
if not movs:
    st.warning("Nenhuma movimentação registrada.")
    st.stop()

df = pd.DataFrame(movs)
df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y %H:%M")
df["valor"] = df["valor"].astype(float)

# 💰 Buscar saldos atuais dos times
res_saldos = supabase.table("times").select("nome, saldo").execute()
mapa_saldos = {
    item["nome"].strip().title(): float(item["saldo"])
    for item in res_saldos.data
    if item.get("nome") and item.get("saldo") is not None
}

# 🧾 Montar nova tabela com saldos
linhas = []
saldos_atuais = mapa_saldos.copy()

for i in reversed(df.index):  # Do mais recente para o mais antigo
    row = df.loc[i]
    tipo = str(row.get("tipo", "")).strip().lower()
    valor = row["valor"]
    origem = str(row.get("origem", "")).strip().title()
    destino = str(row.get("destino", "")).strip().title()
    data = row.get("data", "")

    # 🧾 Quem pagou
    if tipo in ["compra", "leilao", "multa", "roubo"]:
        if origem in saldos_atuais:
            saldo_novo = saldos_atuais[origem]
            saldo_antigo = saldo_novo + valor
            linhas.append({
                "Time": origem,
                "Movimentação": tipo.title(),
                "Valor": f'R${valor:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Antigo": f'R${saldo_antigo:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Novo": f'R${saldo_novo:,.0f}'.replace(",", ".").replace(".", ",", 1)
            })
            saldos_atuais[origem] = saldo_antigo

    # 🧾 Quem recebeu
    if tipo in ["venda", "leilao", "multa", "roubo"]:
        if destino in saldos_atuais:
            saldo_novo = saldos_atuais[destino]
            valor_recebido = valor if tipo != "roubo" else valor / 2
            saldo_antigo = saldo_novo - valor_recebido
            linhas.append({
                "Time": destino,
                "Movimentação": tipo.title(),
                "Valor": f'R${valor_recebido:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Antigo": f'R${saldo_antigo:,.0f}'.replace(",", ".").replace(".", ",", 1),
                "Saldo Novo": f'R${saldo_novo:,.0f}'.replace(",", ".").replace(".", ",", 1)
            })
            saldos_atuais[destino] = saldo_antigo

# 📊 Exibir resultado
if linhas:
    tabela_final = pd.DataFrame(linhas[::-1])  # volta pra ordem original
    st.dataframe(tabela_final, use_container_width=True)
else:
    st.error("❌ Nenhuma movimentação válida foi processada. Verifique os nomes dos times e os saldos.")


