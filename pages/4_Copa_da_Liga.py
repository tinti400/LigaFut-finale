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

# 🔁 Identificar data mais recente da copa
def buscar_data_mais_recente():
    res = supabase.table("copa_ligafut").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    if res.data:
        return res.data[0]["data_criacao"]
    return None

# 🔁 Buscar fase da copa pela data
def buscar_fase(fase, data):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("data_criacao", data).execute()
    return res.data if res.data else []

# 🎨 Exibir confronto com escudo, nome, ida/volta e agregado (melhorado)
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
    <div style='
        background:#111;
        padding:15px;
        border-radius:12px;
        margin-bottom:15px;
        color:white;
        text-align:center;
        height:180px;
        display:flex;
        flex-direction:column;
        justify-content:space-between;
        box-shadow:0 0 10px rgba(0,0,0,0.5)'
    >
        <div style='display:flex;align-items:center;justify-content:space-between'>
            <div style='text-align:center;width:40%'>
                <img src='{mandante["escudo_url"]}' width='45'><br>
                <span style='font-size:13px'>{mandante["nome"]}</span>
            </div>
            <div style='text-align:center;width:20%'>
                <div style='font-size:20px;font-weight:bold'>{agregado}</div>
            </div>
            <div style='text-align:center;width:40%'>
                <img src='{visitante["escudo_url"]}' width='45'><br>
                <span style='font-size:13px'>{visitante["nome"]}</span>
            </div>
        </div>
        <div style='margin-top:5px;font-size:11px;line-height:1.2;color:#ccc'>
            Ida: ({gm_ida}x{gv_ida})<br>
            Volta: ({gm_volta}x{gv_volta})
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# 🔄 Buscar dados
times = buscar_times()
data_atual = buscar_data_mais_recente()
preliminar = buscar_fase("preliminar", data_atual)
oitavas = buscar_fase("oitavas", data_atual)
quartas = buscar_fase("quartas", data_atual)
semis = buscar_fase("semifinal", data_atual)
final = buscar_fase("final", data_atual)

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
            st.success(f"🏆 Campeão:

**{vencedor['nome']}**")
        else:
            st.info("Aguardando resultado da final.")
    else:
        st.info("Final não cadastrada.")


