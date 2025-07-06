# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verificar login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# Funções utilitárias
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
        supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": jogador["nome"],
            "posicao": jogador["posicao"],
            "valor": valor,
            "tipo": tipo,
            "data": str(datetime.utcnow())
        }).execute()
    except Exception as e:
        st.error(f"Erro ao registrar no BID: {e}")

# Carrega dados do evento
ID_CONFIG = "evento_roubo"
res = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
if not res.data:
    st.error("Evento de roubo não configurado.")
    st.stop()
config = res.data[0]

ativo = config.get("ativo", False)
fase = config.get("fase", "sorteio")
ordem = config.get("ordem", [])
vez = int(config.get("vez", 0))
bloqueios = config.get("bloqueios", {})
ultimos_bloqueios = config.get("ultimos_bloqueios", {})
ja_perderam = config.get("ja_perderam", {})
roubos = config.get("roubos", {})
finalizado = config.get("finalizado", False)

# Verifica admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

st.title("🕵️ Evento de Roubo - LigaFut")

# FASE 1: SORTEIO
if eh_admin and not ativo and st.button("🚀 Iniciar Evento de Roubo"):
    times = supabase.table("times").select("id").execute().data
    ordem_sorteada = [t["id"] for t in times]
    random.shuffle(ordem_sorteada)
    supabase.table("configuracoes").update({
        "ativo": True,
        "fase": "bloqueio",
        "ordem": ordem_sorteada,
        "vez": 0,
        "bloqueios": {},
        "ultimos_bloqueios": bloqueios,
        "ja_perderam": {},
        "roubos": {},
        "finalizado": False
    }).eq("id", ID_CONFIG).execute()
    st.success("Evento iniciado. Fase de bloqueio liberada.")
    st.rerun()

