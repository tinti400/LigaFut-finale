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
fase = evento.get("fase", "acao")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
inicio_evento = evento.get("inicio")
limite_bloqueios = evento.get("limite_bloqueios", 4)

# ---------------------- ADMIN ----------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        limite = st.number_input("🔒 Quantos jogadores cada time poderá bloquear?", min_value=1, max_value=11, value=4, step=1)
        if st.button("🚀 Iniciar Evento de Roubo"):
            try:
                times_ref = supabase.table("times").select("id").execute()
                ordem = [doc["id"] for doc in times_ref.data]
                random.shuffle(ordem)
                supabase.table("configuracoes").update({
                    "ativo": True,
                    "inicio": str(datetime.utcnow()),
                    "fase": "bloqueio",
                    "ordem": ordem,
                    "vez": 0,
                    "concluidos": [],
                    "bloqueios": {},
                    "ja_perderam": {},
                    "roubos": {},
                    "finalizado": False,
                    "limite_bloqueios": limite
                }).eq("id", ID_CONFIG).execute()
                st.success("Evento iniciado na fase de bloqueio!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")
        
    else:
        if st.button("🛑 Encerrar Evento"):
            supabase.table("configuracoes").update({
                "ativo": False,
                "finalizado": True
            }).eq("id", ID_CONFIG).execute()
            st.success("Evento encerrado.")
            st.experimental_rerun()

# ---------------------- STATUS ----------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase: {fase.upper()}")

    if fase == "bloqueio":
        st.subheader("🔒 Fase de Bloqueio de Jogadores")
        elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
        elenco = elenco_ref.data if elenco_ref.data else []

        bloqueados_do_time = bloqueios.get(id_time, [])
        nomes_bloqueados = [j['nome'] for j in bloqueados_do_time]

        st.markdown(f"Você pode bloquear até **{limite_bloqueios}** jogadores do seu time.")
        selecionados = st.multiselect("Selecione os jogadores para bloquear", [j['nome'] for j in elenco], default=nomes_bloqueados)

        if len(selecionados) > limite_bloqueios:
            st.warning(f"⚠️ Limite de {limite_bloqueios} bloqueios excedido.")
        elif st.button("🔐 Confirmar bloqueios"):
            novos_bloqueios = [j for j in elenco if j['nome'] in selecionados]
            bloqueios[id_time] = novos_bloqueios

            supabase.table("configuracoes").update({
                "bloqueios": bloqueios
            }).eq("id", ID_CONFIG).execute()

            st.success("Bloqueios salvos com sucesso!")

        if eh_admin:
            if st.button("✅ Avançar para fase de ação"):
                supabase.table("configuracoes").update({"fase": "acao"}).eq("id", ID_CONFIG).execute()
                st.success("Fase de ação iniciada manualmente pelo administrador.")
                st.experimental_rerun()
        else:
            if id_time in bloqueios:
                st.info("✅ Você já confirmou seus bloqueios.")
            elif st.button("✔️ OK - Finalizar bloqueios"):
                novos_bloqueios = [j for j in elenco if j['nome'] in selecionados]
                bloqueios[id_time] = novos_bloqueios

                supabase.table("configuracoes").update({
                    "bloqueios": bloqueios
                }).eq("id", ID_CONFIG).execute()

                st.success("Bloqueios confirmados. Aguarde o início da fase de ação.")
                st.experimental_rerun()

        if all(t in bloqueios for t in ordem):
            supabase.table("configuracoes").update({"fase": "acao"}).eq("id", ID_CONFIG).execute()
            st.success("Todos os times bloquearam. Iniciando fase de roubo...")
            st.experimental_rerun()

    elif fase == "acao":
        try:
            nome_vez = supabase.table("times").select("nome").eq("id", ordem[vez]).execute().data[0]["nome"]
            st.markdown(f"🟡 **Vez do time:** {nome_vez}")

            # Cronômetro regressivo de 3 minutos
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

        except:
            st.warning("Erro ao buscar nome do time da vez ou calcular o tempo.")
