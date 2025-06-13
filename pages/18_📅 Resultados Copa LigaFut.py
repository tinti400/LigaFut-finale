# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📅 Resultados Fase de Grupos", layout="wide")
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

# ⏲️ Data da copa mais recente (fase de grupos)
def buscar_data_recente_grupos():
    res = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute()
    return res.data[0]["data_criacao"] if res.data else None

data_atual_grupos = buscar_data_recente_grupos()
if not data_atual_grupos:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# 🔄 Buscar times (id e nome)
def buscar_times():
    res = supabase.table("times").select("id, nome").execute()
    return {t["id"]: t["nome"] for t in res.data}

times = buscar_times()

# 🔢 Buscar jogos da fase de grupos
res = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual_grupos).eq("fase", "grupos").execute()
grupo_data = res.data if res.data else []

if not grupo_data:
    st.info("A fase de grupos ainda não foi gerada.")
    st.stop()

# 🏋️ Interface para editar jogos por grupo
grupos = sorted(set([g["grupo"] for g in grupo_data]))
tab = st.selectbox("Escolha o grupo para editar resultados:", grupos)

grupo_jogos = next((g for g in grupo_data if g["grupo"] == tab), None)
if not grupo_jogos:
    st.error("Grupo não encontrado.")
    st.stop()

jogos = grupo_jogos.get("jogos", [])

st.markdown(f"### Jogos do Grupo {tab}")

for idx, jogo in enumerate(jogos):
    mandante_id = jogo.get("mandante")
    visitante_id = jogo.get("visitante")
    mandante_nome = times.get(mandante_id, "Mandante")
    visitante_nome = times.get(visitante_id, "Visitante")
    gols_m = jogo.get("gols_mandante")
    gols_v = jogo.get("gols_visitante")

    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 3])
    with col1:
        st.markdown(f"**{mandante_nome}**")
    with col2:
        gols_m_edit = st.number_input(
            f"Gols {mandante_nome}",
            min_value=0,
            value=int(gols_m) if gols_m is not None else 0,
            key=f"gm_{idx}",
            format="%d"
        )
    with col3:
        st.markdown("**X**")
    with col4:
        gols_v_edit = st.number_input(
            f"Gols {visitante_nome}",
            min_value=0,
            value=int(gols_v) if gols_v is not None else 0,
            key=f"gv_{idx}",
            format="%d"
        )
    with col5:
        st.markdown(f"**{visitante_nome}**")

    st.markdown("")

    if st.button("💾 Salvar Resultado", key=f"salvar_{idx}"):
        jogos[idx]["gols_mandante"] = gols_m_edit
        jogos[idx]["gols_visitante"] = gols_v_edit

        try:
            supabase.table("copa_ligafut").update({
                "jogos": jogos
            }).eq("grupo", tab).eq("data_criacao", data_atual_grupos).eq("fase", "grupos").execute()
            st.success(f"Resultado salvo para {mandante_nome} x {visitante_nome}")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

# ===============================
# ⚔️ Edição dos Resultados do Mata-Mata
# ===============================
st.markdown("---")
st.subheader("⚔️ Resultados do Mata-Mata")

fases_mata = ["oitavas", "quartas", "semifinal", "final"]
fase_selecionada = st.selectbox("Escolha a fase para editar os resultados:", fases_mata)

# Buscar a fase eliminatória mais recente
res_fase = supabase.table("copa_ligafut").select("*").eq("fase", fase_selecionada).order("data_criacao", desc=True).limit(1).execute()
fase_data = res_fase.data[0] if res_fase.data else None

if not fase_data:
    st.info(f"A fase '{fase_selecionada}' ainda não foi gerada.")
    st.stop()

jogos_mata = fase_data.get("jogos", [])

for idx, jogo in enumerate(jogos_mata):
    mandante_id = jogo.get("mandante")
    visitante_id = jogo.get("visitante")
    mandante_nome = times.get(mandante_id, "Mandante")
    visitante_nome = times.get(visitante_id, "Visitante")
    gols_m = jogo.get("gols_mandante")
    gols_v = jogo.get("gols_visitante")

    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 3])
    with col1:
        st.markdown(f"**{mandante_nome}**")
    with col2:
        gols_m_edit = st.number_input(
            f"Gols {mandante_nome}", min_value=0,
            value=int(gols_m) if gols_m is not None else 0,
            key=f"mata_gm_{idx}", format="%d"
        )
    with col3:
        st.markdown("**X**")
    with col4:
        gols_v_edit = st.number_input(
            f"Gols {visitante_nome}", min_value=0,
            value=int(gols_v) if gols_v is not None else 0,
            key=f"mata_gv_{idx}", format="%d"
        )
    with col5:
        st.markdown(f"**{visitante_nome}**")

    st.markdown("")

    # Botão de salvar resultado individual
    if st.button("💾 Salvar Resultado", key=f"salvar_mata_{idx}"):
        jogos_mata[idx]["gols_mandante"] = gols_m_edit
        jogos_mata[idx]["gols_visitante"] = gols_v_edit

        try:
            supabase.table("copa_ligafut").update({
                "jogos": jogos_mata
            }).eq("id", fase_data["id"]).execute()
            st.success(f"Resultado salvo para {mandante_nome} x {visitante_nome}")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

# Botão para salvar todos os resultados da fase
if st.button("💾 Salvar todos os resultados da fase eliminatória"):
    try:
        supabase.table("copa_ligafut").update({
            "jogos": jogos_mata
        }).eq("id", fase_data["id"]).execute()
        st.success("✅ Resultados atualizados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
