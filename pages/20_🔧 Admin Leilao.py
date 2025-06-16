# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🧑‍⚖️ Administração de Leilões", layout="wide")
st.title("🧑‍⚖️ Administração de Leilões")

# ✅ Verifica login e admin
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

usuario = st.session_state["usuario"]
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("Apenas administradores podem acessar esta página.")
    st.stop()

# ⏱️ Atualiza automaticamente o status de leilões expirados
agora = datetime.now()
leiloes_ativos = supabase.table("leiloes").select("*").eq("status", "ativo").execute().data

for leilao in leiloes_ativos:
    fim_str = leilao.get("fim")
    if fim_str:
        fim = datetime.strptime(fim_str, "%Y-%m-%d %H:%M:%S")
        if agora > fim:
            supabase.table("leiloes").update({"status": "finalizado"}).eq("id", leilao["id"]).execute()

# 🔁 Ativa automaticamente novos leilões da fila se houver menos de 3 ativos
leiloes_ativos = supabase.table("leiloes").select("*").eq("status", "ativo").execute().data
if len(leiloes_ativos) < 3:
    qtd_necessaria = 3 - len(leiloes_ativos)
    leiloes_fila = supabase.table("leiloes").select("*").eq("status", "fila").order("id").execute().data
    for leilao in leiloes_fila[:qtd_necessaria]:
        novo_fim = (agora + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("leiloes").update({
            "status": "ativo",
            "inicio": agora.strftime("%Y-%m-%d %H:%M:%S"),
            "fim": novo_fim
        }).eq("id", leilao["id"]).execute()
    st.experimental_rerun()

# 📤 Formulário para criar novo leilão
with st.expander("📤 Criar novo leilão"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do jogador")
        posicao = st.selectbox("Posição", [
            "GL", "LD", "ZAG", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"
        ])
    with col2:
        overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
        valor = st.number_input("Valor inicial (R$)", min_value=1, step=100000, format="%d")

    if st.button("🚀 Enviar para fila de leilão"):
        try:
            supabase.table("leiloes").insert({
                "nome": nome,
                "posicao": posicao,
                "overall": int(overall),
                "valor_inicial": int(valor),
                "valor_atual": int(valor),
                "status": "fila"
            }).execute()
            st.success("✅ Jogador enviado para a fila de leilão!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao criar leilão: {e}")

# 📋 Lista de leilões
st.markdown("## 📋 Todos os Leilões")

todos_leiloes = supabase.table("leiloes").select("*").order("id", desc=True).execute().data

for leilao in todos_leiloes:
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        col1.markdown(f"**{leilao['nome']}**")
        col2.markdown(f"Posição: {leilao['posicao']}")
        col3.markdown(f"Overall: {leilao['overall']}")
        col4.markdown(f"💰 Valor Atual: R$ {leilao['valor_atual']:,}".replace(",", "."))

        col5, col6, col7 = st.columns([2, 2, 1])

        # ⏱️ Tempo se ativo
        if leilao["status"] == "ativo":
            tempo_restante = datetime.strptime(leilao["fim"], "%Y-%m-%d %H:%M:%S") - agora
            col5.info(f"⏱️ Tempo restante: {tempo_restante}")
        else:
            col5.markdown(f"📌 Status: `{leilao['status']}`")

        # ❌ Botão excluir
        if col6.button(f"🗑️ Excluir", key=f"excluir_{leilao['id']}"):
            supabase.table("leiloes").delete().eq("id", leilao["id"]).execute()
            st.experimental_rerun()

        # ✅ Finalizar manual
        if leilao["status"] == "ativo":
            if col7.button("⛔ Finalizar", key=f"fim_{leilao['id']}"):
                supabase.table("leiloes").update({"status": "finalizado"}).eq("id", leilao["id"]).execute()
                st.experimental_rerun()
