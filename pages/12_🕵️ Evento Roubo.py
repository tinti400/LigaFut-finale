# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

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

# ✅ Funções utilitárias
def registrar_movimentacao(id_time, jogador, tipo, valor):
    try:
        supabase.table("movimentacoes_financeiras").insert({
            "id": str(uuid.uuid4()),
            "id_time": id_time,
            "tipo": tipo,
            "descricao": f"{tipo.capitalize()} de {jogador}",
            "valor": valor,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar movimentação: {e}")

def registrar_bid(id_time_origem, id_time_destino, jogador, tipo, valor):
    try:
        if not jogador or not isinstance(jogador, dict):
            st.error("❌ Dados do jogador inválidos para o BID.")
            return

        nome_jogador = jogador.get("nome") or "Desconhecido"
        posicao = jogador.get("posicao") or "?"
        valor_final = int(valor) if valor else 0
        tipo_final = tipo or "transferencia"

        supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": nome_jogador,
            "posicao": posicao,
            "valor": valor_final,
            "tipo": tipo_final,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")
# 🔘 Botão para iniciar o evento (aparece apenas para admin se não estiver ativo)
if eh_admin and not ativo:
    st.subheader("🟢 Iniciar Evento de Roubo")
    if st.button("🚀 Iniciar Evento"):
        # Sorteia a ordem dos times participantes
        todos_times = supabase.table("times").select("id", "nome").execute().data
        ordem_sorteada = [t["id"] for t in todos_times]
        random.shuffle(ordem_sorteada)

        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_sorteada,
            "vez": "0",
            "concluidos": [],
            "roubos": {},
            "bloqueios": {},
            "ja_perderam": {},
            "finalizado": False
        }).eq("id", ID_CONFIG).execute()

        st.success("🚀 Evento iniciado com sucesso! Fase de bloqueio liberada.")
        st.experimental_rerun()

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# 🔍 Mostrar jogadores bloqueados do time atual
st.subheader("🛡️ Seus jogadores bloqueados")

bloqueios_atual = bloqueios.get(id_time, [])
ultimos_bloqueios_time = ultimos_bloqueios.get(id_time, [])
todos_bloqueados = bloqueios_atual + ultimos_bloqueios_time

if todos_bloqueados:
    for jogador in todos_bloqueados:
        st.markdown(f"- **{jogador['nome']}** ({jogador['posicao']})")
else:
    st.info("Você ainda não bloqueou nenhum jogador.")
