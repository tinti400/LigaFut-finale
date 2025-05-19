# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import random
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_login()

# Dados do usuário logado
id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

st.title("🚨 Evento de Roubo - LigaFut")

# ID fixo da configuração do evento
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

# Verifica se é admin
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True

# Buscar configuração do evento
res = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = res.data[0] if res.data else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
inicio_vez = evento.get("inicio_vez")
limite_bloqueios = evento.get("limite_bloqueios", 4)

# Botão de encerrar evento - sempre visível para admin
if eh_admin and ativo:
    if st.button("🛑 Encerrar Evento"):
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.success("Evento encerrado.")
        st.experimental_rerun()

# ---------------------- Fim do evento ----------------------
if evento.get("finalizado"):
    st.success("✅ Evento finalizado. Transferindo jogadores...")
    if roubos:
        for tid, acoes in roubos.items():
            for j in acoes:
                try:
                    supabase.table("elenco").delete().eq("id_time", j['de']).eq("nome", j['nome']).execute()
                    saldo_antigo = supabase.table("times").select("saldo").eq("id", j['de']).execute().data[0]['saldo']
                    novo_saldo = saldo_antigo + j['valor'] / 2
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", j['de']).execute()

                    jogador = j.copy()
                    jogador['id_time'] = tid
                    supabase.table("elenco").insert(jogador).execute()

                    saldo_comprador = supabase.table("times").select("saldo").eq("id", tid).execute().data[0]['saldo']
                    novo_saldo_c = saldo_comprador - j['valor'] / 2
                    supabase.table("times").update({"saldo": novo_saldo_c}).eq("id", tid).execute()

                    registrar_movimentacao(tid, j['nome'], "Roubo", "Compra", j['valor'] / 2)

                    st.markdown(f"✅ {j['nome']} transferido de ID {j['de']} para {tid}.")

                except Exception as err:
                    st.error(f"Erro ao transferir {j['nome']}: {err}")
    else:
        st.info("Nenhuma movimentação de roubo foi registrada neste evento.")
