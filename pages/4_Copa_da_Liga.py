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
@st.cache_data
def buscar_times():
    res = supabase.table("times").select("id, nome, logo").execute()
    return {
        item["id"]: {
            "nome": item["nome"],
            "escudo_url": item.get("logo", "")
        }
        for item in res.data
    }

# 🔁 Buscar a copa mais recente
def buscar_copa_recente():
    resultado = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
    return resultado.data[0] if resultado.data else None

# 🔁 Buscar todas as fases da mesma edição
def buscar_fases_copa(numero):
    fases = ["preliminar", "oitavas", "quartas", "semifinal", "final"]
    dados = {}
    for fase in fases:
        rodada = supabase.table("copa_ligafut").select("*").eq("fase", fase).eq("numero", numero).order("data_criacao", desc=True).execute()
        dados[fase] = rodada.data
    return dados

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

# 🔄 Executar carregamentos
times = buscar_times()
copa_atual = buscar_copa_recente()
fases_da_copa = buscar_fases_copa(copa_atual["numero"]) if copa_atual else {}

# 📌 Layout visual
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

# 🧾 Exibir todas as fases da copa atual
exibir_fase(col1, "🟡 Preliminar", fases_da_copa.get("preliminar", []))
exibir_fase(col2, "🔰 Oitavas", fases_da_copa.get("oitavas", []))
exibir_fase(col3, "🥅 Quartas", fases_da_copa.get("quartas", []))
exibir_fase(col4, "⚔️ Semifinal", fases_da_copa.get("semifinal", []))
exibir_fase(col5, "🏁 Final", fases_da_copa.get("final", []))

# 🏆 Campeão
if fases_da_copa.get("final"):
    jogos_finais = fases_da_copa["final"][0].get("jogos", [])
    if jogos_finais:
        jogo_final = jogos_finais[0]
        gm = jogo_final.get("gols_ida_m")
        gv = jogo_final.get("gols_ida_v")
        gm2 = jogo_final.get("gols_volta_v")
        gv2 = jogo_final.get("gols_volta_m")
        if None not in (gm, gv, gm2, gv2):
            total_m = int(gm) + int(gm2)
            total_v = int(gv) + int(gv2)
            vencedor_id = jogo_final["mandante_ida"] if total_m > total_v else jogo_final["visitante_ida"]
            vencedor = times.get(vencedor_id, {"nome": "?", "escudo_url": ""})
            st.markdown(f"""
                <div style='background:#222;padding:15px;border-radius:10px;text-align:center;color:white'>
                    <img src="{vencedor['escudo_url']}" width="60"><br><br>
                    🏆 <b>Campeão da Copa:</b><br>
                    <span style='font-size:18px'>{vencedor['nome']}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aguardando resultado da final.")
    else:
        st.info("Final não cadastrada.")
else:
    st.info("Aguardando fases finais.")


