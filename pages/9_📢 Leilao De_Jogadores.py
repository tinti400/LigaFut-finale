# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import registrar_movimentacao

st.set_page_config(page_title="Leilões Ativos - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time_usuario = st.session_state["id_time"]
nome_time_usuario = st.session_state.get("nome_time", "")

# 🔒 Verifica restrições
restricoes = {}
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time_usuario).execute()
    if res_restricoes.data and isinstance(res_restricoes.data[0].get("restricoes"), dict):
        restricoes = res_restricoes.data[0]["restricoes"]
except Exception:
    restricoes = {}

if restricoes.get("leilao", False):
    st.error("🚫 Seu time está proibido de participar de leilões.")
    st.stop()

# 🔍 Buscar até 3 leilões ativos
res = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).limit(3).execute()
leiloes = res.data

if not leiloes:
    st.warning("⚠️ Nenhum leilão ativo no momento.")
    st.stop()

# 🔁 Loop nos leilões
for leilao in leiloes:
    fim = leilao.get("fim")
    fim_dt = datetime.fromisoformat(fim)
    tempo_restante = max(0, int((fim_dt - datetime.utcnow()).total_seconds()))

    valor_atual = leilao["valor_atual"]
    incremento = leilao["incremento_minimo"]
    overall = leilao.get("overall_jogador", "N/A")
    nacionalidade = leilao.get("nacionalidade", "-")
    imagem_url = leilao.get("imagem_url", "")
    link_sofifa = leilao.get("link_sofifa", "")
    id_time_vencedor = leilao.get("id_time_atual", "")
    nome_jogador = leilao.get("nome_jogador")
    posicao = leilao.get("posicao_jogador")

    # ⛔ Se o tempo acabou e ainda não foi finalizado
    if tempo_restante == 0 and not leilao.get("finalizado", False):
        if id_time_vencedor:
            # ✅ Transferir o jogador
            try:
                supabase.table("elenco").insert({
                    "id_time": id_time_vencedor,
                    "nome": nome_jogador,
                    "posicao": posicao,
                    "overall": overall,
                    "valor": valor_atual,
                    "imagem_url": imagem_url
                }).execute()

                # 💰 Atualizar saldo do time
                saldo_res = supabase.table("times").select("saldo").eq("id", id_time_vencedor).execute()
                saldo_atual = saldo_res.data[0]["saldo"]
                novo_saldo = saldo_atual - valor_atual
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time_vencedor).execute()

                # 🧾 Registrar movimentação
                registrar_movimentacao(id_time_vencedor, -valor_atual, f"Compra no leilão: {nome_jogador}")

                # ✅ Atualizar status do jogador base
                supabase.table("jogadores_base").update({
                    "destino": nome_time_usuario
                }).eq("nome", nome_jogador).execute()

                # 🛑 Finalizar leilão
                supabase.table("leiloes").update({
                    "ativo": False,
                    "finalizado": True
                }).eq("id", leilao["id"]).execute()

                st.success(f"✅ Leilão de {nome_jogador} finalizado. Jogador transferido para {nome_time_usuario}.")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"❌ Erro ao finalizar leilão: {e}")
                st.stop()
        else:
            # Leilão sem lances
            supabase.table("leiloes").update({
                "ativo": False,
                "finalizado": True
            }).eq("id", leilao["id"]).execute()
            st.warning(f"⛔ Leilão de {nome_jogador} expirado sem lances.")
            st.experimental_rerun()

    # ⏳ Exibição enquanto o tempo ainda está rodando
    minutos, segundos = divmod(tempo_restante, 60)

    st.markdown("---")
    st.subheader(f"🧤 {nome_jogador} ({posicao})")

    col1, col2 = st.columns([1, 3])
    with col1:
        if imagem_url:
            st.image(imagem_url, width=180)

    with col2:
        st.markdown(f"""
        **Overall:** {overall}  
        **Nacionalidade:** {nacionalidade}  
        **💰 Preço Atual:** R$ {valor_atual:,.0f}  
        **⏳ Tempo Restante:** {minutos:02d}:{segundos:02d}
        """)
        if link_sofifa:
            st.markdown(f"[📄 Ficha Técnica (SoFIFA)]({link_sofifa})", unsafe_allow_html=True)

        if id_time_vencedor:
            time_res = supabase.table("times").select("nome").eq("id", id_time_vencedor).execute()
            if time_res.data:
                st.info(f"🏷️ Último Lance: {time_res.data[0]['nome']}")

    # 💸 Lances
    st.markdown("#### 💥 Dar um Lance")
    botoes = [incremento * i for i in range(1, 11)]
    colunas = st.columns(5)

    for i, aumento in enumerate(botoes):
        novo_lance = valor_atual + aumento
        with colunas[i % 5]:
            if st.button(f"➕ R$ {novo_lance:,.0f}".replace(",", "."), key=f"lance_{leilao['id']}_{i}"):
                saldo_res = supabase.table("times").select("saldo").eq("id", id_time_usuario).execute()
                saldo = saldo_res.data[0]["saldo"]
                if novo_lance > saldo:
                    st.error("❌ Saldo insuficiente.")
                else:
                    agora = datetime.utcnow()
                    if (fim_dt - agora).total_seconds() <= 15:
                        fim_dt = agora + timedelta(seconds=15)

                    try:
                        update_payload = {
                            "valor_atual": novo_lance,
                            "id_time_atual": id_time_usuario,
                            "fim": fim_dt.isoformat()
                        }

                        if nome_time_usuario:
                            update_payload["time_vencedor"] = nome_time_usuario

                        supabase.table("leiloes").update(update_payload).eq("id", leilao["id"]).execute()

                        st.success("✅ Lance enviado com sucesso!")
                        st.experimental_rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar o leilão: {e}")

# 🔁 Botão manual para atualizar
st.markdown("---")
if st.button("🔄 Atualizar Página"):
    st.experimental_rerun()


