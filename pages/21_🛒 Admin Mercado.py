# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from supabase import create_client
from utils import verificar_sessao

st.set_page_config(page_title="🛒 Admin Mercado", layout="wide")
verificar_sessao()

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🛒 Administração do Mercado de Transferências")

st.markdown("### 📤 Adicionar Jogadores Manualmente")
with st.form("form_adicionar"):
    col1, col2, col3 = st.columns(3)
    with col1:
        nome = st.text_input("Nome do jogador")
        overall = st.number_input("Overall", min_value=0, max_value=99, step=1)
        posicao = st.text_input("Posição")
    with col2:
        valor = st.number_input("Valor R$", min_value=1, step=1)
        nacionalidade = st.text_input("Nacionalidade")
        salario = st.number_input("Salário R$ (opcional)", min_value=0, step=1, value=0)
    with col3:
        origem = st.text_input("Time de origem")
        imagem_url = st.text_input("URL da imagem (opcional)")
        link_sofifa = st.text_input("Link do SoFIFA (opcional)")

    submitted = st.form_submit_button("➕ Adicionar jogador")
    if submitted:
        try:
            if not nome or not posicao or not valor:
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                supabase.table("mercado_transferencias").insert({
                    "nome": nome,
                    "overall": overall,
                    "posicao": posicao,
                    "valor": valor,
                    "nacionalidade": nacionalidade,
                    "salario": salario if salario > 0 else int(valor * 0.007),
                    "time_origem": origem,
                    "imagem": imagem_url,
                    "link_sofifa": link_sofifa
                }).execute()
                st.success(f"✅ Jogador {nome} adicionado com sucesso!")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao adicionar jogador: {e}")

st.markdown("---")

st.markdown("### 📥 Importar Jogadores via Planilha Excel")
arquivo = st.file_uploader("Envie o arquivo .xlsx com os jogadores", type=["xlsx"])

if arquivo:
    try:
        df_excel = pd.read_excel(arquivo)
        st.dataframe(df_excel)

        if st.button("📤 Enviar jogadores para o mercado"):
            inseridos = 0
            for _, row in df_excel.iterrows():
                try:
                    supabase.table("mercado_transferencias").insert({
                        "nome": row.get("nome", "").strip(),
                        "overall": int(row.get("overall", 0)),
                        "posicao": row.get("posicao", "").strip(),
                        "valor": int(row.get("valor", 0)),
                        "nacionalidade": row.get("nacionalidade", "").strip(),
                        "salario": int(row.get("salario", int(row.get("valor", 0) * 0.007))),
                        "time_origem": row.get("time_origem", "").strip(),
                        "imagem": row.get("imagem", "").strip(),
                        "link_sofifa": row.get("link_sofifa", "").strip()
                    }).execute()
                    inseridos += 1
                except Exception as err:
                    st.warning(f"⚠️ Erro ao adicionar {row.get('nome', '')}: {err}")
            st.success(f"✅ {inseridos} jogadores importados com sucesso!")
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

st.markdown("---")

st.markdown("### 📋 Jogadores no Mercado")

try:
    res = supabase.table("mercado_transferencias").select("*").execute()
    jogadores = res.data if res.data else []

    if jogadores:
        st.markdown("#### 👥 Lista de Jogadores")
        for jogador in jogadores:
            with st.container():
                cols = st.columns([1, 2, 2, 2, 2])
                try:
                    url_img = jogador.get("imagem", "")
                    if not url_img:
                        raise Exception("Sem imagem")
                    response = requests.get(url_img, timeout=3)
                    img = Image.open(BytesIO(response.content))
                except:
                    img = Image.open("default_avatar.png")  # imagem padrão no projeto
                cols[0].image(img, width=60)
                cols[1].markdown(f"**{jogador['nome']}**")
                cols[2].markdown(f"🔢 Overall: {jogador['overall']}")
                cols[3].markdown(f"📍 Posição: {jogador['posicao']}")
                cols[4].markdown(f"💰 Valor: R$ {jogador['valor']:,}".replace(",", "."))

    else:
        st.info("Nenhum jogador no mercado.")
except Exception as e:
    st.error(f"Erro ao carregar jogadores: {e}")
