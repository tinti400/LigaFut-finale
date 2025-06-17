# -*- coding: utf-8 -*-
from supabase import create_client
import streamlit as st
import pandas as pd

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ⚽ Premiação da Copa
premiacao_copa = {
    "grupo": 10_000_000,
    "classificado": 25_000_000,
    "oitavas": 40_000_000,
    "quartas": 60_000_000,
    "semi": 85_000_000,
    "vice": 110_000_000,
    "campeao": 130_000_000
}

# 📊 Bônus por desempenho
bonus_desempenho = {
    "vitoria": 3_000_000,
    "empate": 600_000,
    "gol_feito": 125_000,
    "gol_sofrido": -20_000
}

# 🥇 Premiação por colocação final
premiacao_div = {
    1: 150_000_000,
    2: 130_000_000,
    3: 110_000_000,
    4: 110_000_000,
    5: 95_000_000,
    6: 70_000_000,
    7: 60_000_000,
    8: 55_000_000,
    9: 45_000_000,
    10: 33_000_000,
    11: 35_000_000,
    12: 25_000_000,
    13: 20_000_000
}

st.set_page_config(page_title="💸 Aplicar Premiação", layout="wide")
st.title("💰 Prévia da Premiação Final da LigaFut")

tabela_preview = []

# 🔍 Buscar classificações
class1 = supabase.table("classificacao_divisao_1").select("*").execute().data
class2 = supabase.table("classificacao_divisao_2").select("*").execute().data
mapa_class1 = {c["id_time"]: c["posicao_final"] for c in class1}
mapa_class2 = {c["id_time"]: c["posicao_final"] for c in class2}

times = supabase.table("times").select("id", "nome", "saldo").execute().data

for time in times:
    id_time = time["id"]
    nome = time["nome"]
    saldo_atual = time.get("saldo", 0)

    if id_time in mapa_class1:
        divisao = "1"
        posicao = mapa_class1[id_time]
    elif id_time in mapa_class2:
        divisao = "2"
        posicao = mapa_class2[id_time]
    else:
        continue  # time não classificado, pula

    premio_divisao = premiacao_div.get(posicao, 0)

    # 🏆 Fase da Copa
    copa = supabase.table("copa").select("fase_alcancada").eq("id_time", id_time).execute().data
    fase = copa[0]["fase_alcancada"] if copa else None
    premio_copa = premiacao_copa.get(fase, 0)

    # 📊 Desempenho
    est = supabase.table("estatisticas").select("*").eq("id_time", id_time).execute().data
    if est:
        est = est[0]
        bonus_total = (
            est.get("vitorias", 0) * bonus_desempenho["vitoria"] +
            est.get("empates", 0) * bonus_desempenho["empate"] +
            est.get("gols_pro", 0) * bonus_desempenho["gol_feito"] +
            est.get("gols_contra", 0) * bonus_desempenho["gol_sofrido"]
        )
    else:
        bonus_total = 0

    total = premio_copa + bonus_total + premio_divisao
    novo_saldo = saldo_atual + total

    tabela_preview.append({
        "Time": nome,
        "Divisão": divisao,
        "Posição": posicao,
        "Copa": f"R$ {premio_copa:,.0f}",
        "Desempenho": f"R$ {bonus_total:,.0f}",
        "Classificação": f"R$ {premio_divisao:,.0f}",
        "Total a Receber": f"R$ {total:,.0f}",
    })

df_preview = pd.DataFrame(tabela_preview)
st.dataframe(df_preview, use_container_width=True)

# ✅ Botão de confirmação
if st.button("💸 Aplicar Premiações Agora"):
    for i, linha in enumerate(tabela_preview):
        id_time = list(mapa_class1.keys()) + list(mapa_class2.keys())
        id_time = id_time[i]
        valor_total = linha["Total a Receber"].replace("R$", "").replace(".", "").replace(",", "")
        total = int(valor_total)

        saldo_atual = times[i].get("saldo", 0)
        novo_saldo = saldo_atual + total

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "categoria": "Premiação Final",
            "tipo": "entrada",
            "valor": total,
            "descricao": "Premiação final da temporada (Copa + Desempenho + Divisão)"
        }).execute()

    st.success("✅ Premiação aplicada com sucesso!")

