# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📅 Resultados Fase de Grupos", layout="wide")
st.title("📅 Fase de Grupos - Resultados")

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

# 🧠 Funções auxiliares
def buscar_times():
    res = supabase.table("times").select("id, nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

def buscar_data_recente():
    res = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    return res.data[0]["data_criacao"] if res.data else None

# ⏲️ Data da copa
data_atual = buscar_data_recente()
if not data_atual:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# 🗂️ Buscar dados dos jogos da fase de grupos
res = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual).execute()
grupo_data = res.data if res.data else []
if not grupo_data:
    st.info("A fase de grupos ainda não foi gerada.")
    st.stop()

# 📋 Filtro por grupo
grupos = sorted(set([g["grupo"] for g in grupo_data]))
grupo_escolhido = st.selectbox("Selecione o grupo para editar os resultados:", grupos)

# 🔍 Buscar jogos do grupo selecionado
grupo_jogos = next((g for g in grupo_data if g["grupo"] == grupo_escolhido), None)
if not grupo_jogos:
    st.error("Grupo não encontrado.")
    st.stop()

times = buscar_times()
jogos = grupo_jogos.get("jogos", [])

st.markdown(f"### ⚽ Jogos do Grupo {grupo_escolhido}")

for idx, jogo in enumerate(jogos):
    mandante_id = jogo.get("mandante")
    visitante_id = jogo.get("visitante")
    mandante_nome = times.get(mandante_id, "Mandante")
    visitante_nome = times.get(visitante_id, "Visitante")

    st.markdown(f"#### 📝 Editar resultado: **{mandante_nome} x {visitante_nome}**")

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f"**{mandante_nome}**")
    with col2:
        gols_m = st.number_input("Gols M", min_value=0, value=jogo.get("gols_mandante") or 0, key=f"gm_{idx}")
    with col3:
        st.markdown("### x")
    with col4:
        gols_v = st.number_input("Gols V", min_value=0, value=jogo.get("gols_visitante") or 0, key=f"gv_{idx}")
    with col5:
        st.markdown(f"**{visitante_nome}**")

    if st.button(f"💾 Salvar resultado de {mandante_nome} x {visitante_nome}", key=f"salvar_{idx}"):
        # Atualiza os gols do jogo na lista
        jogos[idx]["gols_mandante"] = gols_m
        jogos[idx]["gols_visitante"] = gols_v

        try:
            supabase.table("copa_ligafut").update({"jogos": jogos}).eq("grupo", grupo_escolhido).eq("data_criacao", data_atual).execute()
            st.success("✅ Resultado salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar resultado: {e}")

    st.divider()
