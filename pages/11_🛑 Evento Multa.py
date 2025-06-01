# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random
from utils import registrar_movimentacao

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
usuario_email = st.session_state["usuario"]

st.title("🚨 Evento de Multa - LigaFut")

# Verifica se é admin
admin_data = supabase.table("usuarios").select("administrador").eq("usuario", usuario_email).execute().data
eh_admin = admin_data and admin_data[0].get("administrador", False)

# ID fixo da configuração
ID_CONFIG = "evento_multa"

# 🔄 Busca configuração atual
conf = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data
conf = conf[0] if conf else {}

ativo = conf.get("ativo", False)
fase = conf.get("fase", "bloqueio")
ordem = conf.get("ordem", [])
vez = conf.get("vez", 0)
bloqueios = conf.get("bloqueios", {})
roubos = conf.get("roubos", {})
concluidos = conf.get("concluidos", [])
ja_perderam = conf.get("ja_perderam", {})
finalizado = conf.get("finalizado", False)

# -------------------- ADMIN --------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")

    if not ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            todos_times = supabase.table("times").select("id").execute().data
            nova_ordem = [t["id"] for t in todos_times]
            random.shuffle(nova_ordem)

            supabase.table("configuracoes").upsert({
                "id": ID_CONFIG,
                "ativo": True,
                "fase": "bloqueio",
                "ordem": nova_ordem,
                "vez": 0,
                "bloqueios": {},
                "roubos": {},
                "concluidos": [],
                "ja_perderam": {},
                "finalizado": False
            }).execute()
            st.success("Evento de multa iniciado com sucesso.")
            st.rerun()
    else:
        if st.button("🛑 Encerrar Evento"):
            supabase.table("configuracoes").upsert({
                "id": ID_CONFIG,
                "ativo": False,
                "finalizado": True
            }).execute()
            st.success("Evento encerrado.")
            st.rerun()

# -------------------- STATUS --------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase atual: {fase.upper()}")

    if fase == "bloqueio":
        st.subheader("⛔ Bloqueie até 4 jogadores do seu elenco")

        elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
        bloqueados = bloqueios.get(id_time, [])
        nomes_bloqueados = [f"{j['nome']} - {j['posicao']}" for j in bloqueados]

        opcoes = [f"{j['nome']} - {j['posicao']}" for j in elenco if f"{j['nome']} - {j['posicao']}" not in nomes_bloqueados]

        escolhidos = st.multiselect("Jogadores para bloquear:", opcoes, default=nomes_bloqueados, max_selections=4)

        if st.button("🔐 Salvar bloqueios"):
            novos = [j for j in elenco if f"{j['nome']} - {j['posicao']}" in escolhidos]
            bloqueios[id_time] = novos
            supabase.table("configuracoes").upsert({"id": ID_CONFIG, "bloqueios": bloqueios}).execute()
            st.success("Bloqueios salvos.")
            st.rerun()

        if eh_admin and st.button("➡️ Avançar para Fase de Ação"):
            supabase.table("configuracoes").upsert({"id": ID_CONFIG, "fase": "acao"}).execute()
            st.success("Fase de ação iniciada.")
            st.rerun()

    elif fase == "acao":
        st.subheader("🎯 Ordem de Vez")
        for i, tid in enumerate(ordem):
            nome = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            if tid in concluidos:
                st.markdown(f"🟢 {nome}")
            elif i == vez:
                st.markdown(f"🔹 {nome} (vez atual)")
            else:
                st.markdown(f"⚪ {nome}")

        if vez < len(ordem) and ordem[vez] == id_time:
            st.success("🏸 É sua vez! Você pode roubar até 5 jogadores.")

            times = supabase.table("times").select("id", "nome", "saldo").execute().data
            time_map = {t["id"]: t for t in times}

            for tid, tinfo in time_map.items():
                if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                    continue

                elenco_adversario = supabase.table("elenco").select("*").eq("id_time", tid).execute().data
                if not elenco_adversario:
                    continue

                with st.expander(f"🎯 {tinfo['nome']}"):
                    for jogador in elenco_adversario:
                        nome_jogador = jogador["nome"]
                        posicao = jogador["posicao"]
                        valor = jogador["valor"]

                        bloqueado = any(j["nome"] == nome_jogador for j in bloqueios.get(tid, []))
                        ja_roubado = any(nome_jogador == r.get("nome") and r.get("de") == tid
                                         for rlist in roubos.values() for r in rlist)

                        if bloqueado or ja_roubado:
                            st.markdown(f"🔒 {nome_jogador} - {posicao} (R$ {valor:,.0f})")
                            continue

                        if st.button(f"💸 Pagar multa por {nome_jogador} - R$ {valor:,.0f}", key=f"{tid}_{nome_jogador}"):
                            saldo_atual = time_map[id_time]["saldo"]
                            if saldo_atual < valor:
                                st.error("Saldo insuficiente.")
                                st.stop()

                            # Registrar no histórico
                            novo = roubos.get(id_time, [])
                            novo.append({"nome": nome_jogador, "posicao": posicao, "valor": valor, "de": tid})
                            roubos[id_time] = novo

                            # Atualiza saldo
                            novo_saldo_comprador = saldo_atual - valor
                            novo_saldo_vendedor = time_map[tid]["saldo"] + valor

                            supabase.table("times").update({"saldo": novo_saldo_comprador}).eq("id", id_time).execute()
                            supabase.table("times").update({"saldo": novo_saldo_vendedor}).eq("id", tid).execute()

                            # Remover do time antigo
                            supabase.table("elenco").delete().eq("id_time", tid).eq("nome", nome_jogador).execute()

                            # Adicionar no novo time
                            supabase.table("elenco").insert({
                                "id_time": id_time,
                                "nome": nome_jogador,
                                "posicao": posicao,
                                "overall": jogador["overall"],
                                "valor": valor
                            }).execute()

                            # Atualiza contagem de perdas
                            ja_perderam[tid] = ja_perderam.get(tid, 0) + 1

                            # Movimentações
                            registrar_movimentacao(supabase, id_time, nome_jogador, "Multa", "Saída", valor)
                            registrar_movimentacao(supabase, tid, nome_jogador, "Multa", "Entrada", valor)

                            # Salva no banco
                            supabase.table("configuracoes").upsert({
                                "id": ID_CONFIG,
                                "roubos": roubos,
                                "ja_perderam": ja_perderam
                            }).execute()

                            st.success(f"{nome_jogador} comprado com sucesso!")
                            st.rerun()

            if len(roubos.get(id_time, [])) >= 5:
                st.info("Você já realizou as 5 compras permitidas.")

            if st.button("✅ Finalizar minha vez"):
                concluidos.append(id_time)
                supabase.table("configuracoes").upsert({
                    "id": ID_CONFIG,
                    "concluidos": concluidos,
                    "vez": vez + 1
                }).execute()
                st.success("Sua vez foi finalizada.")
                st.rerun()

        elif eh_admin and vez < len(ordem):
            if st.button("⏩ Pular vez do time atual"):
                supabase.table("configuracoes").upsert({"id": ID_CONFIG, "vez": vez + 1}).execute()
                st.rerun()

    elif finalizado:
        st.success("✅ Evento finalizado. Veja o resumo:")

        for tid, acoes in roubos.items():
            nome_time = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            st.markdown(f"### 🔷 {nome_time}")
            for j in acoes:
                de_nome = supabase.table("times").select("nome").eq("id", j["de"]).execute().data[0]["nome"]
                st.markdown(f"- {j['nome']} ({j['posicao']}) roubado do {de_nome}")

else:
    st.warning("⚠️ Evento de multa não está ativo.")
