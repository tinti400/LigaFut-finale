# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# ✅ Funções
def registrar_movimentacao(id_time, jogador, tipo, valor):
    supabase.table("movimentacoes_financeiras").insert({
        "id": str(uuid.uuid4()),
        "id_time": id_time,
        "tipo": tipo,
        "descricao": f"{tipo.capitalize()} de {jogador}",
        "valor": valor,
        "data": str(datetime.utcnow())
    }).execute()

def registrar_bid(id_origem, id_destino, jogador, tipo, valor):
    supabase.table("bid_transferencias").insert({
        "id": str(uuid.uuid4()),
        "id_time_origem": id_origem,
        "id_time_destino": id_destino,
        "nome_jogador": jogador.get("nome"),
        "posicao": jogador.get("posicao"),
        "valor": int(valor),
        "tipo": tipo,
        "data": str(datetime.utcnow())
    }).execute()

# ⚙️ Configuração do evento
ID_CONFIG = "evento_multa"
evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]

ativo = evento.get("ativo", False)
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", "0"))
concluidos = evento.get("concluidos", [])
ja_perderam = evento.get("ja_perderam", {})
multa_compras = evento.get("multa_compras", {})

# ⚙️ Admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0]["administrador"]

if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()

# 🔐 Início do evento
if eh_admin and not ativo:
    if st.button("🚨 Iniciar Evento de Multa"):
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        nova_ordem = [t["id"] for t in times_data]
        supabase.table("configuracoes").update({
            "ativo": True,
            "ordem": nova_ordem,
            "vez": "0",
            "concluidos": [],
            "ja_perderam": {},
            "multa_compras": {}
        }).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento de Multa iniciado.")
        st.experimental_rerun()

# 🔥 Fase de ação
if ativo and vez < len(ordem):
    id_atual = ordem[vez]
    if id_time == id_atual:
        st.header("💥 Sua vez de pagar multas")
        if id_time in concluidos:
            st.info("✅ Você já finalizou.")
        else:
            st.info("Você pode comprar até 5 jogadores. Máximo de 2 do mesmo time.")

            times_data = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
            times_dict = {t["id"]: t["nome"] for t in times_data}
            time_alvo_nome = st.selectbox("Selecione o time alvo:", list(times_dict.values()))
            id_alvo = next(i for i, n in times_dict.items() if n == time_alvo_nome)

            if ja_perderam.get(id_alvo, 0) >= 5:
                st.warning("❌ Esse time já perdeu 5 jogadores.")
            else:
                if len([r for r in multa_compras.get(id_time, []) if r["de"] == id_alvo]) >= 2:
                    st.warning("❌ Já comprou 2 jogadores desse time.")
                    st.stop()

                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
                ja_comprados = [r["nome"] for sub in multa_compras.values() for r in sub]
                disponiveis = [j for j in elenco_alvo if j["nome"] not in ja_comprados]

                opcoes_jogadores = {
                    f"{j['nome']} | {j['posicao']} | OVR: {j.get('overall', '?')} | R$ {j['valor']:,.0f}": j
                    for j in disponiveis
                }

                jogador_selecionado = st.selectbox("Escolha um jogador:", [""] + list(opcoes_jogadores.keys()))

                if jogador_selecionado:
                    jogador = opcoes_jogadores[jogador_selecionado]
                    valor = int(jogador["valor"])

                    st.info(f"💰 Valor a ser pago: R$ {valor:,.0f}")

                    if st.button("💰 Comprar jogador por multa"):
                        supabase.table("elenco").delete().eq("id_time", id_alvo).eq("nome", jogador["nome"]).execute()
                        supabase.table("elenco").insert({**jogador, "id_time": id_time}).execute()

                        registrar_movimentacao(id_time, jogador["nome"], "saida", valor)
                        registrar_movimentacao(id_alvo, jogador["nome"], "entrada", valor)
                        registrar_bid(id_alvo, id_time, jogador, "multa", valor)

                        saldo = supabase.table("times").select("id", "saldo").in_("id", [id_time, id_alvo]).execute().data
                        saldo_dict = {s["id"]: s["saldo"] for s in saldo}
                        supabase.table("times").update({"saldo": saldo_dict[id_time] - valor}).eq("id", id_time).execute()
                        supabase.table("times").update({"saldo": saldo_dict[id_alvo] + valor}).eq("id", id_alvo).execute()

                        multa_compras.setdefault(id_time, []).append({
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "valor": valor,
                            "de": id_alvo
                        })
                        ja_perderam[id_alvo] = ja_perderam.get(id_alvo, 0) + 1

                        supabase.table("configuracoes").update({
                            "multa_compras": multa_compras,
                            "ja_perderam": ja_perderam
                        }).eq("id", ID_CONFIG).execute()

                        st.success("✅ Jogador adquirido por multa!")
                        st.experimental_rerun()

            if st.button("➡️ Finalizar minha vez"):
                concluidos.append(id_time)
                supabase.table("configuracoes").update({"concluidos": concluidos, "vez": str(vez + 1)}).eq("id", ID_CONFIG).execute()
                st.success("✅ Vez encerrada.")
                st.experimental_rerun()
    else:
        nome_proximo = supabase.table("times").select("nome").eq("id", id_atual).execute().data[0]["nome"]
        st.info(f"⏳ Aguardando: {nome_proximo}")
        if eh_admin and st.button("⏭️ Pular vez"):
            supabase.table("configuracoes").update({"vez": str(vez + 1), "concluidos": concluidos + [id_atual]}).eq("id", ID_CONFIG).execute()
            st.success("⏭️ Pulado.")
            st.experimental_rerun()

# ✅ Finaliza evento
if ativo and vez >= len(ordem):
    st.success("✅ Evento Finalizado!")
    supabase.table("configuracoes").update({"ativo": False, "finalizado": True}).eq("id", ID_CONFIG).execute()
    st.experimental_rerun()

# 📋 Ordem
st.subheader("📋 Ordem dos Times")
if ordem:
    times_ordenados = supabase.table("times").select("id", "nome").in_("id", ordem).execute().data
    mapa = {t["id"]: t["nome"] for t in times_ordenados}
    for i, idt in enumerate(ordem):
        indicador = "🔛" if i == vez else "⏳" if i > vez else "✅"
        st.markdown(f"{indicador} {i+1}º - **{mapa.get(idt, 'Desconhecido')}**")
