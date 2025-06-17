# -*- coding: utf-8 -*-
from supabase import create_client
import streamlit as st

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

# 🥇 Premiação final por posição (Divisão 1 e 2)
premiacao_div1 = {
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
    11: 35_000_000
}
premiacao_div2 = premiacao_div1.copy()

# ▶️ Aplicar premiação
def aplicar_premiacao_final():
    times = supabase.table("times").select("id", "nome", "saldo", "divisao").execute().data

    for time in times:
        id_time = time["id"]
        saldo_atual = time.get("saldo", 0)
        divisao = time.get("divisao", "2")

        copa = supabase.table("copa").select("fase_alcancada").eq("id_time", id_time).execute().data
        fase = copa[0]["fase_alcancancada"] if copa else None
        premio_copa = premiacao_copa.get(fase, 0)

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

        if divisao == "1":
            classif = supabase.table("classificacao_1_divisao").select("posicao_final").eq("id_time", id_time).execute().data
            posicao = classif[0]["posicao_final"] if classif else None
            premio_divisao = premiacao_div1.get(posicao, 0)
        else:
            classif = supabase.table("classificacao_2_divisao").select("posicao_final").eq("id_time", id_time).execute().data
            posicao = classif[0]["posicao_final"] if classif else None
            premio_divisao = premiacao_div2.get(posicao, 0)

        total = premio_copa + bonus_total + premio_divisao
        novo_saldo = saldo_atual + total

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        supabase.table("movimentacoes").insert({
            "id_time": id_time,
            "categoria": "Premiação Final",
            "tipo": "entrada",
            "valor": total,
            "descricao": f"Premiação final da temporada (Copa + Desempenho + Divisão)"
        }).execute()

    st.success("✅ Premiação final aplicada com sucesso!")

# 🔘 Botão
st.set_page_config(page_title="Premiação Final", layout="centered")
st.title("💸 Aplicar Premiação Final da LigaFut")

if st.button("Aplicar Premiações Agora"):
    aplicar_premiacao_final()
