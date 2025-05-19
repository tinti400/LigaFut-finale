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
inicio_evento = evento.get("inicio")
limite_bloqueios = evento.get("limite_bloqueios", 4)

# ---------------------- STATUS ----------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase: {fase.upper()}")

    if fase == "acao":
        try:
            nome_vez = supabase.table("times").select("nome").eq("id", ordem[vez]).execute().data[0]["nome"]
            st.markdown(f"🟡 **Vez do time:** {nome_vez}")

            tempo_inicial = datetime.fromisoformat(inicio_evento)
            tempo_vez = tempo_inicial + timedelta(minutes=3 * vez)
            tempo_restante = tempo_vez + timedelta(minutes=3) - datetime.utcnow()
            segundos = int(tempo_restante.total_seconds())

            if segundos > 0:
                minutos_restantes = segundos // 60
                segundos_restantes = segundos % 60
                st.info(f"⏳ Tempo restante: {minutos_restantes:02d}:{segundos_restantes:02d}")
            else:
                st.warning("⏱️ Tempo esgotado para este time.")

            if id_time == ordem[vez]:
                if st.button("✅ Finalizar minha participação"):
                    concluidos.append(id_time)
                    supabase.table("configuracoes").update({"concluidos": concluidos, "vez": vez + 1}).eq("id", ID_CONFIG).execute()
                    st.experimental_rerun()

            if eh_admin:
                if st.button("⏭️ Pular para o próximo time"):
                    supabase.table("configuracoes").update({"vez": vez + 1}).eq("id", ID_CONFIG).execute()
                    st.success("Avançando para o próximo time.")
                    st.experimental_rerun()

        except Exception as e:
            st.warning("Erro ao buscar nome do time da vez ou calcular o tempo.")
