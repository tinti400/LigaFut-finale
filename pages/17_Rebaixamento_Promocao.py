# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import calcular_movimentacao_divisoes, atualizar_classificacao
from datetime import datetime

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Rebaixamento e Promoção", page_icon="🏋️", layout="centered")
st.title("🏋️ Rebaixamento, Promoção e Playoff")

# 🔄 Atualiza classificações
df_div1 = atualizar_classificacao(supabase, 1)
df_div2 = atualizar_classificacao(supabase, 2)

df1_ord = sorted(df_div1, key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)
df2_ord = sorted(df_div2, key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

promovidos, rebaixados, (playoff_div1, playoff_div2) = calcular_movimentacao_divisoes(df1_ord, df2_ord)

# 📋 Exibição
st.subheader("⬆️ Subindo para a Divisão 1")
for tid, t in promovidos:
    st.write(f"- {t['nome']} ({t['pontos']} pts)")

st.subheader("⬇️ Rebaixados para a Divisão 2")
for tid, t in rebaixados:
    st.write(f"- {t['nome']} ({t['pontos']} pts)")

st.subheader("⚔️ Playoff pela vaga na Divisão 1")
st.markdown(f"**{playoff_div1[1]['nome']}** (18º Div 1) 🏆 vs 🏆 **{playoff_div2[1]['nome']}** (3º Div 2)")

vencedor = st.radio("Quem venceu o playoff?", [playoff_div1[1]["nome"], playoff_div2[1]["nome"]])

# ✅ Encerrar temporada
if st.button("🏁 Encerrar Temporada e Atualizar Divisões"):
    try:
        # 🧹 Zera classificações
        supabase.table("classificacao_divisao_1").delete().neq("id_time", "").execute()
        supabase.table("classificacao_divisao_2").delete().neq("id_time", "").execute()

        # 🔄 Atualiza divisões de rebaixados e promovidos
        for tid, _ in rebaixados:
            supabase.table("usuarios").update({"Divisao": "Divisão 2"}).eq("time_id", tid).execute()

        for tid, _ in promovidos:
            supabase.table("usuarios").update({"Divisao": "Divisão 1"}).eq("time_id", tid).execute()

        # 🔄 Playoff
        vencedor_id = playoff_div1[0] if vencedor == playoff_div1[1]["nome"] else playoff_div2[0]
        perdedor_id = playoff_div2[0] if vencedor == playoff_div1[1]["nome"] else playoff_div1[0]

        supabase.table("usuarios").update({"Divisao": "Divisão 1"}).eq("time_id", vencedor_id).execute()
        supabase.table("usuarios").update({"Divisao": "Divisão 2"}).eq("time_id", perdedor_id).execute()

        st.success("✅ Temporada encerrada e divisões atualizadas com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Erro ao encerrar temporada: {e}")
