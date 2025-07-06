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

# ✅ Função para registrar movimentação financeira
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

# ✅ Função para registrar BID
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

# ✅ Verificar se time está bloqueado do evento
res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
if restricoes.get("roubo", False):
    st.error("🚫 Seu time está proibido de participar do Evento de Roubo.")
    st.stop()

# ✅ Verificar se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

# 🔧 Carrega configuração
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
max_roubos = evento.get("limite_roubos", 5)
max_perdas = evento.get("limite_perdas", 4)

st.title("🕵️ Evento de Roubo - LigaFut")

# 🔃 Atualizar página
if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# 🔧 Admin inicia evento
if eh_admin and not ativo:
    st.subheader("🔧 Iniciar Evento de Roubo")
    limite_bloqueios = st.number_input("❌ Jogadores que cada time pode bloquear", 1, 5, value=3)
    limite_perdas = st.number_input("📉 Jogadores que cada time pode perder", 1, 6, value=4)
    limite_roubos = st.number_input("🕵️ Jogadores que cada time pode roubar", 1, 6, value=5)
    if st.button("🚀 Iniciar Evento"):
        times = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times)
        ordem = [t["id"] for t in times]
        config = {
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem,
            "vez": "0",
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": bloqueios,
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": limite_bloqueios,
            "limite_roubos": limite_roubos,
            "limite_perdas": limite_perdas
        }
        supabase.table("configuracoes").update(config).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado.")
        st.experimental_rerun()

# ✅ Fase de Bloqueio
if ativo and fase == "bloqueio":
    st.subheader("🛡️ Proteja seus jogadores")
    bloqueados = bloqueios.get(id_time, [])
    bloqueados_antes = ultimos_bloqueios.get(id_time, [])
    nomes_bloqueados = [j["nome"] for j in bloqueados + bloqueados_antes]

    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data or []
    livres = [j for j in elenco if j["nome"] not in nomes_bloqueados]
    opcoes = [j["nome"] for j in livres]

    if len(bloqueados) < limite_bloqueios:
        sel = st.multiselect(f"Selecione até {limite_bloqueios - len(bloqueados)} jogadores:", opcoes)
        if sel and st.button("🔐 Confirmar Proteção"):
            novos = [{"nome": j["nome"], "posicao": j["posicao"]} for j in livres if j["nome"] in sel]
            bloqueios[id_time] = bloqueados + novos
            for j in novos:
                supabase.table("jogadores_bloqueados_roubo").insert({
                    "id": str(uuid.uuid4()),
                    "id_time": id_time,
                    "id_jogador": next(e["id"] for e in elenco if e["nome"] == j["nome"]),
                    "temporada": 1,
                    "evento": "roubo",
                    "data_bloqueio": str(datetime.utcnow())
                }).execute()
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("✅ Proteção registrada.")
            st.experimental_rerun()

    if eh_admin and st.button("➡️ Avançar para Fase de Ação"):
        supabase.table("configuracoes").update({"fase": "acao", "vez": "0", "concluidos": []}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# ⚔️ Fase de Ação
if ativo and fase == "acao" and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("⚔️ Sua vez de roubar")
        if id_time in concluidos:
            st.success("Você já finalizou.")
        else:
            st.markdown(f"🕵️ Você pode roubar até **{max_roubos}** jogadores (máximo **2 por time**).")
            times = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
            for t in times:
                id_alvo = t["id"]
                if ja_perderam.get(id_alvo, 0) >= max_perdas:
                    continue
                if len([r for r in roubos.get(id_time, []) if r["de"] == id_alvo]) >= 2:
                    continue
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
                bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]
                ja_roubados = [r["nome"] for sub in roubos.values() for r in sub]
                disponiveis = [j for j in elenco_alvo if j["nome"] not in bloqueados + ja_roubados]

                if disponiveis:
                    with st.expander(f"🎯 Roubar do {t['nome']}"):
                        for j in disponiveis:
                            col1, col2, col3 = st.columns([4, 2, 2])
                            with col1:
                                st.markdown(f"**{j['nome']}** | {j['posicao']} | OVR {j.get('overall','?')} | R$ {j['valor']:,.0f}")
                            with col2:
                                st.write("")
                            with col3:
                                if st.button(f"💰 Roubar {j['nome']}", key=f"{id_alvo}_{j['id']}"):
                                    valor = int(j["valor"])
                                    pago = valor // 2
                                    supabase.table("elenco").delete().eq("id", j["id"]).execute()
                                    supabase.table("elenco").insert({**j, "id_time": id_time}).execute()
                                    registrar_movimentacao(id_time, j["nome"], "saida", pago)
                                    registrar_movimentacao(id_alvo, j["nome"], "entrada", pago)
                                    registrar_bid(id_alvo, id_time, j, "roubo", pago)
                                    roubos.setdefault(id_time, []).append({
                                        "nome": j["nome"], "posicao": j["posicao"], "valor": valor, "de": id_alvo
                                    })
                                    ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1
                                    supabase.table("times").update({"saldo": supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"] - pago}).eq("id", id_time).execute()
                                    supabase.table("times").update({"saldo": supabase.table("times").select("saldo").eq("id", id_alvo).execute().data[0]["saldo"] + pago}).eq("id", id_alvo).execute()
                                    supabase.table("configuracoes").update({
                                        "roubos": roubos, "ja_perderam": ja_perderam
                                    }).eq("id", ID_CONFIG).execute()
                                    st.success("✅ Jogador roubado.")
                                    st.experimental_rerun()
        if st.button("✅ Finalizar minha vez"):
            concluidos.append(id_time)
            supabase.table("configuracoes").update({
                "vez": vez + 1,
                "concluidos": concluidos
            }).eq("id", ID_CONFIG).execute()
            st.experimental_rerun()
    else:
        nome = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.info(f"⏳ Aguardando: {nome}")
        if eh_admin and st.button("⏭️ Pular vez"):
            concluidos.append(id_atual)
            supabase.table("configuracoes").update({
                "vez": vez + 1,
                "concluidos": concluidos
            }).eq("id", ID_CONFIG).execute()
            st.experimental_rerun()

# ✅ Finalizar evento (somente admin)
if ativo and fase == "acao" and vez >= len(ordem) and eh_admin:
    st.success("✅ Evento concluído.")
    if st.button("🚨 Finalizar Evento"):
        supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
        st.experimental_rerun()

# 📊 Relatório final
if evento.get("finalizado"):
    st.title("📊 Relatório Final de Roubos")
    resumo = []
    for id_dest, lista in roubos.items():
        nome_dest = supabase.table("times").select("nome").eq("id", id_dest).execute().data[0]["nome"]
        for j in lista:
            nome_ori = supabase.table("times").select("nome").eq("id", j["de"]).execute().data[0]["nome"]
            resumo.append({
                "🏆 Time que Roubou": nome_dest,
                "👤 Jogador": j["nome"],
                "⚽ Posição": j["posicao"],
                "💰 Valor Pago": f"R$ {int(j['valor']) // 2:,.0f}",
                "😭 Time Roubado": nome_ori
            })
    if resumo:
        st.dataframe(pd.DataFrame(resumo), use_container_width=True)
    else:
        st.info("Nenhum roubo realizado.")