# FASE 2: BLOQUEIO
if ativo and fase == "bloqueio":
    st.subheader("🔐 Bloqueie seus jogadores")
    bloqueios_atual = bloqueios.get(id_time, [])
    ultimos = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueios_atual + ultimos]
    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
    livres = [j for j in elenco if j["nome"] not in nomes_bloqueados]

    max_bloqueios = 4 - len(bloqueios_atual)
    nomes_livres = [j["nome"] for j in livres]
    selecionados = st.multiselect(f"Selecione até {max_bloqueios} jogador(es) para bloquear:", nomes_livres)

    if selecionados and st.button("🔒 Bloquear selecionados"):
        novos = [
            {"nome": j["nome"], "posicao": j["posicao"]}
            for j in livres if j["nome"] in selecionados
        ]
        bloqueios[id_time] = bloqueios_atual + novos
        supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
        st.success("Jogadores bloqueados com sucesso!")
        st.rerun()

    if eh_admin and st.button("➡️ Encerrar Bloqueios e Começar Fase de Roubo"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": 0}).eq("id", ID_CONFIG).execute()
        st.success("Fase de roubo iniciada.")
        st.rerun()

# CONTINUA NA PRÓXIMA RESPOSTA: FASE 3 (AÇÃO) E FASE FINAL (ENCERRAMENTO E RESUMO)
# 🎯 Fase 3 - Ação (Roubo)
if ativo and fase == "acao":
    st.subheader("🎯 Fase de Ação - Roubo de Jogadores")

    if vez >= len(ordem):
        st.success("✅ Todos os times finalizaram suas ações de roubo.")
        if eh_admin:
            if st.button("🚨 Finalizar Evento"):
                supabase.table("configuracoes").update({
                    "ativo": False,
                    "fase": "finalizado",
                    "finalizado": True
                }).eq("id", ID_CONFIG).execute()
                st.experimental_rerun()
        st.stop()

    id_time_vez = ordem[vez]
    if id_time_vez != id_time and not eh_admin:
        nome_time_vez = supabase.table("times").select("nome").eq("id", id_time_vez).execute().data[0]["nome"]
        st.warning(f"⏳ Aguarde sua vez. Agora é a vez de **{nome_time_vez}**.")
        st.stop()

    st.success("🎯 Agora é sua vez de realizar até 5 roubos (de times diferentes).")

    # Evitar repetir times
    times_ja_roubados = roubos.get(id_time, [])
    todos_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
    times_disponiveis = [t for t in todos_times if t["id"] not in ja_perderam or len(ja_perderam[t["id"]]) < 4]

    if not times_disponiveis:
        st.info("❌ Nenhum time disponível para roubo.")
    else:
        alvo_nome = st.selectbox("🔍 Selecione um time para visualizar o elenco:", [t["nome"] for t in times_disponiveis])
        alvo_id = next((t["id"] for t in times_disponiveis if t["nome"] == alvo_nome), None)

        if alvo_id:
            elenco_alvo = supabase.table("elenco").select("*").eq("id_time", alvo_id).execute().data or []
            bloqueados = bloqueios.get(alvo_id, [])
            nomes_bloqueados = [j["nome"] for j in bloqueados]
            ja_roubados_deste = ja_perderam.get(alvo_id, [])
            if len(ja_roubados_deste) >= 2:
                st.warning("⚠️ Este time já perdeu dois jogadores para o seu clube. Selecione outro.")
            else:
                for jogador in elenco_alvo:
                    nome = jogador["nome"]
                    posicao = jogador["posicao"]
                    valor = jogador["valor"]

                    protegido = nome in nomes_bloqueados
                    if protegido:
                        st.markdown(f"🔒 **{nome}** ({posicao}) - Protegido")
                        continue

                    col1, col2 = st.columns([5, 1])
                    col1.markdown(f"**{nome}** ({posicao}) - 💰 R$ {valor:,.0f}")
                    if col2.button("💸 Roubar", key=f"roubar_{jogador['id']}"):
                        saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                        if saldo < valor:
                            st.error("❌ Saldo insuficiente.")
                        else:
                            novo_id = str(uuid.uuid4())
                            jogador_copy = jogador.copy()
                            jogador_copy.update({"id": novo_id, "id_time": id_time})

                            # Transação financeira
                            supabase.table("times").update({"saldo": saldo - valor}).eq("id", id_time).execute()
                            registrar_movimentacao(id_time, nome, "compra", -valor)
                            registrar_movimentacao(alvo_id, nome, "venda", valor // 2)

                            # BID
                            registrar_bid(alvo_id, id_time, jogador, "roubo", valor)

                            # Inserir novo jogador e remover do alvo
                            supabase.table("elenco").insert(jogador_copy).execute()
                            supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                            # Histórico de perdas e roubo
                            ja_perderam.setdefault(alvo_id, []).append(nome)
                            roubos.setdefault(id_time, []).append({
                                "nome": nome,
                                "posicao": posicao,
                                "valor": valor,
                                "de": alvo_id
                            })

                            supabase.table("configuracoes").update({
                                "ja_perderam": ja_perderam,
                                "roubos": roubos
                            }).eq("id", ID_CONFIG).execute()

                            st.success(f"✅ Jogador {nome} roubado com sucesso!")
                            st.experimental_rerun()

    if st.button("✅ Finalizar minha rodada"):
        if id_time not in concluidos:
            concluidos.append(id_time)
            supabase.table("configuracoes").update({
                "concluidos": concluidos,
                "vez": vez + 1
            }).eq("id", ID_CONFIG).execute()
            st.success("✅ Sua vez foi finalizada.")
            st.experimental_rerun()

# 📊 Fase Final - Resumo e Encerramento
if evento.get("finalizado"):
    st.subheader("📊 Resumo Final do Evento de Roubo")
    resumo = []

    times_data = supabase.table("times").select("id", "nome").execute().data
    mapa_times = {t["id"]: t["nome"] for t in times_data}

    for id_roubador, jogadores in roubos.items():
        for j in jogadores:
            nome_roubador = mapa_times.get(id_roubador, "Desconhecido")
            nome_roubado = mapa_times.get(j["de"], "Desconhecido")
            resumo.append({
                "🟢 Quem Roubou": nome_roubador,
                "👤 Jogador": j["nome"],
                "⚽ Posição": j["posicao"],
                "💰 Valor Pago": f"R$ {j['valor'] // 2:,.0f}",
                "🔴 Time Roubado": nome_roubado
            })

    df = pd.DataFrame(resumo)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("Nenhum jogador foi roubado.")

    if eh_admin:
        st.subheader("🔁 Reiniciar Evento")
        if st.button("🧹 Apagar dados e reiniciar evento"):
            supabase.table("configuracoes").update({
                "ativo": False,
                "fase": "sorteio",
                "ordem": [],
                "vez": "0",
                "roubos": {},
                "bloqueios": {},
                "ultimos_bloqueios": bloqueios,
                "ja_perderam": {},
                "concluidos": [],
                "finalizado": False
            }).eq("id", ID_CONFIG).execute()
            st.success("Evento reiniciado com sucesso.")
            st.experimental_rerun()
