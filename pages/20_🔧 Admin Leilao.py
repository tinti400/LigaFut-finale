# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="🧑‍⚖️ Administração de Leilões (Fila)", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica admin
usuario_atual = st.session_state.get("usuario", "").lower()
try:
    admin_ref = supabase.table("admins").select("email").execute()
    emails_admin = [item["email"].lower() for item in admin_ref.data]
except Exception as e:
    emails_admin = []
    st.error("Erro ao verificar administradores.")

if usuario_atual not in emails_admin:
    st.warning("🔐 Acesso restrito a administradores.")
    st.stop()

st.title("🧑‍⚖️ Administração de Leilões (Fila)")

# 📋 Adicionar novo leilão manualmente
with st.form("novo_leilao"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99)
    valor_inicial = st.number_input("Valor Inicial (R$)", min_value=100_000, step=50_000)
    incremento = st.number_input("Incremento mínimo (R$)", min_value=100_000, step=50_000, value=3_000_000)
    tempo_minutos = st.number_input("⏱️ Duração do Leilão (min)", min_value=1, max_value=30, value=2)
    origem = st.text_input("Origem do Jogador (ex: Real Madrid)")
    nacionalidade = st.text_input("Nacionalidade (ex: Brasil)")
    imagem_url = st.text_input("URL da Imagem do Jogador (opcional)")
    botao = st.form_submit_button("Adicionar à Fila")

    if botao and nome:
        agora = datetime.utcnow()
        fim = agora + timedelta(minutes=tempo_minutos)
        novo = {
            "nome_jogador": nome,
            "posicao_jogador": posicao,
            "overall_jogador": overall,
            "valor_inicial": valor_inicial,
            "valor_atual": valor_inicial,
            "incremento_minimo": incremento,
            "inicio": agora.isoformat(),
            "fim": fim.isoformat(),
            "ativo": True,
            "finalizado": False,
            "origem": origem,
            "nacionalidade": nacionalidade,
            "imagem_url": imagem_url,
            "enviado_bid": False,
            "validado": False,
            "aguardando_validacao": False
        }
        supabase.table("leiloes").insert(novo).execute()
        st.success("✅ Jogador adicionado à fila e leilão iniciado.")

# 📄 Leilões aguardando validação do administrador
pendentes = supabase.table("leiloes") \
    .select("*") \
    .eq("aguardando_validacao", True) \
    .eq("validado", False) \
    .order("fim", desc=True) \
    .limit(10) \
    .execute()

if pendentes.data:
    st.subheader("📄 Leilões Aguardando Validação do Administrador")
    for item in pendentes.data:
        nome = item.get("nome_jogador") or "Jogador sem nome"
        posicao = item.get("posicao_jogador") or "Posição indefinida"
        valor = item.get("valor_atual", 0)
        id_time = item.get("id_time_atual")

        st.markdown(f"**{nome}** ({posicao}) - R$ {valor:,.0f}".replace(",", "."))

        if st.button(f"✅ Validar Leilão de {nome}", key=f"validar_{item['id']}"):
            try:
                # 1. Inserir jogador no elenco do time vencedor
                jogador = {
                    "nome": nome,
                    "posicao": posicao,
                    "overall": item["overall_jogador"],
                    "valor": valor,
                    "nacionalidade": item.get("nacionalidade", ""),
                    "origem": item.get("origem", ""),
                    "imagem_url": item.get("imagem_url", ""),
                    "id_time": id_time
                }
                supabase.table("elenco").insert(jogador).execute()

                # 2. Descontar valor do saldo
                res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
                if res_saldo.data:
                    saldo_atual = res_saldo.data[0]["saldo"]
                    novo_saldo = saldo_atual - valor
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                # 3. Registrar movimentação financeira (vai para o BID)
                registrar_movimentacao(
                    id_time=id_time,
                    tipo="saida",
                    valor=valor,
                    descricao=f"Compra de {nome} via Leilão (origem: {item.get('origem', '-')})"
                )

                # 4. Atualizar status do leilão
                supabase.table("leiloes").update({
                    "validado": True,
                    "finalizado": True,
                    "enviado_bid": True,
                    "aguardando_validacao": False
                }).eq("id", item["id"]).execute()

                st.success(f"✅ {nome} validado com sucesso e adicionado ao elenco.")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Erro ao validar o leilão: {e}")


