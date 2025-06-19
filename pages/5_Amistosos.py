# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao_simples
import uuid

st.set_page_config(page_title="🤝 Amistosos - LigaFut", layout="wide")
st.title("🤝 Amistosos de Pré-Temporada")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu time")

# 🔄 Buscar todos os times
res_times = supabase.table("times").select("id, nome, saldo").neq("id", id_time).execute()
todos_times = res_times.data or []
mapa_times = {t["id"]: t for t in todos_times}

# 📋 Buscar elenco do time logado
res_elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
meu_elenco = res_elenco.data or []

# 📨 Enviar convite
st.subheader("📨 Enviar Convite de Amistoso")

times_disponiveis = {t["nome"]: t["id"] for t in todos_times}
if not times_disponiveis:
    st.info("Nenhum adversário disponível no momento.")
    st.stop()

adversario_nome = st.selectbox("Escolha o adversário", list(times_disponiveis.keys()))
id_adversario = times_disponiveis[adversario_nome]

# 🔍 Buscar elenco do adversário
elenco_adv = supabase.table("elenco").select("*").eq("id_time", id_adversario).execute().data or []

valor_aposta = st.number_input("💰 Valor da aposta (em milhões)", min_value=1.0, max_value=100.0, step=1.0)

apostar_jogador = st.checkbox("🎲 Deseja incluir um jogador do adversário como aposta?")

jogador_escolhido = None
if apostar_jogador:
    if not elenco_adv:
        st.warning("O adversário não possui jogadores cadastrados.")
        apostar_jogador = False
    else:
        nomes = [f"{j['nome']} ({j['posicao']})" for j in elenco_adv]
        selecionado = st.selectbox("👤 Escolha o jogador do adversário que deseja apostar", nomes)
        jogador_escolhido = elenco_adv[nomes.index(selecionado)]

if st.button("📩 Enviar Convite"):
    convite = {
        "id": str(uuid.uuid4()),
        "time_convidante": id_time,
        "time_convidado": id_adversario,
        "valor_aposta": valor_aposta,
        "status": "pendente",
        "aposta_com_jogador": apostar_jogador,
        "jogador_convidante": jogador_escolhido["nome"] if jogador_escolhido else None,
        "jogador_convidado": None,
        "data_criacao": datetime.now().isoformat()
    }
    supabase.table("amistosos").insert(convite).execute()
    st.success("Convite enviado com sucesso!")
    st.experimental_rerun()

# 📥 Convites recebidos
st.subheader("📥 Convites Recebidos")

res_convites = supabase.table("amistosos").select("*").eq("time_convidado", id_time).eq("status", "pendente").execute()
convites_recebidos = res_convites.data or []

if not convites_recebidos:
    st.info("Você não recebeu nenhum convite.")
else:
    for convite in convites_recebidos:
        time_a_id = convite["time_convidante"]
        nome_a = mapa_times.get(time_a_id, {}).get("nome", "Desconhecido")
        valor = convite["valor_aposta"]
        aposta_jog = convite.get("aposta_com_jogador", False)
        jogador_convidante = convite.get("jogador_convidante", None)

        st.markdown(f"---\n### ⚽ {nome_a} te desafiou para um amistoso!")
        st.markdown(f"💰 Valor apostado: R${valor:.2f} milhões")

        if aposta_jog:
            st.markdown(f"🎲 Jogador que ele quer do seu elenco: **{jogador_convidante}**")

            nomes_meu_elenco = [f"{j['nome']} ({j['posicao']})" for j in meu_elenco]
            jogador_defesa = st.selectbox(
                f"👤 Escolha 1 jogador seu para colocar na aposta contra {nome_a}",
                nomes_meu_elenco,
                key=f"jogador_convidado_{convite['id']}"
            )
            jogador_convidado = meu_elenco[nomes_meu_elenco.index(jogador_defesa)]
        else:
            jogador_convidado = None

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aceitar apenas valor", key=f"aceitar_valor_{convite['id']}"):
                saldo_convidante = mapa_times.get(time_a_id, {}).get("saldo", 0)
                saldo_convidado = mapa_times.get(id_time, {}).get("saldo", 0)

                if saldo_convidante >= valor and saldo_convidado >= valor:
                    supabase.table("times").update({"saldo": saldo_convidante - valor}).eq("id", time_a_id).execute()
                    supabase.table("times").update({"saldo": saldo_convidado - valor}).eq("id", id_time).execute()
                    registrar_movimentacao_simples(time_a_id, -valor, "Aposta amistoso (dinheiro)")
                    registrar_movimentacao_simples(id_time, -valor, "Aposta amistoso (dinheiro)")
                    supabase.table("amistosos").update({
                        "status": "aceito",
                        "jogador_convidado": None
                    }).eq("id", convite["id"]).execute()
                    st.success("Amistoso aceito com aposta apenas em dinheiro!")
                    st.experimental_rerun()
                else:
                    st.error("Um dos clubes não tem saldo suficiente.")

        with col2:
            if aposta_jog and st.button("🎯 Aceitar com aposta de jogador", key=f"aceitar_total_{convite['id']}"):
                saldo_convidante = mapa_times.get(time_a_id, {}).get("saldo", 0)
                saldo_convidado = mapa_times.get(id_time, {}).get("saldo", 0)

                if saldo_convidante >= valor and saldo_convidado >= valor:
                    supabase.table("times").update({"saldo": saldo_convidante - valor}).eq("id", time_a_id).execute()
                    supabase.table("times").update({"saldo": saldo_convidado - valor}).eq("id", id_time).execute()
                    registrar_movimentacao_simples(time_a_id, -valor, "Aposta amistoso (dinheiro + jogador)")
                    registrar_movimentacao_simples(id_time, -valor, "Aposta amistoso (dinheiro + jogador)")
                    supabase.table("amistosos").update({
                        "status": "aceito",
                        "jogador_convidado": jogador_convidado["nome"]
                    }).eq("id", convite["id"]).execute()
                    st.success("Amistoso aceito com aposta total!")
                    st.experimental_rerun()
                else:
                    st.error("Um dos clubes não tem saldo suficiente.")




