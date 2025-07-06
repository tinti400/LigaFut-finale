# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

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

# ✅ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["email"] == email_usuario

# ⚙️ ID da configuração
ID_CONFIG = "evento_roubo"

# ✅ Buscar evento
res_evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
if not res_evento.data:
    st.error("❌ Evento de roubo não encontrado.")
    st.stop()

evento = res_evento.data[0]
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
concluidos = evento.get("concluidos", [])
finalizado = evento.get("finalizado", False)

st.title("🕵️ Evento de Roubo - LigaFut")

if finalizado:
    st.success("✅ Evento finalizado com sucesso!")
    st.stop()

# 🔁 Se for admin, pode encerrar manualmente
if eh_admin and st.button("❌ Finalizar Evento Agora (ADMIN)"):
    supabase.table("configuracoes").update({
        "fase": "finalizado",
        "finalizado": True
    }).eq("id", ID_CONFIG).execute()
    st.success("Evento encerrado manualmente.")
    st.rerun()

# 🔄 Avanço da vez
if vez >= len(ordem):
    st.info("✅ Todos os times já participaram do evento.")
    if eh_admin and st.button("✔️ Finalizar Evento"):
        supabase.table("configuracoes").update({
            "fase": "finalizado",
            "finalizado": True
        }).eq("id", ID_CONFIG).execute()
        st.success("Evento encerrado.")
        st.rerun()
    st.stop()

# 📍 Verifica se é a vez do time logado
id_time_vez = ordem[vez] if vez < len(ordem) else None

if id_time != id_time_vez and not eh_admin:
    nome_prox = supabase.table("times").select("nome").eq("id", id_time_vez).execute().data
    nome_prox = nome_prox[0]["nome"] if nome_prox else "Outro time"
    st.warning(f"⏳ Aguarde! Agora é a vez do time: **{nome_prox}**.")
    st.stop()

st.markdown(f"### 👊 É sua vez, **{nome_time}**!")

# 🔍 Selecionar time alvo
res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times_disponiveis = res_times.data

opcoes_times = {t["nome"]: t["id"] for t in times_disponiveis}
time_alvo_nome = st.selectbox("Escolha um time para roubar um jogador:", list(opcoes_times.keys()))
time_alvo_id = opcoes_times[time_alvo_nome]

# 🎯 Buscar elenco do time alvo
res_elenco = supabase.table("elenco").select("*").eq("id_time", time_alvo_id).execute()
elenco_alvo = res_elenco.data

if not elenco_alvo:
    st.warning("Esse time não possui jogadores disponíveis.")
else:
    df = pd.DataFrame(elenco_alvo)
    df = df[["nome", "posicao", "overall", "valor"]]
    jogador_escolhido = st.selectbox("👤 Escolha o jogador para roubar:", df["nome"].tolist())

    jogador_info = next((j for j in elenco_alvo if j["nome"] == jogador_escolhido), None)
    if jogador_info:
        valor_jogador = jogador_info["valor"]
        custo = int(valor_jogador * 0.5)

        st.info(f"💰 Custo do roubo: R$ {custo:,.0f}".replace(",", "."))

        if st.button("💸 Roubar jogador"):
            # Atualiza saldo
            saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
            if saldo_atual < custo:
                st.error("❌ Saldo insuficiente.")
            else:
                # Remove do time anterior
                supabase.table("elenco").delete().eq("id", jogador_info["id"]).execute()

                # Adiciona ao novo time
                novo_jogador = jogador_info.copy()
                novo_jogador["id"] = str(uuid.uuid4())
                novo_jogador["id_time"] = id_time
                supabase.table("elenco").insert(novo_jogador).execute()

                # Atualiza saldos
                saldo_destino = supabase.table("times").select("saldo").eq("id", time_alvo_id).execute().data[0]["saldo"]
                supabase.table("times").update({"saldo": saldo_atual - custo}).eq("id", id_time).execute()
                supabase.table("times").update({"saldo": saldo_destino + custo}).eq("id", time_alvo_id).execute()

                # Atualiza vez
                supabase.table("configuracoes").update({
                    "vez": vez + 1,
                    "concluidos": concluídos + [id_time]
                }).eq("id", ID_CONFIG).execute()

                st.success(f"✅ {jogador_info['nome']} foi roubado com sucesso de {time_alvo_nome}!")
                st.rerun()
