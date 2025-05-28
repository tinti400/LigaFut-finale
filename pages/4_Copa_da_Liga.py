# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa da LigaFut", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏆 Copa da LigaFut - Chaveamento</h1><hr>", unsafe_allow_html=True)

# 🔁 Buscar times (id + nome)
@st.cache
def buscar_times():
    res = supabase.table("times").select("id, nome, logo").execute()
    return {
        item["id"]: {
            "nome": item["nome"],
            "escudo_url": item.get("logo", "")
        }
        for item in res.data
    }

# 🔁 Buscar jogos por fase
def buscar_jogos(fase):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).order("numero").execute()
    return res.data

# 🎨 Exibir confronto com nome e placar
def exibir_card(jogo):
    id_m = jogo.get("mandante_ida")
    id_v = jogo.get("visitante_ida")

    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})

    gols_m = jogo.get("gols_ida_m", "?") if jogo.get("gols_ida_m") is not None else "?"
    gols_v = jogo.get("gols_ida_v", "?") if jogo.get("gols_ida_v") is not None else "?"

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

# 🔁 Fases
times = buscar_times()
oitavas = buscar_jogos("oitavas")
quartas = buscar_jogos("quartas")
semis = buscar_jogos("semifinal")
final = buscar_jogos("final")

# 🧱 Layout
col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1.2, 1.2, 1])

def exibir_fase(coluna, titulo, rodadas):
    with coluna:
        st.markdown(f"### {titulo}")
        if rodadas:
            for rodada in rodadas:
                for jogo in rodada.get("jogos", []):
                    exibir_card(jogo)
        else:
            st.info("Sem jogos cadastrados.")

# 🧾 Exibição por fase
exibir_fase(col1, "🔰 Oitavas", oitavas)
exibir_fase(col2, "🥅 Quartas", quartas)
exibir_fase(col3, "⚔️ Semifinal", semis)
exibir_fase(col4, "🏁 Final", final)

# 🏆 Campeão
with col5:
    st.markdown("### 🏆 Campeão")
    if final and final[0].get("jogos"):
        jogo_final = final[0]["jogos"][0]
        gm = jogo_final.get("gols_ida_m")
        gv = jogo_final.get("gols_ida_v")
        if gm is not None and gv is not None:
            vencedor_id = jogo_final["mandante_ida"] if gm > gv else jogo_final["visitante_ida"]
            vencedor = times.get(vencedor_id, {"nome": "?"})
            st.success(f"🏆 Campeão:\n\n**{vencedor['nome']}**")
        else:
            st.info("Aguardando resultado da final.")
    else:
        st.info("Final não cadastrada.")

