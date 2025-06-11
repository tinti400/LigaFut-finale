# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="🔧 Admin Leilão - LigaFut", layout="wide")
st.title("🔧 Administração de Leilão")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login do admin usando o campo booleano "administrador"
if "usuario_id" not in st.session_state or not st.session_state.get("administrador", False):
    st.warning("Acesso restrito ao administrador.")
    st.stop()

# 📦 Campos para criar novo leilão
st.subheader("📦 Criar novo leilão")
nome_jogador = st.text_input("Nome do jogador")
posicao_jogador = st.selectbox("Posição", [
    "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
    "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
    "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centro Avante (CA)"
])
overall_jogador = st.number_input("Overall", min_value=50, max_value=99, value=70)
valor_inicial = st.number_input("Valor inicial (R$)", min_value=100000, step=50000)
duracao_minutos = st.number_input("Duração do leilão (em minutos)", min_value=1, value=2)
id_time = st.text_input("ID do time vendedor")
nome_time = st.text_input("Nome do time vendedor")

# 🚀 Botão para criar leilão
if st.button("🚀 Criar Leilão"):
    try:
        agora = datetime.now(pytz.timezone("America/Sao_Paulo"))
        fim = agora + timedelta(minutes=duracao_minutos)

        supabase.table("leiloes").insert({
            "nome_jogador": nome_jogador,
            "posicao_jogador": posicao_jogador,
            "overall_jogador": overall_jogador,
            "valor_inicial": valor_inicial,
            "id_time_vendedor": id_time,
            "nome_time_vendedor": nome_time,
            "ativo": False,
            "finalizado": False,
            "fim": fim.isoformat()
        }).execute()

        st.success("✅ Leilão criado com sucesso!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao criar leilão: {e}")

# 📋 Lista de leilões criados
st.subheader("📋 Leilões criados")
res_leiloes = supabase.table("leiloes").select("*").order("fim", desc=True).execute()
leiloes = res_leiloes.data if res_leiloes.data else []

for leilao in leiloes:
    with st.expander(f"{leilao['nome_jogador']} ({leilao['posicao_jogador']}) - R$ {leilao['valor_inicial']:,}".replace(",", ".")):
        st.write("👤 Time vendedor:", leilao.get("nome_time_vendedor"))
        st.write("⏰ Termina em:", leilao.get("fim"))
        st.write("🔁 Status:", "Ativo" if leilao.get("ativo") else "Inativo")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Ativar", key=f"ativar_{leilao['id']}"):
                supabase.table("leiloes").update({"ativo": True}).eq("id", leilao["id"]).execute()
                st.success("Leilão ativado!")
                st.experimental_rerun()
        with col2:
            if st.button("🛑 Desativar", key=f"desativar_{leilao['id']}"):
                supabase.table("leiloes").update({"ativo": False}).eq("id", leilao["id"]).execute()
                st.warning("Leilão desativado.")
                st.experimental_rerun()


