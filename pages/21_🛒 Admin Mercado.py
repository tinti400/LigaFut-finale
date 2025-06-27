# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="🛒 Admin - Mercado", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")

# 👑 Verifica se é admin
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True
if not eh_admin:
    st.warning("🔐 Acesso permitido apenas para administradores.")
    st.stop()

st.title("🛒 Administração do Mercado de Transferências")
st.markdown("---")

# 📦 Cadastro manual de jogador no mercado
with st.expander("➕ Adicionar Jogador Manualmente ao Mercado"):
    nome = st.text_input("Nome do Jogador")
    posicao = st.text_input("Posição do Jogador")
    overall = st.number_input("Overall", min_value=0, max_value=99, value=70)
    valor = st.number_input("Valor de Mercado (R$)", min_value=0, step=100000, value=10000000)
    time_origem = st.text_input("Time de Origem")
    nacionalidade = st.text_input("Nacionalidade")
    imagem_url = st.text_input("URL da Imagem do Jogador")
    link_sofifa = st.text_input("🔗 Link do Jogador no SoFIFA (opcional)")

    if st.button("Adicionar ao Mercado"):
        if not nome or not posicao:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")
        else:
            foto = imagem_url if imagem_url else "https://cdn-icons-png.flaticon.com/512/147/147144.png"
            salario = round(valor * 0.007)
            novo_jogador = {
                "nome": nome,
                "posicao": posicao,
                "overall": overall,
                "valor": valor,
                "time_origem": time_origem,
                "nacionalidade": nacionalidade,
                "foto": foto,
                "link_sofifa": link_sofifa,
                "classificacao": "sem classificacao",
                "origem": "",
                "idade": "",
                "salario": salario,
                "id_time": None
            }
            try:
                supabase.table("mercado_transferencias").insert(novo_jogador).execute()
                st.success(f"✅ Jogador {nome} adicionado com sucesso ao mercado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar jogador: {e}")

st.markdown("---")

# 📊 Visualizar jogadores no mercado
st.subheader("📋 Jogadores no Mercado")
res = supabase.table("mercado_transferencias").select("*").execute()
df = pd.DataFrame(res.data)

# Remove colunas não necessárias na visualização
colunas_ocultas = ["imagem", "imagem_url", "origem", "idade", "id_time"]
df = df.drop(columns=[c for c in colunas_ocultas if c in df.columns], errors="ignore")

# Exibe a tabela limpa
st.dataframe(df, use_container_width=True)

st.markdown("---")
st.info("🔧 Para remover ou editar jogadores, utilize o painel do Supabase diretamente ou solicite uma funcionalidade extra aqui.")
