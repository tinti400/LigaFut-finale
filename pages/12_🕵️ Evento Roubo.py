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

        resultado = supabase.table("bid_transferencias").insert({
            "id": str(uuid.uuid4()),
            "id_time_origem": id_time_origem,
            "id_time_destino": id_time_destino,
            "nome_jogador": nome_jogador,
            "posicao": posicao,
            "valor": valor_final,
            "tipo": tipo_final,
            "data": str(datetime.utcnow())
        }).execute()

        st.success(f"✅ Jogador registrado no BID: {nome_jogador}")
        print("📦 BID OK:", resultado)

    except Exception as e:
        st.error(f"❌ Erro ao registrar no BID: {e}")
# 🚫 Verifica restrições
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
    if restricoes.get("roubo", False):
        st.error("🚫 Seu time está proibido de participar do Evento de Roubo.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

st.title("🕵️ Evento de Roubo - LigaFut")

# 🔧 Configuração do evento
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"
evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]

ativo = evento.get("ativo", False)
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", "0"))
concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})
limite_bloqueios = evento.get("limite_bloqueios", 3)

# ✅ Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

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

# 🔐 Início do evento (admin)
if eh_admin:
    st.subheader("🔐 Configurar Limite de Bloqueio")
    novo_limite = st.number_input("Quantos jogadores cada time pode bloquear?", min_value=1, max_value=5, value=3, step=1)
    if st.button("✅ Salvar limite e iniciar evento"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        palmeiras = next((t for t in times_data if t["nome"].strip().lower() == "palmeiras"), None)
        restantes = [t for t in times_data if t != palmeiras]
        random.shuffle(restantes)
        nova_ordem = [palmeiras["id"]] + [t["id"] for t in restantes] if palmeiras else [t["id"] for t in times_data]
        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": nova_ordem,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_limite
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado.")
        st.experimental_rerun()

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
# 🎯 Fase de Ação (Roubo)
if ativo and fase == "acao":
    st.subheader("🎯 Fase de Roubo em andamento")

    if vez >= len(ordem):
        st.success("✅ Todos os times passaram.")
        if eh_admin and st.button("✅ Finalizar Evento"):
            supabase.table("configuracoes").update({"ativo": False, "fase": "concluido"}).eq("id", ID_CONFIG).execute()
            st.success("Evento de Roubo finalizado com sucesso!")
        st.stop()

    id_vez = ordem[vez]
    nome_vez = supabase.table("times").select("nome").eq("id", id_vez).execute().data[0]["nome"]

    st.markdown(f"🎲 Agora é a vez de **{nome_vez}**")

    if id_vez != id_time:
        st.warning("⏳ Aguarde sua vez.")
        st.stop()

    times_data = supabase.table("times").select("id", "nome").execute().data
    times_adversarios = [t for t in times_data if t["id"] != id_time]

    time_alvo = st.selectbox("Selecione um time para roubar jogador", [t["nome"] for t in times_adversarios])
    alvo = next((t for t in times_adversarios if t["nome"] == time_alvo), None)

    if not alvo:
        st.warning("Selecione um time válido.")
        st.stop()

    id_alvo = alvo["id"]

    if ja_perderam.get(id_alvo, 0) >= 4:
        st.error("❌ Esse time já perdeu 4 jogadores.")
        st.stop()

    if ja_perderam.get(id_alvo, 0) >= 2 and ja_perderam.get(id_alvo, 0) > ja_perderam.get(id_time, 0):
        st.error("❌ Você já roubou 2 jogadores desse time.")
        st.stop()

    bloqueados_alvo = bloqueios.get(id_alvo, []) + ultimos_bloqueios.get(id_alvo, [])
    nomes_bloqueados = [j["nome"] for j in bloqueados_alvo]

    elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data or []
    elenco_disponivel = [j for j in elenco_alvo if j["nome"] not in nomes_bloqueados]

    if not elenco_disponivel:
        st.warning("Nenhum jogador disponível para roubo.")
        st.stop()

    nome_jogador = st.selectbox("Escolha o jogador para roubar", [j["nome"] for j in elenco_disponivel])
    jogador = next((j for j in elenco_disponivel if j["nome"] == nome_jogador), None)

    if jogador:
        st.markdown(f"**Nome:** {jogador['nome']}  \n**Posição:** {jogador['posicao']}  \n**Valor:** R$ {jogador['valor']:,}")

        if st.button("💸 Confirmar Roubo"):
            valor = int(jogador["valor"]) // 2
            # Remover do time antigo
            supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
            # Adicionar no time atual
            novo_id = str(uuid.uuid4())
            supabase.table("elenco").insert({
                "id": novo_id,
                "id_time": id_time,
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": jogador["valor"]
            }).execute()
            # Registrar movimentações
            registrar_movimentacao(id_time, jogador["nome"], "compra", valor)
            registrar_movimentacao(id_alvo, jogador["nome"], "venda", valor)
            registrar_bid(id_alvo, id_time, jogador, "roubo", valor)

            # Atualizar saldo dos dois
            saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
            novo_saldo = int(saldo_atual) - valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            saldo_alvo = supabase.table("times").select("saldo").eq("id", id_alvo).execute().data[0]["saldo"]
            novo_saldo_alvo = int(saldo_alvo) + valor
            supabase.table("times").update({"saldo": novo_saldo_alvo}).eq("id", id_alvo).execute()

            # Atualizar registros do evento
            roubos.setdefault(id_time, []).append(jogador)
            ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
            vez_atual = vez + 1
            concluidos.append(id_time)

            supabase.table("configuracoes").update({
                "vez": str(vez_atual),
                "concluidos": concluidos,
                "ja_perderam": ja_perderam,
                "roubos": roubos
            }).eq("id", ID_CONFIG).execute()

            st.success(f"✅ {jogador['nome']} roubado com sucesso!")
            st.experimental_rerun()
# 📋 Resumo do Evento
if fase in ["acao", "concluido"] and roubos:
    st.subheader("📋 Resumo dos Roubos")
    resumo = []
    for time_id, lista in roubos.items():
        nome = next((t["nome"] for t in times_data if t["id"] == time_id), f"Time {time_id}")
        for jogador in lista:
            resumo.append({
                "Time que Roubou": nome,
                "Jogador": jogador["nome"],
                "Posição": jogador["posicao"],
                "Overall": jogador["overall"],
                "Valor": f"R$ {jogador['valor']:,}"
            })

    if resumo:
        df_resumo = pd.DataFrame(resumo)
        st.data_editor(df_resumo, use_container_width=True)
    else:
        st.info("Nenhum roubo registrado até agora.")
