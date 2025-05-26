# -*- coding: utf-8 -*- 
import streamlit as st 
from supabase import create_client 
from datetime import datetime, timedelta 
from dateutil.parser import parse 
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]

# Verifica nome do time
if "nome_time" in st.session_state:
    nome_time_usuario = st.session_state["nome_time"]
else:
    st.warning("O nome do time não foi encontrado. Faça login novamente.")
    st.stop()

# 🔍 Buscar time na tabela 'times' com o nome fornecido
res = supabase.table("times").select("*").eq("nome", nome_time_usuario).execute()
if not res.data:
    st.warning(f"Nenhum time encontrado com o nome '{nome_time_usuario}'.")
    st.stop()
id_time_usuario = res.data[0]["id"]

# 🔍 Buscar leilão ativo
leilao_res = supabase.table("configuracoes").select("*").eq("id", "leilao_sistema").execute()
leilao = leilao_res.data[0] if leilao_res.data else None

if not leilao or not leilao.get("ativo", False):
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

jogador = leilao.get("jogador", {})
valor_atual = leilao.get("valor_atual", 0)
id_time_vencedor = leilao.get("time_vencedor", "")
fim = leilao.get("fim")

# ⏱️ Cronômetro regressivo
try:
    fim_dt = parse(fim) if isinstance(fim, str) else fim
    tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
    minutos, segundos = divmod(tempo_restante, 60)
    st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro ao calcular cronômetro: {e}")
    st.stop()

st.markdown("---")

# 🏷️ Último lance
nome_time_vencedor = ""
if id_time_vencedor:
    try:
        ref = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute()
        nome_time_vencedor = ref.data[0]["nome"]
    except:
        nome_time_vencedor = "Desconhecido"

# 👤 Exibir jogador
col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
with col1:
    st.subheader(jogador.get("posicao", ""))
with col2:
    st.subheader(jogador.get("nome", ""))
with col3:
    st.metric("⭐ Overall", jogador.get("overall", ""))
with col4:
    st.metric("💰 Lance Atual", f"R$ {valor_atual:,.0f}".replace(",", "."))

if nome_time_vencedor:
    st.info(f"🏷️ Último Lance: {nome_time_vencedor}")

st.markdown("---")

# ⏱️ FINALIZAÇÃO AUTOMÁTICA
if tempo_restante == 0:
    try:
        if id_time_vencedor:
            # Verifica se jogador já está no elenco
            elenco_ref = supabase.table("elenco").select("id").eq("id_time", id_time_vencedor).eq("nome", jogador["nome"]).execute()
            if not elenco_ref.data:
                jogador.pop("id", None)
                jogador.pop("id_time", None)
                jogador["valor"] = valor_atual
                jogador["id_time"] = id_time_vencedor

                supabase.table("elenco").insert(jogador).execute()

                # Atualiza saldo
                saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
                saldo = saldo_ref.data[0]["saldo"]
                novo_saldo = saldo - valor_atual
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

                # Registrar movimentação
                registrar_movimentacao(
                    supabase=supabase,
                    id_time=id_time_vencedor,
                    jogador=jogador["nome"],
                    categoria="Leilão",
                    tipo="Compra",
                    valor=valor_atual
                )

                st.success(f"✅ O time {nome_time_vencedor} levou {jogador['nome']} por R$ {valor_atual:,.0f}.")
        # Encerrar leilão
        supabase.table("configuracoes").update({"ativo": False}).eq("id", "leilao_sistema").execute()
        st.stop()
    except Exception as e:
        st.error(f"Erro ao finalizar o leilão: {e}")
        st.stop()

# 🛎️ SISTEMA DE LANCES
if tempo_restante > 0:
    st.markdown("### 💥 Dar um Lance")
    st.markdown(f"💰 **Lance Atual:** R$ {valor_atual:,.0f}".replace(",", "."))

    botoes = {
        "➕ R$ 500 mil": 500_000,
        "➕ R$ 1 milhão": 1_000_000,
        "➕ R$ 2 milhões": 2_000_000,
        "➕ R$ 5 milhões": 5_000_000,
        "➕ R$ 10 milhões": 10_000_000
    }

    for rotulo, incremento in botoes.items():
        if st.button(rotulo):
            novo_lance = valor_atual + incremento
            saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
            saldo = saldo_ref.data[0].get("saldo")

            if saldo is None or not isinstance(saldo, (int, float)):
                st.error("❌ Erro ao recuperar o saldo do time.")
            elif novo_lance > saldo:
                st.error("❌ Saldo insuficiente.")
            elif novo_lance <= valor_atual:
                st.warning("⚠️ Seu lance não é o maior.")
                st.experimental_rerun()
            else:
                try:
                    agora = datetime.utcnow()
                    novo_fim = fim_dt
                    if (fim_dt - agora).total_seconds() <= 15:
                        novo_fim = agora + timedelta(seconds=15)

                    supabase.table("configuracoes").update({
                        "valor_atual": novo_lance,
                        "time_vencedor": id_time_usuario,
                        "fim": novo_fim.isoformat()
                    }).eq("id", "leilao_sistema").execute()

                    st.success(f"✅ Lance de R$ {novo_lance:,.0f} enviado com sucesso!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar lance: {e}")
else:
    st.info("⏱️ O tempo do leilão acabou.")

# 🔄 Botão manual
if st.button("🔄 Atualizar"):
    st.experimental_rerun()
