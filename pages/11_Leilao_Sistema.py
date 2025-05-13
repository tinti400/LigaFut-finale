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
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]

# Verifique se a chave 'nome_time' existe no session_state
if "nome_time" in st.session_state:
    nome_time_usuario = st.session_state["nome_time"]
else:
    st.warning("O nome do time não foi encontrado. Por favor, faça o login novamente.")
    st.stop()

# 🔍 Buscar leilão ativo
res = supabase.table("configuracoes").select("*").eq("id", "leilao_sistema").execute()
leilao = res.data[0] if res.data else None

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
    tempo_restante = (fim_dt - datetime.utcnow()).total_seconds()
    tempo_restante = max(0, int(tempo_restante))
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

# 🛑 Finaliza o leilão automaticamente
if tempo_restante == 0:
    try:
        if id_time_vencedor:
            # Verifica se o jogador já foi adicionado ao elenco do time vencedor
            elenco_ref = supabase.table("elenco").select("id_time").eq("id_time", id_time_vencedor).eq("nome", jogador["nome"]).execute()

            if len(elenco_ref.data) == 0:  # Se o jogador não estiver no elenco, adiciona
                jogador.pop("id", None)
                jogador.pop("id_time", None)
                jogador["valor"] = valor_atual
                jogador["id_time"] = id_time_vencedor

                # Adiciona jogador ao elenco
                supabase.table("elenco").insert(jogador).execute()

                # Atualiza saldo do time vencedor
                saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
                saldo_atual = saldo_ref.data[0].get("saldo", 0)

                if isinstance(saldo_atual, (int, float)) and saldo_atual >= valor_atual:
                    novo_saldo = saldo_atual - valor_atual
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

                    # Exibe mensagem confirmando que o time levou o jogador
                    st.success(f"✅ O time {nome_time_vencedor} levou o jogador {jogador['nome']} por R$ {valor_atual:,.0f}.")
                else:
                    st.warning("❌ Erro: saldo insuficiente no time vencedor.")
            else:
                st.info("⏱️ Jogador já foi transferido para o time vencedor.")

        # Encerrar o leilão
        supabase.table("configuracoes").update({"ativo": False}).eq("id", "leilao_sistema").execute()
        st.stop()

    except Exception as e:
        st.error(f"Erro ao finalizar o leilão: {e}")
        st.stop()

# 🛎️ Sistema de lances
if tempo_restante > 0:
    novo_lance = valor_atual + 5000000  # Aumento fixo de 5 milhões

    st.metric("💸 Lance Mínimo", f"R$ {novo_lance:,.0f}".replace(",", "."))

    if st.button(f"💥 Fazer Lance de R$ {novo_lance:,.0f}"):
        try:
            saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
            saldo = saldo_ref.data[0].get("saldo")

            if saldo is None or not isinstance(saldo, (int, float)):
                st.error("❌ Erro ao recuperar o saldo do time.")
            elif novo_lance > saldo:
                st.error("❌ Saldo insuficiente.")
            else:
                agora = datetime.utcnow()
                novo_fim = fim_dt
                if (fim_dt - agora).total_seconds() <= 15:
                    novo_fim = agora + timedelta(seconds=15)

                supabase.table("configuracoes").update({
                    "valor_atual": novo_lance,
                    "time_vencedor": id_time_usuario,
                    "fim": novo_fim.isoformat()
                }).eq("id", "leilao_sistema").execute()

                st.success(f"✅ Lance de R$ {novo_lance:,.0f} enviado!")
                st.experimental_rerun()  # Força a atualização da página
        except Exception as e:
            st.error(f"Erro ao registrar lance: {e}")
else:
    st.info("⏱️ O tempo do leilão acabou.")

# 🛎️ Botão de Atualização
if st.button("🔄 Atualizar"):
    st.experimental_rerun()  # Força a atualização da página
