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
vez = int(evento.get("vez", "0"))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
inicio_vez = evento.get("inicio_vez")
limite_bloqueios = evento.get("limite_bloqueios", 4)

# 🔁 Botão admin: reiniciar evento com nova ordem embaralhada
if eh_admin:
    st.markdown("---")
    st.subheader("🔁 Reiniciar Evento com Nova Ordem (Admin)")
    if st.button("🔀 Embaralhar e Reiniciar Evento"):
        try:
            res = supabase.table("times").select("id", "nome").execute()
            if res.data:
                nova_ordem = res.data
                random.shuffle(nova_ordem)
                nova_ordem_ids = [t["id"] for t in nova_ordem]

                supabase.table("configuracoes").update({
                    "ativo": True,
                    "finalizado": False,
                    "fase": "sorteio",
                    "ordem": nova_ordem_ids,
                    "vez": "0",
                    "inicio_vez": None,
                    "roubos": {},
                    "bloqueios": {},
                    "ultimos_bloqueios": bloqueios,
                    "ja_perderam": {},
                    "concluidos": [],
                    "inicio": str(datetime.utcnow())
                }).eq("id", ID_CONFIG).execute()

                st.success("✅ Evento sorteado! Veja abaixo a ordem dos times:")
                for i, time in enumerate(nova_ordem):
                    st.markdown(f"{i+1}️⃣ {time['nome']}")
                st.experimental_rerun()
            else:
                st.error("❌ Nenhum time encontrado para sortear.")
        except Exception as e:
            st.error(f"Erro ao sortear evento: {e}")

# 🛡️ Botão para iniciar fase de bloqueio após sorteio
if ativo and fase == "sorteio" and eh_admin:
    st.markdown("---")
    st.subheader("🛡️ Iniciar Fase de Bloqueio")
    if st.button("➡️ Começar Bloqueios"):
        supabase.table("configuracoes").update({
            "fase": "bloqueio"
        }).eq("id", ID_CONFIG).execute()
        st.success("Fase de bloqueio iniciada!")
        st.experimental_rerun()

# 👉 Botão admin para iniciar fase de ação (após bloqueio)
if ativo and fase == "bloqueio" and eh_admin:
    st.markdown("---")
    st.subheader("🚨 Iniciar Fase de Ação (Roubo)")
    if st.button("👉 Iniciar Fase de Ação"):
        supabase.table("configuracoes").update({
            "fase": "acao",
            "vez": "0",
            "inicio_vez": None,
            "concluidos": []
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Fase de ação iniciada com sucesso!")
        st.experimental_rerun()

# 🎯 Fase de ação (roubos)
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
                            r.get("nome") == nome_j and r.get("de") == time["id"]
                            for lista in roubos.values()
                            for r in lista
                        )
                        bloqueado = nome_j in bloqueados

                        if bloqueado:
                            st.markdown(f"🔒 {nome_j} - {posicao} (R$ {valor:,.0f})")
                        elif ja_roubado:
                            st.markdown(f"❌ {nome_j} - já roubado")
                        else:
                            if st.button(f"Roubar {nome_j} (R$ {valor/2:,.0f})", key=f"{time['id']}_{nome_j}"):
                                try:
                                    novo = roubos.get(id_time, [])
                                    novo.append({
                                        "nome": nome_j,
                                        "posicao": posicao,
                                        "valor": int(valor),
                                        "de": time["id"]
                                    })
                                    roubos[id_time] = novo
                                    ja_perderam[time["id"]] = ja_perderam.get(time["id"], 0) + 1

                                    saldo_r = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                                    saldo_p = supabase.table("times").select("saldo").eq("id", time["id"]).execute().data[0]["saldo"]
                                    supabase.table("times").update({"saldo": saldo_r - valor // 2}).eq("id", id_time).execute()
                                    supabase.table("times").update({"saldo": saldo_p + valor // 2}).eq("id", time["id"]).execute()

                                    registrar_movimentacao(id_time, nome_j, "Roubo", "Compra", valor // 2)

                                    supabase.table("configuracoes").update({
                                        "roubos": roubos,
                                        "ja_perderam": ja_perderam
                                    }).eq("id", ID_CONFIG).execute()

                                    st.success(f"✅ {nome_j} foi roubado com sucesso.")
                                    st.experimental_rerun()
                                except Exception as erro:
                                    st.error(f"Erro ao roubar {nome_j}: {erro}")

            if len(roubos.get(id_time, [])) >= 5:
                st.info("✅ Você já escolheu os 5 jogadores permitidos.")

            if st.button("✅ Finalizar minha participação"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({
                    "concluidos": concluidos,
                    "vez": str(vez + 1),
                    "inicio_vez": str(datetime.utcnow())
                }).eq("id", ID_CONFIG).execute()
                st.experimental_rerun()

        if eh_admin:
            st.markdown("---")
            st.subheader("👑 Controles do Administrador")
            if vez < len(ordem):
                if st.button("⏭️ Avançar manualmente para o próximo time"):
                    supabase.table("configuracoes").update({
                        "vez": str(vez + 1),
                        "inicio_vez": str(datetime.utcnow())
                    }).eq("id", ID_CONFIG).execute()
                    st.success("Próximo time ativado.")
                    st.experimental_rerun()
            else:
                if st.button("✅ Finalizar Evento e Validar Transferências"):
                    supabase.table("configuracoes").update({
                        "finalizado": True
                    }).eq("id", ID_CONFIG).execute()
                    st.success("Evento encerrado com sucesso! Iniciando transferência dos jogadores...")
                    st.experimental_rerun()
    except Exception as e:
        st.warning("Erro ao buscar nome do time da vez ou calcular o tempo.")
