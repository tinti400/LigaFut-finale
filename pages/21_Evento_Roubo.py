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

# 🔒 Alerta fixo para admin
if eh_admin and ativo:
    st.info("👑 Você é administrador. Use o botão abaixo para encerrar o evento a qualquer momento.")
    if st.button("🛑 Encerrar Evento"):
        supabase.table("configuracoes").update({
            "ativo": False,
            "finalizado": True
        }).eq("id", ID_CONFIG).execute()
        st.success("Evento encerrado.")
        st.experimental_rerun()

if ativo and fase == "acao":
    try:
        nome_vez = supabase.table("times").select("nome").eq("id", ordem[vez]).execute().data[0]["nome"]
        st.markdown(f"🟡 **Vez do time:** {nome_vez}")

        if not inicio_vez:
            inicio_vez = str(datetime.utcnow())
            supabase.table("configuracoes").update({"inicio_vez": inicio_vez}).eq("id", ID_CONFIG).execute()

        tempo_inicio = datetime.fromisoformat(inicio_vez)
        tempo_restante = tempo_inicio + timedelta(minutes=3) - datetime.utcnow()
        segundos = int(tempo_restante.total_seconds())

        if segundos > 0:
            minutos_restantes = segundos // 60
            segundos_restantes = segundos % 60
            st.info(f"⏳ Tempo restante: {minutos_restantes:02d}:{segundos_restantes:02d}")
        else:
            st.warning("⏱️ Tempo esgotado para este time.")

        if id_time == ordem[vez]:
            st.subheader("🔍 Escolha os jogadores para roubar")
            times = supabase.table("times").select("id", "nome").execute().data
            for time in times:
                if time["id"] == id_time or ja_perderam.get(time["id"], 0) >= 4:
                    continue

                elenco_ref = supabase.table("elenco").select("*").eq("id_time", time["id"]).execute()
                elenco = elenco_ref.data if elenco_ref.data else []
                bloqueados = [j["nome"] for j in bloqueios.get(time["id"], [])]

                with st.expander(f"📂 {time['nome']}"):
                    for jogador in elenco:
                        nome_j = jogador["nome"]
                        posicao = jogador["posicao"]
                        valor = jogador["valor"]

                        ja_roubado = any(
                            nome_j == r.get("nome") and r.get("de") == time["id"]
                            for acoes in roubos.values()
                            for r in acoes
                        )
                        bloqueado = nome_j in bloqueados

                        if bloqueado:
                            st.markdown(f"🔒 {nome_j} - {posicao} (R$ {valor:,.0f})")
                        elif ja_roubado:
                            st.markdown(f"❌ {nome_j} - já roubado")
                        else:
                            if st.button(f"Roubar {nome_j} (R$ {valor/2:,.0f})", key=f"{time['id']}_{nome_j}"):
                                novo = roubos.get(id_time, [])
                                novo.append({
                                    "nome": nome_j,
                                    "posicao": posicao,
                                    "valor": valor,
                                    "de": time["id"]
                                })
                                roubos[id_time] = novo
                                ja_perderam[time["id"]] = ja_perderam.get(time["id"], 0) + 1

                                supabase.table("configuracoes").update({
                                    "roubos": roubos,
                                    "ja_perderam": ja_perderam
                                }).eq("id", ID_CONFIG).execute()
                                st.experimental_rerun()

            if len(roubos.get(id_time, [])) >= 5:
                st.info("✅ Você já escolheu os 5 jogadores permitidos.")

            if st.button("✅ Finalizar minha participação"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({
                    "concluidos": concluidos,
                    "vez": vez + 1,
                    "inicio_vez": str(datetime.utcnow())
                }).eq("id", ID_CONFIG).execute()
                st.experimental_rerun()

        if eh_admin:
            if st.button("⏭️ Pular para o próximo time"):
                supabase.table("configuracoes").update({
                    "vez": vez + 1,
                    "inicio_vez": str(datetime.utcnow())
                }).eq("id", ID_CONFIG).execute()
                st.success("Avançando para o próximo time.")
                st.experimental_rerun()

    except Exception as e:
        st.warning("Erro ao buscar nome do time da vez ou calcular o tempo.")

# ⬇️ Aqui começa o bloco finalizado sem erro
if evento.get("finalizado"):
    st.success("✅ Evento finalizado. Transferindo jogadores...")

    if roubos:
        for tid, acoes in roubos.items():
            for j in acoes:
                try:
                    supabase.table("elenco").delete().eq("id_time", j["de"]).eq("nome", j["nome"]).execute()
                    saldo_v = supabase.table("times").select("saldo").eq("id", j["de"]).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": saldo_v + j["valor"]/2}).eq("id", j["de"]).execute()

                    novo = j.copy()
                    novo["id_time"] = tid
                    supabase.table("elenco").insert(novo).execute()

                    saldo_c = supabase.table("times").select("saldo").eq("id", tid).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": saldo_c - j["valor"]/2}).eq("id", tid).execute()

                    registrar_movimentacao(tid, j["nome"], "Roubo", "Compra", j["valor"] / 2)

                except Exception as err:
                    st.error(f"Erro ao transferir {j['nome']}: {err}")
    else:
        st.info("ℹ️ Nenhuma movimentação de roubo foi registrada neste evento.")

    if eh_admin:
        st.markdown("---")
        st.info("👑 Você é administrador. Deseja encerrar totalmente este evento?")
        if st.button("✅ Finalizar e sair do evento"):
            supabase.table("configuracoes").update({
                "ativo": False,
                "finalizado": False,
                "fase": "sorteio",
                "vez": 0,
                "ordem": [],
                "concluidos": [],
                "bloqueios": {},
                "ultimos_bloqueios": {},
                "ja_perderam": {},
                "roubos": {},
                "inicio_vez": None
            }).eq("id", ID_CONFIG).execute()
            st.success("Evento resetado com sucesso! Você pode criar um novo agora.")
            st.experimental_rerun()

# 🔁 Exibir botão para iniciar um novo evento se estiver inativo
def exibir_botao_iniciar():
    st.markdown("### 🚦 Evento inativo")
    if eh_admin:
        st.info("Clique abaixo para iniciar um novo evento de roubo.")
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
                    "ultimos_bloqueios": ultimos_bloqueios,
                    "ja_perderam": {},
                    "roubos": {},
                    "inicio_vez": None,
                    "limite_bloqueios": limite
                }).eq("id", ID_CONFIG).execute()
                st.success("Evento iniciado com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")

if not ativo:
    exibir_botao_iniciar()
