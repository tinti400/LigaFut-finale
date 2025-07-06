
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import random

st.set_page_config(page_title="🕵️ Evento Roubo - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verificar login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# Função para registrar movimentações
def registrar_movimentacao(id_time, jogador, tipo, valor):
    try:
        supabase.table("movimentacoes_financeiras").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "descricao": f"{tipo} de {jogador}",
            "valor": valor,
            "data": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

# 🔍 Buscar status do evento
evento_data = supabase.table("configuracoes").select("*").eq("id", "evento_roubo").execute()
evento = evento_data.data[0] if evento_data.data else None

if not evento:
    st.warning("Evento ainda não iniciado pelo administrador.")
    st.stop()

fase = evento.get("fase", "configuracao")

# =================== FASE 1 - ADMIN CONFIGURA EVENTO ====================
if fase == "configuracao":
    st.header("⚙️ Configuração do Evento de Roubo")
    if st.session_state["usuario"] != "admin":
        st.info("Aguardando o administrador configurar o evento.")
        st.stop()

    num_perder = st.number_input("Quantos jogadores cada time poderá perder no máximo?", min_value=1, max_value=10, value=2)
    num_bloquear = st.number_input("Quantos jogadores cada time poderá bloquear?", min_value=1, max_value=10, value=3)
    num_roubar = st.number_input("Quantos jogadores cada time poderá roubar?", min_value=1, max_value=10, value=2)

    if st.button("🎲 Sortear Ordem e Iniciar Evento"):
        times_data = supabase.table("times").select("id, nome").execute()
        times = times_data.data
        ordem = random.sample(times, len(times))

        for i, time in enumerate(ordem):
            supabase.table("evento_roubo_ordem").insert({
                "id": str(uuid.uuid4()),
                "id_time": time["id"],
                "nome_time": time["nome"],
                "ordem": i
            }).execute()

        supabase.table("configuracoes").update({
            "fase": "acao",
            "max_perder": num_perder,
            "max_bloquear": num_bloquear,
            "max_roubar": num_roubar,
            "vez_atual": 0
        }).eq("id", "evento_roubo").execute()

        st.success("Evento configurado e iniciado com sucesso!")
        st.rerun()

# =================== FASE 2 - AÇÃO ====================
elif fase == "acao":
    st.header("🕵️ Fase de Ação - Evento de Roubo")
    ordem_data = supabase.table("evento_roubo_ordem").select("*").order("ordem", asc=True).execute()
    ordem = ordem_data.data
    vez_atual = evento.get("vez_atual", 0)

    if vez_atual >= len(ordem):
        st.success("✅ Todos os times já agiram. Clique abaixo para finalizar o evento.")
        if st.button("🚫 Finalizar Evento"):
            supabase.table("configuracoes").update({"fase": "finalizado"}).eq("id", "evento_roubo").execute()
            st.rerun()
        st.stop()

    time_da_vez = ordem[vez_atual]
    id_time_vez = time_da_vez["id_time"]
    nome_time_vez = time_da_vez["nome_time"]

    if id_time != id_time_vez:
        st.info(f"Aguardando a vez de **{nome_time_vez}**. Aguarde sua vez.")
        st.stop()

    st.subheader(f"🎯 Sua vez: {nome_time_vez}")
    times_data = supabase.table("times").select("id, nome").neq("id", id_time).execute()
    times_alvo = times_data.data

    for t in times_alvo:
        st.markdown(f"### 🛡️ Elenco do Time Alvo: **{t['nome']}**")

        elenco_data = supabase.table("elencos").select("*").eq("id_time", t["id"]).execute()
        elenco = elenco_data.data

        for jogador in elenco:
            nome = jogador["nome"]
            posicao = jogador.get("posição", "??")
            valor = jogador["valor"]
            nome_formatado = f"{nome} ({posicao}) - R${valor:,.0f}".replace(",", ".")

            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{nome_formatado}**")
            with col2:
                if st.button("💰 Roubar", key=f"{nome}_{t['id']}"):
                    # Lógica de roubo
                    if evento.get("max_perder", 0) <= 0:
                        st.warning("Este time não pode mais perder jogadores.")
                    else:
                        # Atualiza jogador
                        supabase.table("elencos").update({"id_time": id_time}).eq("id", jogador["id"]).execute()
                        # Movimentação
                        registrar_movimentacao(id_time, nome, "compra (roubo)", valor * 0.5)
                        registrar_movimentacao(t["id"], nome, "venda (roubo)", valor * 0.5)
                        # Reduz contagem do time alvo
                        novo_max = evento["max_perder"] - 1
                        supabase.table("configuracoes").update({"max_perder": novo_max}).eq("id", "evento_roubo").execute()
                        st.success(f"Você roubou {nome} com sucesso!")
                        st.rerun()

    if st.button("✅ Finalizar minha rodada"):
        supabase.table("configuracoes").update({"vez_atual": vez_atual + 1}).eq("id", "evento_roubo").execute()
        st.rerun()

# =================== FASE 3 - FINALIZADO ====================
elif fase == "finalizado":
    st.success("✅ Evento finalizado com sucesso!")
    st.markdown("Parabéns a todos os participantes. Os jogadores já foram transferidos com sucesso.")


