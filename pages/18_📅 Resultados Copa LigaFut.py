# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta, timezone
from utils import registrar_movimentacao

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📆 Horário de Brasília (UTC-3)
def agora_brasilia():
    return datetime.now(timezone.utc) - timedelta(hours=3)

st.set_page_config(page_title="🗕️ Resultados Fase de Grupos", layout="wide")
st.title("🗕️ Resultados da Fase de Grupos")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.warning("⛔ Acesso restrito aos administradores.")
    st.stop()

# Buscar times
res_times = supabase.table("times").select("id, nome").execute()
times = {t["id"]: t["nome"] for t in res_times.data}

# Função para pagar bônus dos patrocinadores ativos
def pagar_bonus_vitoria(id_time):
    patrocinadores = supabase.table("patrocinios_ativos").select("*").eq("id_time", id_time).execute().data
    for p in patrocinadores:
        valor = p.get("bonus_vitoria") or 0
        if valor > 0:
            registrar_movimentacao(
                id_time=id_time,
                tipo="Entrada",
                valor=valor,
                descricao="Bônus por Vitória do Patrocinador"
            )

# Atualizar jogos no elenco
def atualizar_jogos_elenco_completo(id_time_mandante, id_time_visitante):
    for id_time in [id_time_mandante, id_time_visitante]:
        jogadores = supabase.table("elenco").select("id", "jogos").eq("id_time", id_time).execute().data
        for jogador in jogadores:
            jogos_atuais = jogador.get("jogos", 0) or 0
            supabase.table("elenco").update({"jogos": jogos_atuais + 1}).eq("id", jogador["id"]).execute()

# Buscar data mais recente da fase de grupos
data_grupos = supabase.table("grupos_copa").select("data_criacao").order("data_criacao", desc=True).limit(1).execute().data
data_atual_grupos = data_grupos[0]["data_criacao"] if data_grupos else None

if not data_atual_grupos:
    st.info("Nenhuma edição da copa encontrada.")
    st.stop()

# Resultados da fase de grupos
res = supabase.table("copa_ligafut").select("*").eq("data_criacao", data_atual_grupos).eq("fase", "grupos").execute()
grupo_data = res.data if res.data else []

grupos = sorted(set([g["grupo"] for g in grupo_data]))
grupo_escolhido = st.selectbox("Escolha o grupo para editar resultados:", grupos)
grupo_jogos = next((g for g in grupo_data if g["grupo"] == grupo_escolhido), None)

if not grupo_jogos:
    st.error("Grupo não encontrado.")
    st.stop()

jogos = grupo_jogos.get("jogos", [])

for idx, jogo in enumerate(jogos):
    mandante_id = jogo["mandante"]
    visitante_id = jogo["visitante"]
    mandante_nome = times.get(mandante_id, "Mandante")
    visitante_nome = times.get(visitante_id, "Visitante")
    gols_m = jogo.get("gols_mandante", 0)
    gols_v = jogo.get("gols_visitante", 0)

    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 3])
    with col1:
        st.markdown(f"**{mandante_nome}**")
    with col2:
        gm = st.number_input(f"Gols {mandante_nome}", min_value=0, value=int(gols_m) if gols_m is not None else 0, key=f"gm_{idx}")
    with col3:
        st.markdown("**X**")
    with col4:
        gv = st.number_input(f"Gols {visitante_nome}", min_value=0, value=int(gols_v) if gols_v is not None else 0, key=f"gv_{idx}")
    with col5:
        st.markdown(f"**{visitante_nome}**")

    if st.button("📏 Salvar Resultado", key=f"salvar_grupo_{idx}"):
        jogos[idx]["gols_mandante"] = gm
        jogos[idx]["gols_visitante"] = gv

        try:
            supabase.table("copa_ligafut").update({
                "jogos": jogos,
                "data_alteracao": agora_brasilia().isoformat()
            }).eq("grupo", grupo_escolhido).eq("fase", "grupos").eq("data_criacao", data_atual_grupos).execute()

            atualizar_jogos_elenco_completo(mandante_id, visitante_id)

            if gm > gv:
                pagar_bonus_vitoria(mandante_id)
            elif gv > gm:
                pagar_bonus_vitoria(visitante_id)

            st.success(f"✅ Resultado salvo com sucesso para {mandante_nome} x {visitante_nome}")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

# ⚔️ FASES ELIMINATÓRIAS
st.subheader("⚔️ Resultados do Mata-Mata")
fases = ["oitavas", "quartas", "semifinal", "final"]
fase = st.selectbox("Escolha a fase:", fases)

res_fase = supabase.table("copa_ligafut").select("*").eq("fase", fase).order("data_criacao", desc=True).limit(1).execute()
fase_data = res_fase.data[0] if res_fase.data else None

if not fase_data:
    st.info(f"A fase '{fase}' ainda não foi gerada.")
    st.stop()

jogos_mata = fase_data.get("jogos", [])

for idx, jogo in enumerate(jogos_mata):
    mandante_id = jogo["mandante"]
    visitante_id = jogo["visitante"]
    mandante_nome = times.get(mandante_id, "Mandante")
    visitante_nome = times.get(visitante_id, "Visitante")
    gols_m = int(jogo.get("gols_mandante") or 0)
    gols_v = int(jogo.get("gols_visitante") or 0)

    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 3])
    with col1:
        st.markdown(f"**{mandante_nome}**")
    with col2:
        gm = st.number_input(f"Gols {mandante_nome}", min_value=0, value=gols_m, key=f"mata_gm_{idx}")
    with col3:
        st.markdown("**X**")
    with col4:
        gv = st.number_input(f"Gols {visitante_nome}", min_value=0, value=gols_v, key=f"mata_gv_{idx}")
    with col5:
        st.markdown(f"**{visitante_nome}**")

    if st.button("📏 Salvar Resultado", key=f"salvar_mata_{idx}"):
        jogos_mata[idx]["gols_mandante"] = gm
        jogos_mata[idx]["gols_visitante"] = gv

        try:
            supabase.table("copa_ligafut").update({
                "jogos": jogos_mata,
                "data_alteracao": agora_brasilia().isoformat()
            }).eq("id", fase_data["id"]).execute()

            atualizar_jogos_elenco_completo(mandante_id, visitante_id)

            if gm > gv:
                pagar_bonus_vitoria(mandante_id)
            elif gv > gm:
                pagar_bonus_vitoria(visitante_id)

            st.success(f"✅ Resultado salvo com sucesso para {mandante_nome} x {visitante_nome}")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.markdown("---")

if st.button("📥 Salvar todos os resultados da fase eliminatória"):
    try:
        supabase.table("copa_ligafut").update({
            "jogos": jogos_mata,
            "data_alteracao": agora_brasilia().isoformat()
        }).eq("id", fase_data["id"]).execute()
        st.success("✅ Resultados atualizados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")ntrad
