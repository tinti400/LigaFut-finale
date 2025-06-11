# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(page_title="Admin - Leilões em Fila", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica admin pela tabela 'admins'
usuario_atual = st.session_state.get("usuario", "").lower()
try:
    admin_ref = supabase.table("admins").select("email").execute()
    emails_admin = [item["email"].lower() for item in admin_ref.data]
except Exception as e:
    emails_admin = []
    st.error("Erro ao verificar administradores.")

if usuario_atual not in emails_admin:
    st.warning("🔒 Acesso restrito a administradores.")
    st.stop()

st.title("🧑‍⚖️ Administração de Leilões (Fila)")

# 📝 Adicionar novo leilão manualmente
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
    duracao = st.slider("Duração (min)", 1, 10, value=2)
    origem = st.text_input("Origem do Jogador (ex: Real Madrid)")
    nacionalidade = st.text_input("Nacionalidade (ex: Brasil)")
    imagem_url = st.text_input("URL da Imagem do Jogador (opcional)")
    botao = st.form_submit_button("Adicionar à Fila")

    if botao and nome:
        novo = {
            "nome_jogador": nome,
            "posicao_jogador": posicao,
            "overall_jogador": overall,
            "valor_inicial": valor_inicial,
            "valor_atual": valor_inicial,
            "incremento_minimo": incremento,
            "inicio": None,
            "fim": None,
            "ativo": False,
            "finalizado": False,
            "origem": origem,
            "nacionalidade": nacionalidade,
            "imagem_url": imagem_url
        }
        supabase.table("leiloes").insert(novo).execute()
        st.success("✅ Jogador adicionado à fila.")

# 🔄 Verificar e ativar leilão
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).execute()
ativo = res.data[0] if res.data else None

if ativo:
    st.subheader("🔴 Leilão Ativo")
    st.markdown(f"**Jogador:** {ativo['nome_jogador']}")
    st.markdown(f"**Posição:** {ativo['posicao_jogador']}")
    st.markdown(f"**Valor Atual:** R$ {ativo['valor_atual']:,.0f}".replace(",", "."))
    st.markdown(f"**Origem:** {ativo.get('origem', 'Desconhecida')}")
    st.markdown(f"**Nacionalidade:** {ativo.get('nacionalidade', 'Desconhecida')}")

    if ativo.get("imagem_url"):
        st.image(ativo["imagem_url"], width=200)

    fim = datetime.fromisoformat(ativo["fim"])
    restante = fim - datetime.utcnow()
    if restante.total_seconds() <= 0:
        supabase.table("leiloes").update({"ativo": False, "finalizado": True}).eq("id", ativo["id"]).execute()
        st.info("⏱️ Leilão finalizado automaticamente.")
    else:
        st.info(f"⏳ Tempo restante: {int(restante.total_seconds())} segundos")
else:
    proximo = supabase.table("leiloes").select("*").eq("ativo", False).eq("finalizado", False).order("id").limit(1).execute()
    if proximo.data:
        leilao = proximo.data[0]
        agora = datetime.utcnow()
        fim = agora + timedelta(minutes=2)
        supabase.table("leiloes").update({
            "ativo": True,
            "inicio": agora.isoformat(),
            "fim": fim.isoformat(),
            "imagem_url": leilao.get("imagem_url"),
            "origem": leilao.get("origem"),
            "nacionalidade": leilao.get("nacionalidade")
        }).eq("id", leilao["id"]).execute()
        st.success("✅ Novo leilão iniciado automaticamente.")
        st.experimental_rerun()
    else:
        st.info("✅ Nenhum leilão ativo. Fila vazia.")

