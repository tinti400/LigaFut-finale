# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao
import time

st.set_page_config(page_title="📢 Leilão de Jogadores - LigaFut", layout="wide")
st.title("📢 Leilão de Jogadores")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state["nome_time"]

# 🔄 Consulta leilões ativos
res = supabase.table("leiloes").select("*").eq("ativo", True).execute()
leiloes = res.data or []

if not leiloes:
    st.info("🕑 Nenhum leilão ativo no momento.")
    st.stop()

for leilao in leiloes:
    st.markdown("---")

    nome_jogador = leilao["nome"]
    posicao = leilao.get("posicao", "")
    overall = leilao.get("overall", 0)
    valor_inicial = leilao.get("valor_inicial", 0)
    valor_atual = leilao.get("valor_atual", valor_inicial)
    tempo_fim = leilao.get("fim", "")
    imagem_url = leilao.get("imagem_url", "")
    id_mercado = leilao.get("id_mercado")
    nacionalidade = leilao.get("nacionalidade", "")
    link_sofifa = leilao.get("link_sofifa", "")

    st.subheader(f"🎯 {nome_jogador} ({posicao}) - Overall {overall}")
    if imagem_url:
        st.image(imagem_url, width=150)

    st.markdown(f"🌍 Nacionalidade: **{nacionalidade}**")
    st.markdown(f"💰 Lance atual: **R$ {valor_atual:,.0f}**".replace(",", "."))

    # ⏱️ Cronômetro
    if tempo_fim:
        tempo_final = datetime.fromisoformat(tempo_fim)
        agora = datetime.now()
        tempo_restante = int((tempo_final - agora).total_seconds())
    else:
        tempo_restante = 0

    if tempo_restante > 0:
        minutos = tempo_restante // 60
        segundos = tempo_restante % 60
        st.info(f"⏳ Tempo restante: {minutos:02d}:{segundos:02d}")
    else:
        st.warning("⛔ Leilão encerrado")

    # 🔁 Finalizar leilão automaticamente se tempo acabar
    if tempo_restante <= 0 and not leilao.get("finalizado", False):
        id_time_vencedor = leilao.get("id_time_vencedor")

        if id_time_vencedor:
            try:
                # ➕ Inserir jogador no elenco
                supabase.table("elenco").insert({
                    "id_time": id_time_vencedor,
                    "nome": nome_jogador,
                    "posicao": posicao,
                    "overall": overall,
                    "valor": valor_atual,
                    "imagem_url": imagem_url,
                    "link_sofifa": link_sofifa,
                    "nacionalidade": nacionalidade
                }).execute()

                # 💸 Atualizar saldo
                saldo_res = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
                saldo_atual = saldo_res.data[0]["saldo"]
                novo_saldo = saldo_atual - valor_atual
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

                # 📋 Registrar movimentação
                registrar_movimentacao(
                    id_time=id_time_vencedor,
                    tipo="saida",
                    valor=valor_atual,
                    descricao=f"Compra no leilão: {nome_jogador}",
                    jogador=nome_jogador,
                    categoria="leilao",
                    destino=nome_time_usuario
                )

                # 🔄 Atualizar mercado (se aplicável)
                if id_mercado:
                    supabase.table("mercado_transferencias").update({
                        "status": "atribuido",
                        "destino": nome_time_usuario
                    }).eq("id", id_mercado).execute()

                # 🚫 Finalizar leilão
                supabase.table("leiloes").update({
                    "ativo": False,
                    "finalizado": True
                }).eq("id", leilao["id"]).execute()

                st.success(f"✅ Leilão finalizado! {nome_jogador} agora pertence ao time vencedor.")
                st.rerun()
                return  # 🔒 Evita execução duplicada
            except Exception as e:
                st.error(f"❌ Erro ao finalizar leilão: {e}")
                st.stop()
        else:
            # Sem lances, finaliza leilão
            supabase.table("leiloes").update({
                "ativo": False,
                "finalizado": True
            }).eq("id", leilao["id"]).execute()
            st.warning(f"⚠️ Leilão de {nome_jogador} expirado sem lances.")
            st.rerun()
            return

    # 💸 Botão para dar lance
    if tempo_restante > 0:
        novo_valor = valor_atual + 100_000
        if st.button(f"📢 Dar lance - R$ {novo_valor:,.0f}".replace(",", "."), key=leilao["id"]):
            try:
                supabase.table("leiloes").update({
                    "valor_atual": novo_valor,
                    "id_time_vencedor": id_time_usuario
                }).eq("id", leilao["id"]).execute()
                st.success("✅ Lance registrado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao dar lance: {e}")
