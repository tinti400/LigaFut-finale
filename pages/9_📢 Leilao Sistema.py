# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import verificar_sessao, registrar_bid

st.set_page_config(page_title="📢 Leilão do Sistema", layout="wide")
st.title("📢 Leilão do Sistema")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔍 Buscar jogador em leilão ativo
res = supabase.table("leilao_sistema").select("*").eq("ativo", True).execute()
leiloes_ativos = res.data

if not leiloes_ativos:
    st.info("⚠️ Nenhum leilão ativo no momento.")
else:
    leilao = leiloes_ativos[0]
    jogador = leilao["jogador"]
    valor_atual = leilao["valor_atual"]
    imagem = leilao.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(imagem, width=120)
    with col2:
        st.markdown(f"### {jogador}")
        st.write(f"📌 **Posição:** {leilao['posicao']}")
        st.write(f"⭐ **Overall:** {leilao['overall']}")
        st.write(f"💰 **Valor atual:** R$ {valor_atual:,.0f}".replace(",", "."))
        st.write(f"⌛ **Tempo restante:** {leilao['tempo_restante']} segundos")

    novo_valor = valor_atual + 100_000
    if st.button(f"💸 Dar lance de R$ {novo_valor:,.0f}".replace(",", ".")):
        try:
            # Atualiza o leilão com o novo valor e time que deu o lance
            supabase.table("leilao_sistema").update({
                "valor_atual": novo_valor,
                "id_time_lance": id_time,
                "nome_time_lance": nome_time,
                "data_lance": datetime.now().isoformat()
            }).eq("id", leilao["id"]).execute()

            st.success("✅ Lance registrado com sucesso!")

        except Exception as e:
            st.error(f"Erro ao dar lance: {e}")

    # Botão para comprar (usuário responsável pelo último lance)
    if leilao.get("id_time_lance") == id_time:
        if st.button("✅ Finalizar compra e enviar para validação do admin"):
            try:
                jogador_info = {
                    "nome": jogador,
                    "posicao": leilao["posicao"],
                    "overall": leilao["overall"],
                    "valor": valor_atual,
                    "id_time": id_time,
                    "imagem_url": leilao.get("imagem_url"),
                    "nacionalidade": leilao.get("nacionalidade"),
                    "origem": "Leilão Sistema"
                }

                # Salva para validação do admin (tabela pendente_leiloes)
                supabase.table("pendente_leiloes").insert({
                    "id_time": id_time,
                    "nome_time": nome_time,
                    "jogador": jogador_info["nome"],
                    "valor": jogador_info["valor"],
                    "dados_jogador": jogador_info,
                    "status": "pendente",
                    "data": datetime.now().isoformat()
                }).execute()

                # Registro público no BID (marcado como "aguardando validação")
                registrar_bid(
                    id_time=id_time,
                    tipo="compra",
                    categoria="leilao",
                    jogador=jogador,
                    valor=valor_atual,
                    origem="Leilão Sistema",
                    destino=nome_time
                )

                st.success("✅ Compra enviada para validação do administrador.")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao enviar para validação: {e}")
