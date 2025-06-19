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
meu_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]

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
if apostar_jogador and elenco_adv:
    nomes = [f"{j['nome']} ({j['posicao']})" for j in elenco_adv]
    selecionado = st.selectbox("👤 Escolha o jogador do adversário que deseja apostar", nomes)
    jogador_escolhido = elenco_adv[nomes.index(selecionado)]

if st.button("📩 Enviar Convite"):
    convite = {
        "id": str(uuid.uuid4()),
        "time_convidante": id_time,
        "time_convidado": id_adversario,
        "valor_aposta": float(valor_aposta),
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

for convite in convites_recebidos:
    nome_convidante = mapa_times.get(convite["time_convidante"], {}).get("nome", "Desconhecido")
    id_convidante = convite["time_convidante"]
    valor = convite["valor_aposta"]
    aposta_com_jogador = convite.get("aposta_com_jogador", False)
    jogador_convidante = convite.get("jogador_convidante")

    st.markdown(f"---\n### ⚔️ {nome_convidante} te desafiou para um amistoso!")
    st.markdown(f"💰 Valor apostado: R$ {valor:.2f} milhões")

    jogador_convidado = None
    if aposta_com_jogador:
        st.markdown(f"🎯 {nome_convidante} quer o jogador: **{jogador_convidante}**")
        elenco_convidante = supabase.table("elenco").select("*").eq("id_time", id_convidante).execute().data or []
        nomes_jogadores = [f"{j['nome']} ({j['posicao']})" for j in elenco_convidante]
        selecao = st.selectbox("👤 Escolha 1 jogador do adversário para apostar", nomes_jogadores, key=f"jadv_{convite['id']}")
        jogador_convidado = elenco_convidante[nomes_jogadores.index(selecao)]["nome"]

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Aceitar apenas valor", key=f"aceitar_valor_{convite['id']}"):
            saldo_convidante = mapa_times.get(id_convidante, {}).get("saldo", 0)
            saldo_respondente = meu_saldo
            if saldo_convidante >= valor and saldo_respondente >= valor:
                supabase.table("times").update({"saldo": int(saldo_convidante - valor)}).eq("id", id_convidante).execute()
                supabase.table("times").update({"saldo": int(saldo_respondente - valor)}).eq("id", id_time).execute()
                registrar_movimentacao_simples(id_convidante, -valor, "Aposta amistoso")
                registrar_movimentacao_simples(id_time, -valor, "Aposta amistoso")
                supabase.table("amistosos").update({
                    "status": "aceito",
                    "jogador_convidado": None
                }).eq("id", convite["id"]).execute()
                st.success("Amistoso aceito com valor apenas.")
                st.experimental_rerun()
            else:
                st.error("Saldo insuficiente.")

    with col2:
        if aposta_com_jogador and st.button("📨 Enviar contra proposta com jogador", key=f"contra_{convite['id']}"):
            supabase.table("amistosos").update({
                "status": "aguardando_confirmacao",
                "jogador_convidado": jogador_convidado
            }).eq("id", convite["id"]).execute()
            st.success("Contra proposta enviada. Aguardando confirmação do adversário.")
            st.experimental_rerun()

    with col3:
        if st.button("❌ Recusar convite", key=f"recusar_{convite['id']}"):
            supabase.table("amistosos").update({"status": "recusado"}).eq("id", convite["id"]).execute()
            st.info("Convite recusado.")
            st.experimental_rerun()
# 🕒 Amistosos aguardando confirmação final
st.subheader("🔁 Amistosos aguardando confirmação final")

res_confirmacoes = supabase.table("amistosos").select("*").eq("time_convidante", id_time).eq("status", "aguardando_confirmacao").execute()
confirmacoes = res_confirmacoes.data or []

for convite in confirmacoes:
    nome_convidado = mapa_times.get(convite["time_convidado"], {}).get("nome", "Desconhecido")
    jogador_convidante = convite.get("jogador_convidante", "Desconhecido")
    jogador_convidado = convite.get("jogador_convidado", "Desconhecido")
    valor = convite["valor_aposta"]

    st.markdown(f"---\n### ⚔️ {nome_convidado} aceitou com aposta de jogador!")
    st.markdown(f"💰 Valor apostado: R$ {valor:.2f} milhões")
    st.markdown(f"🎯 Seu jogador apostado: **{jogador_convidante}**")
    st.markdown(f"🎯 Jogador do adversário: **{jogador_convidado}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar amistoso com jogadores", key=f"confirmar_{convite['id']}"):
            saldo_a = meu_saldo
            saldo_b = mapa_times.get(convite["time_convidado"], {}).get("saldo", 0)

            if saldo_a >= valor and saldo_b >= valor:
                # Descontar saldo de ambos
                supabase.table("times").update({"saldo": int(saldo_a - valor)}).eq("id", id_time).execute()
                supabase.table("times").update({"saldo": int(saldo_b - valor)}).eq("id", convite["time_convidado"]).execute()
                registrar_movimentacao_simples(id_time, -valor, "Aposta amistoso com jogador")
                registrar_movimentacao_simples(convite["time_convidado"], -valor, "Aposta amistoso com jogador")

                # Atualizar para aceito
                supabase.table("amistosos").update({"status": "aceito"}).eq("id", convite["id"]).execute()
                st.success("Amistoso confirmado com aposta de jogadores. Agora aguarde a definição do vencedor.")
                st.experimental_rerun()
            else:
                st.error("Saldo insuficiente de algum dos times.")

    with col2:
        if st.button("❌ Cancelar amistoso", key=f"cancelar_{convite['id']}"):
            supabase.table("amistosos").update({"status": "recusado"}).eq("id", convite["id"]).execute()
            st.info("Amistoso cancelado.")
            st.experimental_rerun()
# 🏁 Finalizar Amistosos Aceitos
st.subheader("🏁 Finalizar Amistosos Aceitos")

res_aceitos = supabase.table("amistosos").select("*").eq("status", "aceito").or_(
    f"time_convidante.eq.{id_time},time_convidado.eq.{id_time}"
).execute()

amistosos_aceitos = res_aceitos.data or []

for amistoso in amistosos_aceitos:
    id_convidante = amistoso["time_convidante"]
    id_convidado = amistoso["time_convidado"]

    # Nome dos times
    nome_convidante = nome_time if id_convidante == id_time else mapa_times.get(id_convidante, {}).get("nome", "Desconhecido")
    nome_convidado = nome_time if id_convidado == id_time else mapa_times.get(id_convidado, {}).get("nome", "Desconhecido")

    st.markdown(f"---\n### 🏁 {nome_convidante} x {nome_convidado}")
    vencedor = st.selectbox("👑 Quem venceu?", [nome_convidante, nome_convidado], key=f"v_{amistoso['id']}")

    if st.button("✔️ Finalizar amistoso", key=f"fim_{amistoso['id']}"):
        try:
            valor = float(amistoso["valor_aposta"])
            jogador_convidante = amistoso.get("jogador_convidante")
            jogador_convidado = amistoso.get("jogador_convidado")

            # Determinar vencedor e perdedor
            id_vencedor = id_convidante if vencedor == nome_convidante else id_convidado
            id_perdedor = id_convidado if id_vencedor == id_convidante else id_convidante

            # Atualizar saldo do vencedor
            res_saldo = supabase.table("times").select("saldo").eq("id", id_vencedor).execute()
            saldo_atual = float(res_saldo.data[0]["saldo"])
            novo_saldo = saldo_atual + (valor * 2)
            supabase.table("times").update({"saldo": int(novo_saldo)}).eq("id", id_vencedor).execute()
            registrar_movimentacao_simples(id_vencedor, valor * 2, "Vitória em amistoso")

            # Transferência do jogador, se houver
            if jogador_convidante and jogador_convidado:
                jogador_perdedor = jogador_convidado if id_vencedor == id_convidante else jogador_convidante

                # Transferir o jogador do time perdedor para o vencedor
                supabase.table("elenco").update({"id_time": id_vencedor})\
                    .eq("nome", jogador_perdedor).eq("id_time", id_perdedor).execute()

            # Marcar amistoso como concluído
            supabase.table("amistosos").update({"status": "concluido"}).eq("id", amistoso["id"]).execute()

            st.success(f"Amistoso finalizado! {vencedor} venceu e recebeu o valor total.{' Jogador transferido.' if jogador_convidante and jogador_convidado else ''}")
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao finalizar amistoso: {e}")





