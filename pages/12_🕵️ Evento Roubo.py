# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd

st.set_page_config(page_title="🕵️ Evento de Roubo - LigaFut", layout="wide")

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

# 🔄 Buscar configurações do evento
res = supabase.table("configuracoes").select("*").execute()
config = res.data[0] if res.data else {}

fase = config.get("fase", "sorteio")
ordem = config.get("ordem", [])
vez = config.get("vez", 0)
if fase == "sorteio":
    st.subheader("🎲 Sorteio da Ordem dos Times")

    if st.button("🔀 Realizar Sorteio da Ordem"):
        res_times = supabase.table("times").select("id", "nome").execute()
        times = res_times.data
        random.shuffle(times)
        ordem_ids = [t["id"] for t in times]

        supabase.table("configuracoes").update({
            "ordem": ordem_ids,
            "vez": 0,
            "fase": "protecao"
        }).eq("id", config["id"]).execute()

        st.success("✅ Sorteio realizado com sucesso. Ordem definida.")
        st.rerun()

    else:
        st.warning("⚠️ Clique no botão acima para sortear a ordem dos times.")
elif fase == "protecao":
    st.subheader("🛡️ Proteja até 4 jogadores do seu time")

    # Buscar elenco
    elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
    protegidos = config.get("bloqueios", {}).get(id_time, [])

    selecionados = st.multiselect(
        "Selecione até 4 jogadores para proteger",
        options=[j["nome"] for j in elenco],
        default=protegidos
    )

    if st.button("✅ Confirmar Proteção"):
        if len(selecionados) > 4:
            st.warning("⚠️ Você só pode proteger até 4 jogadores.")
        else:
            bloqueios = config.get("bloqueios", {})
            bloqueios[id_time] = selecionados

            supabase.table("configuracoes").update({
                "bloqueios": bloqueios
            }).eq("id", config["id"]).execute()

            st.success("✅ Jogadores protegidos com sucesso.")
            st.rerun()
elif fase == "acao":
    st.subheader("🕵️ Ação: Roube um jogador de outro time")

    if vez >= len(ordem):
        st.success("✅ Todos os times já roubaram. Finalizando evento.")
        supabase.table("configuracoes").update({
            "fase": "final"
        }).eq("id", config["id"]).execute()
        st.rerun()

    id_time_da_vez = ordem[vez]
    if id_time != id_time_da_vez:
        st.info("⏳ Aguarde sua vez. Outro time está realizando sua ação.")
        st.stop()

    # Selecionar time a ser roubado
    st.markdown("### 🧩 Escolha um time para roubar um jogador:")
    res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
    times_roubo = res_times.data

    time_alvo = st.selectbox("Selecione o time:", [t["nome"] for t in times_roubo])
    time_selecionado = next((t for t in times_roubo if t["nome"] == time_alvo), None)

    # Buscar jogadores do time alvo
    jogadores_alvo = supabase.table("elenco").select("*").eq("id_time", time_selecionado["id"]).execute().data
    bloqueados = config.get("bloqueios", {}).get(time_selecionado["id"], [])
    disponiveis = [j for j in jogadores_alvo if j["nome"] not in bloqueados]

    jogador_roubo = st.selectbox("Escolha o jogador:", [j["nome"] for j in disponiveis])

    if st.button("💥 Roubar Jogador"):
        jogador_selecionado = next(j for j in disponiveis if j["nome"] == jogador_roubo)

        # Atualizar elenco
        supabase.table("elenco").update({"id_time": id_time}).eq("id", jogador_selecionado["id"]).execute()

        # Atualizar saldo (50% do valor vai para time roubado)
        valor = jogador_selecionado["valor"]
        supabase.table("times").update({"saldo": f"saldo + {int(valor * 0.5)}"}).eq("id", time_selecionado["id"]).execute()
        supabase.table("times").update({"saldo": f"saldo - {int(valor * 0.5)}"}).eq("id", id_time).execute()

        # Atualizar `configuracoes`
        ja_roubaram = config.get("roubos", {})
        ja_roubaram.setdefault(id_time, []).append(jogador_selecionado["nome"])

        ja_perderam = config.get("ja_perderam", {})
        ja_perderam.setdefault(time_selecionado["id"], []).append(jogador_selecionado["nome"])

        supabase.table("configuracoes").update({
            "vez": vez + 1,
            "roubos": ja_roubaram,
            "ja_perderam": ja_perderam
        }).eq("id", config["id"]).execute()

        st.success(f"✅ Você roubou o jogador {jogador_roubo} do time {time_alvo}!")
        st.rerun()
elif fase == "final":
    st.success("🎉 Evento de Roubo encerrado com sucesso!")

    st.markdown("### 🔚 Resumo do Evento:")
    st.json({
        "Roubos realizados": config.get("roubos", {}),
        "Times que perderam jogadores": config.get("ja_perderam", {})
    })