# 🔐 Fase de Bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🔐 Proteja seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    bloqueios_anteriores = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual]
    nomes_anteriores = [j["nome"] for j in bloqueios_anteriores]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    jogadores_livres = [j for j in elenco if j["nome"] not in nomes_bloqueados + nomes_anteriores]
    nomes_livres = [j["nome"] for j in jogadores_livres]

    if len(nomes_bloqueados) < limite_bloqueios:
        max_selecao = limite_bloqueios - len(nomes_bloqueados)
        selecionados = st.multiselect(f"Selecione até {max_selecao} jogador(es):", nomes_livres)

        if selecionados and st.button("🔐 Confirmar proteção"):
            novos_bloqueios = []
            for j in jogadores_livres:
                if j["nome"] in selecionados:
                    bloqueio = {"nome": j["nome"], "posicao": j["posicao"]}
                    novos_bloqueios.append(bloqueio)
                    try:
                        supabase.table("jogadores_bloqueados_roubo").insert({
                            "id": str(uuid.uuid4()),
                            "id_jogador": j["id"],
                            "id_time": id_time,
                            "temporada": 1,
                            "evento": "roubo",
                            "data_bloqueio": str(datetime.utcnow())
                        }).execute()
                    except Exception as e:
                        st.warning(f"Erro ao salvar bloqueio no histórico: {e}")

            bloqueios[id_time] = bloqueios_atual + novos_bloqueios
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("✅ Proteção realizada.")
            st.experimental_rerun()

    if eh_admin and st.button("👉 Iniciar Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()
# 🎯 Fase de Ação
if ativo and fase == "acao":
    vez_atual = int(vez)
    if vez_atual >= len(ordem):
        st.success("✅ Todas as rodadas de ação foram concluídas.")
    else:
        id_time_vez = ordem[vez_atual]
        nome_time_vez = next((t["nome"] for t in times if t["id"] == id_time_vez), f"Time {id_time_vez}")

        if id_time == id_time_vez:
            st.markdown(f"### 👊 É sua vez de roubar jogadores ({nome_time_vez})")
            st.markdown(f"📌 Você pode roubar até **{limite_roubos_por_time} jogadores** no total.")
            st.markdown("Cada time pode perder no máximo **4 jogadores** no evento.")
            st.markdown("Você pode roubar no máximo **2 jogadores de um mesmo time**.")

            # Ver times adversários
            for t in times:
                alvo_id = t["id"]
                if alvo_id == id_time:
                    continue

                # Checa se alvo já perdeu 4
                perdidos = ja_perderam.get(alvo_id, [])
                if len(perdidos) >= 4:
                    continue

                # Quantos jogadores já roubou desse time?
                roubos_atuais = roubos.get(id_time, [])
                do_alvo = [j for j in roubos_atuais if j["de"] == alvo_id]
                if len(do_alvo) >= 2:
                    continue

                elenco = supabase.table("elenco").select("*").eq("id_time", alvo_id).execute().data or []
                bloqueados = bloqueios.get(alvo_id, []) + ultimos_bloqueios.get(alvo_id, [])
                nomes_bloqueados = [j["nome"] for j in bloqueados]
                disponiveis = [j for j in elenco if j["nome"] not in nomes_bloqueados]

                if not disponiveis:
                    continue

                with st.expander(f"🔓 Elenco disponível de {t['nome']}"):
                    for jogador in disponiveis:
                        nome = jogador["nome"]
                        pos = jogador["posicao"]
                        val = jogador["valor"]

                        col1, col2 = st.columns([4, 1])
                        col1.markdown(f"**{nome}** ({pos}) - R$ {val:,.0f}")

                        if col2.button("💰 Roubar", key=f"roubar_{nome}"):
                            saldo_m = supabase.table("times").select("saldo").eq("id", id_time).execute().data
                            saldo_atual = saldo_m[0]["saldo"] if saldo_m else 0
                            valor_roubo = int(val * 0.5)  # 💸 50% do valor do jogador

                            if saldo_atual < valor_roubo:
                                st.error("❌ Saldo insuficiente.")
                            else:
                                # Atualiza saldos e histórico
                                supabase.table("times").update({"saldo": saldo_atual - valor_roubo}).eq("id", id_time).execute()
                                registrar_movimentacao(id_time, nome, "compra", -valor_roubo)
                                registrar_movimentacao(alvo_id, nome, "venda", valor_roubo)

                                # Adiciona ao elenco
                                novo = jogador.copy()
                                novo["id"] = str(uuid.uuid4())
                                novo["id_time"] = id_time
                                supabase.table("elenco").insert(novo).execute()

                                # Remove do alvo
                                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                                # Bid
                                registrar_bid(alvo_id, id_time, jogador, "roubo", valor_roubo)

                                # Atualiza histórico
                                ja_perderam.setdefault(alvo_id, []).append(nome)
                                roubos.setdefault(id_time, []).append({
                                    "nome": nome,
                                    "posicao": pos,
                                    "valor": val,
                                    "de": alvo_id
                                })

                                supabase.table("configuracoes").update({
                                    "ja_perderam": ja_perderam,
                                    "roubos": roubos
                                }).eq("id", ID_CONFIG).execute()

                                st.success(f"✅ Jogador {nome} roubado com sucesso por R$ {valor_roubo:,.0f}!")
                                st.experimental_rerun()
            # ✅ Botão para encerrar vez do time
            if st.button("➡️ Encerrar minha vez"):
                concluidos.append(id_time)
                vez_nova = vez_atual + 1

                supabase.table("configuracoes").update({
                    "concluidos": concluidos,
                    "vez": str(vez_nova)
                }).eq("id", ID_CONFIG).execute()

                st.success("✅ Sua vez foi encerrada. Próximo time poderá roubar.")
                st.experimental_rerun()

        else:
            st.info(f"Aguarde sua vez. Agora é a vez de **{nome_time_vez}**.")

# ✅ Fase Final - Mostrar resumo e botão para finalizar evento
if ativo and fase == "acao" and int(vez) >= len(ordem):
    st.subheader("📋 Resumo do Evento de Roubo")
    resumo = []

    for time_id, jogadores in roubos.items():
        nome = next((t["nome"] for t in times if t["id"] == time_id), f"Time {time_id}")
        for j in jogadores:
            alvo_nome = next((t["nome"] for t in times if t["id"] == j["de"]), f"Time {j['de']}")
            resumo.append({
                "Time que Roubou": nome,
                "Jogador": j["nome"],
                "Posição": j["posicao"],
                "Valor Original": f"R$ {j['valor']:,.0f}",
                "Pago (50%)": f"R$ {j['valor'] * 0.5:,.0f}",
                "Do Time": alvo_nome
            })

    if resumo:
        df = pd.DataFrame(resumo)
        st.dataframe(df)

    if eh_admin and st.button("🔚 Finalizar Evento"):
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento finalizado.")
        st.experimental_rerun()
            # ✅ Botão para encerrar vez do time
            if st.button("➡️ Encerrar minha vez"):
                concluidos.append(id_time)
                vez_nova = vez_atual + 1

                supabase.table("configuracoes").update({
                    "concluidos": concluidos,
                    "vez": str(vez_nova)
                }).eq("id", ID_CONFIG).execute()

                st.success("✅ Sua vez foi encerrada. Próximo time poderá roubar.")
                st.experimental_rerun()

        else:
            st.info(f"Aguarde sua vez. Agora é a vez de **{nome_time_vez}**.")

# ✅ Fase Final - Mostrar resumo e botão para finalizar evento
if ativo and fase == "acao" and int(vez) >= len(ordem):
    st.subheader("📋 Resumo do Evento de Roubo")
    resumo = []

    for time_id, jogadores in roubos.items():
        nome = next((t["nome"] for t in times if t["id"] == time_id), f"Time {time_id}")
        for j in jogadores:
            alvo_nome = next((t["nome"] for t in times if t["id"] == j["de"]), f"Time {j['de']}")
            resumo.append({
                "Time que Roubou": nome,
                "Jogador": j["nome"],
                "Posição": j["posicao"],
                "Valor Original": f"R$ {j['valor']:,.0f}",
                "Pago (50%)": f"R$ {j['valor'] * 0.5:,.0f}",
                "Do Time": alvo_nome
            })

    if resumo:
        df = pd.DataFrame(resumo)
        st.dataframe(df)

    if eh_admin and st.button("🔚 Finalizar Evento"):
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento finalizado.")
        st.experimental_rerun()


