# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa - LigaFut", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏆 Copa da LigaFut - Chaveamento</h1><hr>", unsafe_allow_html=True)

# 📥 Buscar times
@st.cache_data
def buscar_times():
    res = supabase.table("times").select("id, nome, escudo_url").execute()
    return {item["id"]: item for item in res.data}

# 🔁 Buscar jogos por fase (usando nova tabela)
def buscar_jogos(fase):
    res = supabase.table("18_Copa_ligafut").select("*").eq("fase", fase).order("id").execute()
    return res.data

# 🎨 Exibir card do confronto
def exibir_card(jogo):
    mandante = times.get(jogo.get("id_mandante"), {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(jogo.get("id_visitante"), {"nome": "Aguardando", "escudo_url": ""})
    gols_m = jogo.get("gols_mandante", "?") if jogo.get("gols_mandante") is not None else "?"
    gols_v = jogo.get("gols_visitante", "?") if jogo.get("gols_visitante") is not None else "?"
    
    card = f"""
    <div style='background:#222;padding:10px;border-radius:10px;margin-bottom:10px;color:white'>
        <div style='display:flex;align-items:center;justify-content:space-between;'>
            <div style='text-align:center;width:45%'>
                {'<img src="'+mandante['escudo_url']+'" width="40"><br>' if mandante['escudo_url'] else ''}
                {mandante["nome"]}
            </div>
            <div style='font-size:20px;font-weight:bold;width:10%;text-align:center'>{gols_m} x {gols_v}</div>
            <div style='text-align:center;width:45%'>
                {'<img src="'+visitante['escudo_url']+'" width="40"><br>' if visitante['escudo_url'] else ''}
                {visitante["nome"]}
            </div>
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# 🔄 Buscar dados
times = buscar_times()
oitavas = buscar_jogos("oitavas")
quartas = buscar_jogos("quartas")
semis = buscar_jogos("semifinal")
final = buscar_jogos("final")

# 📌 Layout visual
col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1.2, 1.2, 1])

with col1:
    st.markdown("### 🔰 Oitavas")
    if oitavas:
        for jogo in oitavas:
            exibir_card(jogo)
    else:
        st.info("Sem jogos cadastrados.")

with col2:
    st.markdown("### 🥅 Quartas")
    if quartas:
        for jogo in quartas:
            exibir_card(jogo)
    else:
        st.info("Sem jogos cadastrados.")

with col3:
    st.markdown("### ⚔️ Semifinal")
    if semis:
        for jogo in semis:
            exibir_card(jogo)
    else:
        st.info("Sem jogos cadastrados.")

with col4:
    st.markdown("### 🏁 Final")
    if final:
        for jogo in final:
            exibir_card(jogo)
    else:
        st.info("Sem jogos cadastrados.")

with col5:
    st.markdown("### 🏆 Campeão")
    if final and final[0].get("gols_mandante") is not None and final[0].get("gols_visitante") is not None:
        f = final[0]
        vencedor_id = f["id_mandante"] if f["gols_mandante"] > f["gols_visitante"] else f["id_visitante"]
        vencedor = times.get(vencedor_id, {"nome": "?"})
        st.success(f"🏆 Campeão:\n\n**{vencedor['nome']}**")
    else:
        st.info("Aguardando finalização da final.")
