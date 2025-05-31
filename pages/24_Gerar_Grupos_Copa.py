# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📅 Resultados da Copa - LigaFut", layout="wide")
st.title("📅 Resultados da Fase de Grupos - Copa LigaFut")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = len(admin_ref.data) > 0

# 🔄 Buscar times
res = supabase.table("times").select("id, nome").execute()
times_dict = {t["id"]: t["nome"] for t in res.data}

# 🔄 Buscar grupos
data_mais_recente = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
data_copa = data_mais_recente.data[0]["data_criacao"] if data_mais_recente.data else None

res = supabase.table("grupos_copa").select("grupo, id_time").eq("data_criacao", data_copa).execute()
grupos = {}
for item in res.data:
    grupo = item["grupo"]
    if grupo not in grupos:
        grupos[grupo] = []
    grupos[grupo].append(item["id_time"])

# 🔁 Gerar jogos (caso não existam)
jogos_res = supabase.table("resultados_grupos").select("*").eq("data_criacao", data_copa).execute()
if not jogos_res.data:
    from itertools import combinations
    for grupo_nome, ids in grupos.items():
        for a, b in combinations(ids, 2):
            jogo = {
                "grupo": grupo_nome,
                "mandante": a,
                "visitante": b,
                "gols_mandante": None,
                "gols_visitante": None,
                "data_criacao": data_copa
            }
            supabase.table("resultados_grupos").insert(jogo).execute()

# 🔄 Buscar jogos atualizados
res = supabase.table("resultados_grupos").select("*").eq("data_criacao", data_copa).order("grupo").execute()
jogos = res.data

# 🎯 Exibir e permitir edição
st.markdown("## 📝 Edição de Resultados")
grupo_atual = None
for i, jogo in enumerate(jogos):
    grupo = jogo["grupo"]
    if grupo != grupo_atual:
        st.subheader(f"{grupo}")
        grupo_atual = grupo

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f"**{times_dict.get(jogo['mandante'], '?')}** vs **{times_dict.get(jogo['visitante'], '?')}**")
    with col2:
        gols_m = st.number_input("Gols M", key=f"gm{i}", value=jogo["gols_mandante"] or 0, min_value=0)
    with col3:
        st.markdown("x")
    with col4:
        gols_v = st.number_input("Gols V", key=f"gv{i}", value=jogo["gols_visitante"] or 0, min_value=0)
    with col5:
        if eh_admin:
            if st.button("Salvar", key=f"salvar{i}"):
                supabase.table("resultados_grupos").update({
                    "gols_mandante": gols_m,
                    "gols_visitante": gols_v
                }).eq("id", jogo["id"]).execute()
                st.success("✅ Resultado salvo!")
                st.rerun()
        else:
            st.caption("Somente administradores podem editar.")

