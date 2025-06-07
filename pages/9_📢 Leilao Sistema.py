# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilão - LigaFut", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔍 Buscar leilão ativo
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).limit(1).execute()
if not res.data:
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

leilao = res.data[0]
fim = leilao.get("fim")
valor_atual = leilao["valor_atual"]
incremento = leilao["incremento_minimo"]
id_time_vencedor = leilao.get("id_time_atual", "")
nome_jogador = leilao["nome_jogador"]
posicao_jogador = leilao["posicao_jogador"]
overall_jogador = leilao["overall_jogador"]

# ⏱️ Cronômetro
fim_dt = datetime.fromisoformat(fim)
tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))
minutos, segundos = divmod(tempo_restante, 60)
st.markdown(f"<h2 style='text-align:center'>⏳ Tempo restante: {minutos:02d}:{segundos:02d}</h2>", unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
with col1: st.subheader(posicao_jogador)
with col2: st.subheader(nome_jogador)
with col3: st.metric("⭐ Overall", overall_jogador)
with col4: st.metric("💰 Lance Atual", f"R$ {valor_atual:,.0f}".replace(",", "."))

# 🏷️ Último lance
if id_time_vencedor:
    nome_time = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute().data[0]["nome"]
    st.info(f"🏷️ Último Lance: {nome_time}")

st.markdown("---")

# ⏹️ Finalização automática
if tempo_restante == 0:
    if id_time_vencedor:
        jogador = {
            "nome": nome_jogador,
            "posicao": posicao_jogador,
            "overall": overall_jogador,
            "valor": valor_atual,
            "id_time": id_time_vencedor
        }

        supabase.table("elenco").insert(jogador).execute()
        saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
        saldo = saldo_ref.data[0]["saldo"]
        novo_saldo = saldo - valor_atual
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

        registrar_movimentacao(
            supabase=supabase,
            id_time=id_time_vencedor,
            jogador=nome_jogador,
            categoria="Leilão",
            tipo="Compra",
            valor=valor_atual
        )

        st.success(f"✅ {nome_jogador} foi arrematado por {nome_time} por R$ {valor_atual:,.0f}!")
    supabase.table("leiloes").update({"ativo": False, "finalizado": True}).eq("id", leilao["id"]).execute()
    st.stop()

# 📢 Dar lances
if tempo_restante > 0:
    st.markdown("### 💥 Dar um Lance")
    botoes = {
        f"➕ R$ {incremento:,.0f}": incremento,
        f"➕ R$ {incremento * 2:,.0f}": incremento * 2,
        f"➕ R$ {incremento * 3:,.0f}": incremento * 3,
    }

    for label, aumento in botoes.items():
        if st.button(label):
            novo_lance = valor_atual + aumento
            saldo_ref = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
            saldo = saldo_ref.data[0]["saldo"]

            if novo_lance > saldo:
                st.error("❌ Saldo insuficiente.")
            else:
                fim_estendido = datetime.utcnow()
                if (fim_dt - fim_estendido).total_seconds() <= 15:
                    fim_dt = fim_estendido + timedelta(seconds=15)

                supabase.table("leiloes").update({
                    "valor_atual": novo_lance,
                    "id_time_atual": id_time_usuario,
                    "time_vencedor": nome_time_usuario,
                    "fim": fim_dt.isoformat()
                }).eq("id", leilao["id"]).execute()

                st.success(f"✅ Lance enviado com sucesso!")
                st.experimental_rerun()

st.markdown("---")
if st.button("🔄 Atualizar"):
    st.experimental_rerun()
