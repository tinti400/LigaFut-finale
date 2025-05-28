# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa da LigaFut", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏆 Copa da LigaFut - Chaveamento</h1><hr>", unsafe_allow_html=True)

# 🔁 Buscar times (id + nome + logo)
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

# 🔁 Buscar dados da copa mais recente, independente da fase
def buscar_fase(fase):
    todas = supabase.table("copa_ligafut").select("*").eq("fase", fase).order("data_criacao", desc=True).execute()
    return todas.data[:1] if todas.data else []

# 🎨 Exibir confronto com escudo, nome, ida/volta e agregado
def exibir_card(jogo):
    id_m = jogo.get("mandante_ida")
    id_v = jogo.get("visitante_ida")

    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})

    gm_ida = jogo.get("gols_ida_m", "?") if jogo.get("gols_ida_m") is not None else "?"
    gv_ida = jogo.get("gols_ida_v", "?") if jogo.get("gols_ida_v") is not None else "?"
    gm_volta = jogo.get("gols_volta_v", "?") if jogo.get("gols_volta_v") is not None else "?"
    gv_volta = jogo.get("gols_volta_m", "?") if jogo.get("gols_volta_m") is not None else "?"

    try:
        gm_total = int(gm_ida) + int(gm_volta)
        gv_total = int(gv_ida) + int(gv_volta)
        agregado = f"{gm_total}x{gv_total}"
    except:
        agregado = "?x?"

    card = f"""
    <div style='background:#111;padding:15px;border-radius:12px;margin-bottom:10px;color:white;text-align:center'>
        <div style='display:flex;align-items:center;justify-content:space-between'>
            <div style='text-align:center;width:40%'>
                <img src='{mandante["escudo_url"]}' width='50'><br>
                <span style='font-size:14px'>{mandante["nome"]}</span>
            </div>
            <div style='text-align:center;width:20%'>
                <div style='font-size:24px;font-weight:bold'>{agregado}</div>
                <div style='font-size:12px;line-height:1.2;margin-top:5px'>
                    ({gm_ida}x{gv_ida})<br>({gm_volta}x{gv_volta})
                </div>
            </div>
            <div style='text-align:center;width:40%'>
                <img src='{visitante["escudo_url"]}' width='50'><br>
                <span style='font-size:14px'>{visitante["nome"]}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# 🔄 Buscar dados
times = buscar_times()
preliminar = buscar_fase("preliminar")
oitavas = buscar_fase("oitavas")
quartas = buscar_fase("quartas")
semis = buscar_fase("semifinal")
final = buscar_fase("final")

# 📌 Layout visual
col0, col1, col2, col3, col4, col5 = st.columns([1.1, 1.1, 1.1, 1.1, 1.1, 1])

def exibir_fase(coluna, titulo, rodadas):
    with coluna:
        st.markdown(f"### {titulo}")
        if rodadas:
            for rodada in rodadas:
                for jogo in rodada.get("jogos", []):
                    exibir_card(jogo)
        else:
            st.info("Sem jogos cadastrados.")

# 🧾 Exibir todas as fases
exibir_fase(col0, "🔎 Preliminar", preliminar)
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
        gm2 = jogo_final.get("gols_volta_v")
        gv2 = jogo_final.get("gols_volta_m")
        if None not in (gm, gv, gm2, gv2):
            total_m = int(gm) + int(gm2)
            total_v = int(gv) + int(gv2)
            vencedor_id = jogo_final["mandante_ida"] if total_m > total_v else jogo_final["visitante_ida"]
            vencedor = times.get(vencedor_id, {"nome": "?"})
            st.success(f"🏆 Campeão:\n\n**{vencedor['nome']}**")
        else:
            st.info("Aguardando resultado da final.")
    else:
        st.info("Final não cadastrada.")


