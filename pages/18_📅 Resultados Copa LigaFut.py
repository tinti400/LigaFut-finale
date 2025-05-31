# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from collections import defaultdict
import random
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🗕️ Resultados Copa LigaFut", layout="wide")
st.title("🗕️ Resultados da Fase de Grupos")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# ⚡️ Verifica se é administrador
email_usuario = st.session_state.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if len(admin_ref.data) == 0:
    st.warning("⛔️ Acesso restrito aos administradores.")
    st.stop()

# ⏲️ Buscar data da edição atual da copa
res_data = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
data_atual = res_data.data[0]["data_criacao"] if res_data.data else None
if not data_atual:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# 🔄 Buscar times (nome + logo)
res_times = supabase.table("times").select("id, nome, logo").execute()
times = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res_times.data}

# 🔢 Buscar todos os grupos e jogos
res_copa = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual).eq("fase", "grupos").execute()
grupo_data = res_copa.data if res_copa.data else []
if not grupo_data:
    st.info("A fase de grupos ainda não foi gerada.")
    st.stop()

grupo_selecionado = st.selectbox("Escolha o grupo para editar:", sorted({g["grupo"] for g in grupo_data}))

grupo_atual = next((g for g in grupo_data if g["grupo"] == grupo_selecionado), None)
jogos = grupo_atual.get("jogos", []) if grupo_atual else []

st.markdown(f"### Jogos do {grupo_selecionado}")

for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 0.5, 1.5, 3])

    mandante = times.get(jogo["mandante"], {"nome": "?", "logo": ""})
    visitante = times.get(jogo["visitante"], {"nome": "?", "logo": ""})

    with col1:
        st.image(mandante["logo"], width=30)
        st.markdown(f"**{mandante['nome']}**")

    with col2:
        gols_m = st.number_input(f"Gols {mandante['nome']}", min_value=0, value=jogo.get("gols_mandante") or 0, key=f"gm_{idx}", label_visibility="visible")

    with col3:
        st.markdown("<h4 style='text-align:center;'>x</h4>", unsafe_allow_html=True)

    with col4:
        gols_v = st.number_input(f"Gols {visitante['nome']}", min_value=0, value=jogo.get("gols_visitante") or 0, key=f"gv_{idx}", label_visibility="visible")

    with col5:
        st.image(visitante["logo"], width=30)
        st.markdown(f"**{visitante['nome']}**")

    if st.button("📅 Salvar Resultado", key=f"salvar_{idx}"):
        try:
            jogos[idx]["gols_mandante"] = gols_m
            jogos[idx]["gols_visitante"] = gols_v
            supabase.table("copa_ligafut").update({"jogos": jogos}).eq("grupo", grupo_selecionado).eq("data_criacao", data_atual).execute()
            st.success("Resultado salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# ⏭️ Avançar para Oitavas
st.markdown("---")
st.subheader("🔄 Avançar para Oitavas")

def jogos_preenchidos():
    for grupo in grupo_data:
        for j in grupo.get("jogos", []):
            if j.get("gols_mandante") is None or j.get("gols_visitante") is None:
                return False
    return True

def calcular_classificacao(jogos):
    tabela = defaultdict(lambda: {"P": 0, "GP": 0, "GC": 0, "SG": 0})
    for j in jogos:
        m, v = j["mandante"], j["visitante"]
        gm, gv = j["gols_mandante"], j["gols_visitante"]
        if None in (gm, gv):
            continue
        tabela[m]["GP"] += gm
        tabela[m]["GC"] += gv
        tabela[v]["GP"] += gv
        tabela[v]["GC"] += gm
        if gm > gv:
            tabela[m]["P"] += 3
        elif gv > gm:
            tabela[v]["P"] += 3
        else:
            tabela[m]["P"] += 1
            tabela[v]["P"] += 1
    for t in tabela:
        tabela[t]["SG"] = tabela[t]["GP"] - tabela[t]["GC"]
    return sorted(tabela.items(), key=lambda x: (x[1]["P"], x[1]["SG"], x[1]["GP"]), reverse=True)

if jogos_preenchidos():
    if st.button("⏭️ Gerar Oitavas de Final"):
        classificados = []
        for grupo in grupo_data:
            classificados_grupo = calcular_classificacao(grupo["jogos"])
            ids = [tid for tid, _ in classificados_grupo[:4]]
            classificados.extend(ids)
        random.shuffle(classificados)
        oitavas = []
        for i in range(0, len(classificados), 2):
            oitavas.append({
                "mandante_ida": classificados[i],
                "visitante_ida": classificados[i+1],
                "gols_ida_m": None,
                "gols_ida_v": None,
                "gols_volta_m": None,
                "gols_volta_v": None
            })
        try:
            supabase.table("copa_ligafut").insert({
                "fase": "oitavas",
                "data_criacao": data_atual,
                "jogos": oitavas
            }).execute()
            st.success("🚀 Oitavas de Final geradas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar oitavas: {e}")
else:
    st.info("Todos os jogos precisam estar preenchidos para avançar para as oitavas.")

