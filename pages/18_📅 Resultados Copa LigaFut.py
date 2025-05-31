# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📅 Resultados Copa LigaFut", layout="wide")
st.title("📅 Resultados da Fase de Grupos")

# ✅ Verifica login
dados_sessao = st.session_state
if "usuario_id" not in dados_sessao:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# ⚡️ Verifica se é administrador
email_usuario = dados_sessao.get("usuario", "")
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if len(admin_ref.data) == 0:
    st.warning("⛔️ Acesso restrito aos administradores.")
    st.stop()

# ⏲️ Data da copa mais recente
def buscar_data_recente():
    res = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    return res.data[0]["data_criacao"] if res.data else None

data_atual = buscar_data_recente()
if not data_atual:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# 🔄 Buscar times (id, nome e logo)
def buscar_times():
    res = supabase.table("times").select("id, nome, logo").execute()
    return {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res.data}

times = buscar_times()

# 🔢 Buscar jogos da fase de grupos
res = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual).execute()
grupo_data = res.data if res.data else []

if not grupo_data:
    st.info("A fase de grupos ainda não foi gerada.")
    st.stop()

# 🔍 Seleção de grupo
grupos = sorted(set([g["grupo"] for g in grupo_data]))
tab = st.selectbox("Escolha o grupo:", grupos)

grupo_jogos = next((g for g in grupo_data if g["grupo"] == tab), None)
if not grupo_jogos:
    st.error("Grupo não encontrado.")
    st.stop()

jogos = grupo_jogos.get("jogos", [])

st.markdown(f"### Jogos do Grupo {tab}")
for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])

    mandante_info = times.get(jogo["mandante"], {"nome": "?", "logo": ""})
    visitante_info = times.get(jogo["visitante"], {"nome": "?", "logo": ""})

    with col1:
        st.image(mandante_info["logo"], width=30)
        st.write(f"**{mandante_info['nome']}**")
    with col2:
        gols_m = st.number_input(
            f"Gols {mandante_info['nome']}", min_value=0,
            value=jogo.get("gols_mandante") if jogo.get("gols_mandante") is not None else 0,
            key=f"gm_{idx}"
        )
    with col3:
        st.write("x")
    with col4:
        gols_v = st.number_input(
            f"Gols {visitante_info['nome']}", min_value=0,
            value=jogo.get("gols_visitante") if jogo.get("gols_visitante") is not None else 0,
            key=f"gv_{idx}"
        )
    with col5:
        st.image(visitante_info["logo"], width=30)
        st.write(f"**{visitante_info['nome']}**")

    if st.button("💾 Salvar Resultado", key=f"btn_{idx}"):
        jogos[idx]["gols_mandante"] = gols_m
        jogos[idx]["gols_visitante"] = gols_v
        supabase.table("copa_ligafut").update({"jogos": jogos}).eq("grupo", tab).eq("data_criacao", data_atual).execute()
        st.success("✅ Resultado salvo com sucesso!")
