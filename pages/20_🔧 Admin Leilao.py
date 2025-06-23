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
    origem = st.text_input("Origem do Jogador (ex: Real Madrid)")
    nacionalidade = st.text_input("Nacionalidade (ex: Brasil)")
    imagem_url = st.text_input("URL da Imagem do Jogador (opcional)")
    tempo_duracao = st.number_input("⏱️ Duração do Leilão (em minutos)", min_value=1, value=2)
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
            "imagem_url": imagem_url,
            "enviado_bid": False,
            "validado": False,
            "aguardando_validacao": False,
            "duracao_minutos": tempo_duracao
        }
        supabase.table("leiloes").insert(novo).execute()
        st.success("✅ Jogador adicionado à fila.")

# 🔄 Ativar até 3 leilões
ativos = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).execute().data

if ativos:
    st.subheader("🔴 Leilões Ativos")
    for ativo in ativos:
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
            supabase.table("leiloes").update({"ativo": False, "aguardando_validacao": True}).eq("id", ativo["id"]).execute()
            st.info(f"⏱️ Leilão de {ativo['nome_jogador']} marcado como aguardando validação.")
            st.experimental_rerun()
        else:
            st.info(f"⏳ Tempo restante: {int(restante.total_seconds())} segundos")
else:
    inativos = supabase.table("leiloes") \
        .select("*") \
        .eq("ativo", False) \
        .eq("finalizado", False) \
        .eq("aguardando_validacao", False) \
        .order("valor_atual") \
        .limit(3) \
        .execute().data

    if inativos:
        for leilao in inativos:
            agora = datetime.utcnow()
            minutos = leilao.get("duracao_minutos", 2)
            fim = agora + timedelta(minutes=minutos)
            supabase.table("leiloes").update({
                "ativo": True,
                "inicio": agora.isoformat(),
                "fim": fim.isoformat()
            }).eq("id", leilao["id"]).execute()
        st.success("✅ Novos leilões iniciados automaticamente.")
        st.experimental_rerun()
    else:
        st.info("✅ Nenhum leilão ativo. Fila vazia.")

# 📄 Validação dos leilões
pendentes = supabase.table("leiloes") \
    .select("*") \
    .eq("aguardando_validacao", True) \
    .eq("validado", False) \
    .order("fim", desc=True) \
    .limit(5) \
    .execute()

if pendentes.data:
    st.subheader("📄 Leilões Aguardando Validação do Administrador")
    for item in pendentes.data:
        nome = item.get("nome_jogador", "Desconhecido")
        posicao = item.get("posicao_jogador", "ND")
        valor = item.get("valor_atual", 0)
        id_time = item.get("id_time_atual")
        origem = item.get("origem", "")
        nacionalidade = item.get("nacionalidade", "")

        st.markdown(f"**{nome}** ({posicao}) - R$ {valor:,.0f}".replace(",", "."))

        if st.button(f"✅ Validar Leilão de {nome}", key=f"val_{item['id']}"):
            try:
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": nome,
                    "posicao": posicao,
                    "overall": item["overall_jogador"],
                    "valor": valor,
                    "origem": origem,
                    "nacionalidade": nacionalidade,
                    "imagem_url": item.get("imagem_url", "")
                }).execute()

                registrar_movimentacao(
                    id_time=id_time,
                    tipo="saida",
                    valor=valor,
                    descricao=f"Compra do jogador {nome} via leilão",
                    jogador=nome,
                    categoria="leilao",
                    origem=origem,
                    destino=""
                )

                supabase.table("leiloes").update({
                    "validado": True,
                    "finalizado": True,
                    "enviado_bid": True,
                    "aguardando_validacao": False
                }).eq("id", item["id"]).execute()

                st.success(f"✅ {nome} validado, saldo descontado e registrado no BID.")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Erro ao validar o leilão: {e}")

# 🧹 Limpar histórico
st.subheader("🪨 Limpar Histórico de Leilões Enviados ao BID")
if st.button("🧼 Apagar Histórico de Leilões Enviados"):
    try:
        supabase.table("leiloes") \
            .delete() \
            .eq("finalizado", True) \
            .eq("enviado_bid", True) \
            .execute()
        st.success("🧹 Histórico apagado com sucesso!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao apagar histórico: {e}")


