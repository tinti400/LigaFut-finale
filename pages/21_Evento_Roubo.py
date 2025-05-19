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
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

st.title("🚨 Evento de Roubo - LigaFut")

# Configuração do evento
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

def atualizar_configuracao(dados):
    supabase.table("configuracoes").update(dados).eq("id", ID_CONFIG).execute()

# Verifica se é admin
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True

# Buscar evento
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

# 🔁 Admin - reiniciar evento
if eh_admin:
    st.markdown("---")
    st.subheader("🔁 Reiniciar Evento com Nova Ordem (Admin)")
    if st.button("🔀 Embaralhar e Reiniciar Evento"):
        res = supabase.table("times").select("id", "nome").execute()
        if res.data:
            nova_ordem = res.data
            random.shuffle(nova_ordem)
            nova_ordem_ids = [t["id"] for t in nova_ordem]

            atualizar_configuracao({
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
            })

            st.success("✅ Evento sorteado! Veja abaixo a ordem dos times:")
            for i, time in enumerate(nova_ordem):
                st.markdown(f"{i+1}️⃣ {time['nome']}")
            st.experimental_rerun()

        else:
            st.error("❌ Nenhum time encontrado para sortear.")

# 🛡️ Admin - iniciar fase de bloqueio
if ativo and fase == "sorteio" and eh_admin:
    st.markdown("---")
    st.subheader("🛡️ Iniciar Fase de Bloqueio")
    if st.button("➡️ Começar Bloqueios"):
        atualizar_configuracao({"fase": "bloqueio"})
        st.success("Fase de bloqueio iniciada!")
        st.experimental_rerun()


# 👉 Admin - iniciar fase de ação
if ativo and fase == "bloqueio" and eh_admin:
    st.markdown("---")
    st.subheader("🚨 Iniciar Fase de Ação (Roubo)")
    if st.button("👉 Iniciar Fase de Ação"):
        atualizar_configuracao({
            "fase": "acao",
            "vez": "0",
            "inicio_vez": None,
            "concluidos": []
        })
        st.success("✅ Fase de ação iniciada com sucesso!")
        st.experimental_rerun()


# 🎯 Fase de Ação
if ativo and fase == "acao":
    try:
        nome_vez = supabase.table("times").select("nome").eq("id", ordem[vez]).execute().data[0]["nome"]
        st.markdown(f"🟡 **Vez do time:** {nome_vez}")

        if not inicio_vez:
            inicio_vez = str(datetime.utcnow())
            atualizar_configuracao({"inicio_vez": inicio_vez})

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

                elenco = supabase.table("elenco").select("*").eq("id_time", time["id"]).execute().data or []
                bloqueados = [j["nome"] for j in bloqueios.get(time["id"], [])]

                with st.expander(f"📂 {time['nome']}"):
                    for jogador in elenco:
                        nome_j = jogador["nome"]
                        posicao = jogador["posicao"]
                        valor = int(jogador["valor"]) if isinstance(jogador["valor"], float) else jogador["valor"]

                        if nome_j in bloqueados:
                            st.markdown(f"🔒 {nome_j} - {posicao} (R$ {valor:,.0f})")
                            continue

                        ja_roubado = any(r.get("nome") == nome_j and r.get("de") == time["id"]
                                         for lista in roubos.values() for r in lista)
                        if ja_roubado:
                            st.markdown(f"❌ {nome_j} - já roubado")
                            continue

                        if st.button(f"Roubar {nome_j} (R$ {valor/2:,.0f})", key=f"{time['id']}_{nome_j}"):
                            saldo_r = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                            if saldo_r < valor / 2:
                                st.warning("⚠️ Saldo insuficiente.")
                                continue

                            novo = roubos.get(id_time, [])
                            novo.append({
                                "nome": nome_j,
                                "posicao": posicao,
                                "valor": valor,
                                "de": time["id"]
                            })
                            roubos[id_time] = novo
                            ja_perderam[time["id"]] = ja_perderam.get(time["id"], 0) + 1

                            saldo_p = supabase.table("times").select("saldo").eq("id", time["id"]).execute().data[0]["saldo"]
                            atualizar_configuracao({"roubos": roubos, "ja_perderam": ja_perderam})
                            supabase.table("times").update({"saldo": saldo_r - valor // 2}).eq("id", id_time).execute()
                            supabase.table("times").update({"saldo": saldo_p + valor // 2}).eq("id", time["id"]).execute()
                            registrar_movimentacao(id_time, nome_j, "Roubo", "Compra", valor // 2)
                            st.success(f"✅ {nome_j} foi roubado com sucesso.")
                            st.experimental_rerun()


            if len(roubos.get(id_time, [])) >= 5:
                st.info("✅ Você já escolheu os 5 jogadores permitidos.")

            if st.button("✅ Finalizar minha participação"):
                concluidos.append(id_time)
                atualizar_configuracao({
                    "concluidos": concluidos,
                    "vez": str(vez + 1),
                    "inicio_vez": str(datetime.utcnow())
                })
                st.experimental_rerun()


        if eh_admin:
            if st.button("⏭️ Pular para o próximo time"):
                atualizar_configuracao({
                    "vez": str(vez + 1),
                    "inicio_vez": str(datetime.utcnow())
                })
                st.experimental_rerun()


    except Exception as e:
        st.warning("Erro ao buscar nome do time da vez ou calcular o tempo.")

# Painel de Bloqueio
if ativo and fase == "bloqueio":
    st.markdown("---")
    st.subheader("🔐 Proteja seus jogadores")

    bloqueios_atual = bloqueios.get(id_time, [])
    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []

    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    jogadores_disponiveis = [j["nome"] for j in elenco if j["nome"] not in nomes_bloqueados]

    if len(nomes_bloqueados) < limite_bloqueios:
        opcoes = [j for j in jogadores_disponiveis if j not in nomes_bloqueados]
        selecionado = st.selectbox("Selecione um jogador para proteger:", [""] + opcoes)

        if selecionado and st.button("🔒 Proteger jogador"):
            jogador_obj = next((j for j in elenco if j["nome"] == selecionado), None)
            if jogador_obj:
                bloqueios_atual.append({
                    "nome": jogador_obj["nome"],
                    "posicao": jogador_obj["posicao"]
                })
                bloqueios[id_time] = bloqueios_atual
                atualizar_configuracao({"bloqueios": bloqueios})
                st.success(f"✅ {jogador_obj['nome']} protegido com sucesso!")
                st.experimental_rerun()

    else:
        st.info(f"✅ Você já protegeu {limite_bloqueios} jogadores.")
        for j in bloqueios_atual:
            st.markdown(f"- 🔐 {j['nome']} ({j['posicao']})")
