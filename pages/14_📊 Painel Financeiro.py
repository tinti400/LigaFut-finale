# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📊 Painel Financeiro Simples", layout="wide")
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

# 🔁 Mapeamento de apelidos → nomes oficiais
apelidos_para_oficial = {
    "Ajax Amsterdam": "Ajax",
    "Atlético De Madrid": "Atletico De Madrid",
    "Atletico Madrid": "Atletico De Madrid",
    "Fc Barcelona": "Barcelona",
    "Barcelona Fc": "Barcelona",
    "Fc Bayern": "Bayern",
    "Bayern Munique": "Bayern",
    "Belgrano Fc": "Belgrano",
    "Boca Juniors": "Boca Jrs",
    "Boca": "Boca Jrs",
    "Borussia Dortmund": "Borussia",
    "Casa Pia Ac": "Casa Pia",
    "Charleroi Sc": "Charleroi",
    "Chelsea Fc": "Chelsea",
    "Estudiantes De La Plata": "Estudiantes",
    "Intermiami": "Inter Miami",
    "Inter Miami Cf": "Inter Miami",
    "Leicester City": "Leicester",
    "Manchester Utd": "Manchester United",
    "Man Utd": "Manchester United",
    "Ac Milan": "Milan",
    "SSC Napoli": "Napoli",
    "Napoli Fc": "Napoli",
    "Newell's": "Newells",
    "Olympique Marseille": "Olympique Marselhe",
    "O. Marseille": "Olympique Marselhe",
    "Palmeiras Fc": "Palmeiras",
    "Palmeiras Futebol Clube": "Palmeiras",
    "Paris Saint-Germain": "Psg",
    "PSG FC": "Psg",
    "Real Betis Balompié": "Real Betis",
    "Real Madrid Cf": "Real Madrid",
    "Rio Ave Fc": "Rio Ave",
    "River Plate": "River",
    "As Roma": "Roma",
    "Tottenham Hotspur": "Tottenham",
    "Venezia Fc": "Venezia",
    "Wolverhampton Wanderers": "Wolverhampton",
    "Wrexham Afc": "Wrexham"
}

# ✅ Padronizar nomes com título e aplicar mapeamento
df["origem"] = df["origem"].astype(str).str.strip().str.title().replace(apelidos_para_oficial)
df["destino"] = df["destino"].astype(str).str.strip().str.title().replace(apelidos_para_oficial)

# 💰 Buscar saldos atuais dos times
res_saldos = supabase.table("times").select("nome, saldo").execute()
mapa_saldos = {
    item["nome"].strip().title(): float(item["saldo"])
    for item in res_saldos.data
    if item.get("nome") and item.get("saldo") is not None
}

# 👁️ Visualização para debug
st.subheader("👁️ Times da tabela de saldos (times):")
st.write(sorted(mapa_saldos.keys()))

st.subheader("🔎 Nomes encontrados nas movimentações:")
st.write("Origem:", sorted(df["origem"].dropna().unique().tolist()))
st.write("Destino:", sorted(df["destino"].dropna().unique().tolist()))

# 🧾 Montar nova tabela com saldos
linhas = []
saldos_atuais = mapa_saldos.copy()

for i in reversed(df.index):  # do mais recente para o mais antigo
    row = df.loc[i]
    tipo = str(row.get("tipo", "")).strip().lower()
    valor = row["valor"]
    origem = row.get("origem", "")
    destino = row.get("destino", "")
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
    tabela_final = pd.DataFrame(linhas[::-1])  # ordem cronológica
    st.dataframe(tabela_final, use_container_width=True)
else:
    st.error("❌ Nenhuma movimentação válida foi processada. Verifique os nomes dos times e saldos.")




