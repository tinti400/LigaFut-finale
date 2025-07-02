# 20_🔧 Admin Leilao.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import uuid
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

# 📥 Importar jogadores via Excel
st.markdown("### 📊 Importar Jogadores em Lote via Excel")

uploaded_file = st.file_uploader("Selecione um arquivo Excel (.xlsx) com os jogadores para a Fila de Leilão", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.dataframe(df)

        if st.button("📥 Enviar jogadores para a fila"):
            for _, row in df.iterrows():
                supabase.table("fila_leilao").insert({
                    "id": str(uuid.uuid4()),
                    "nome": row["nome"],
                    "posicao": row["posicao"],
                    "overall": int(row["overall"]),
                    "valor": int(row["valor"]),
                    "imagem_url": row.get("imagem_url", ""),
                    "link_sofifa": row.get("link_sofifa", ""),
                    "status": "aguardando"
                }).execute()
            st.success("✅ Jogadores importados para a fila de leilão com sucesso!")
            st.experimental_rerun()

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")

# 📂 Fila de jogadores aguardando leilão
st.subheader("📥 Jogadores na Fila de Leilão (Aguardando Inclusão)")

fila = supabase.table("fila_leilao").select("*").eq("status", "aguardando").execute().data

if fila:
    for jogador in fila:
        with st.container():
            cols = st.columns([1, 3, 2, 2, 2])
            cols[0].image(jogador.get("imagem_url", ""), width=80)
            cols[1].markdown(f"**{jogador.get('nome', 'Sem Nome')}**")
            cols[1].markdown(f"`{jogador.get('posicao', 'ND')}` | Overall: {jogador.get('overall', '-')}")
            cols[2].markdown(f"💰 R$ {int(jogador.get('valor', 0)):,}".replace(",", "."))
            if jogador.get("link_sofifa"):
                cols[3].markdown(f"[📄 Ficha Técnica](https://{jogador['link_sofifa'].lstrip('https://')})")

            if cols[4].button("📢 Criar Leilão", key=f"criar_{jogador['id']}"):
                try:
                    agora = datetime.utcnow()
                    fim = agora + timedelta(minutes=2)

                    supabase.table("leiloes").insert({
                        "nome_jogador": jogador.get("nome", "Sem Nome"),
                        "posicao_jogador": jogador.get("posicao", "ND"),
                        "overall_jogador": jogador.get("overall", 0),
                        "valor_inicial": int(jogador.get("valor", 0)),
                        "valor_atual": int(jogador.get("valor", 0)),
                        "incremento_minimo": 3_000_000,
                        "inicio": agora.isoformat(),
                        "fim": fim.isoformat(),
                        "ativo": False,
                        "finalizado": False,
                        "origem": "Base",
                        "nacionalidade": "Desconhecida",
                        "imagem_url": jogador.get("imagem_url", ""),
                        "link_sofifa": jogador.get("link_sofifa", ""),
                        "enviado_bid": False,
                        "validado": False,
                        "aguardando_validacao": False,
                        "tempo_minutos": 2
                    }).execute()

                    supabase.table("fila_leilao").update({"status": "enviado"}).eq("id", jogador["id"]).execute()
                    st.success(f"✅ {jogador['nome']} movido para a fila oficial de leilões.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao criar leilão: {e}")
else:
    st.info("✅ Nenhum jogador aguardando na fila de leilão.")

# 🔄 Ativar até 3 leilões simultâneos
ativos = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).execute().data

if ativos:
    st.subheader("🔴 Leilões Ativos")
    for ativo in ativos:
        st.markdown(f"**Jogador:** {ativo['nome_jogador']}")
        st.markdown(f"**Posição:** {ativo['posicao_jogador']}")
        st.markdown(f"**Valor Atual:** R$ {ativo['valor_atual']:,.0f}".replace(",", "."))
        st.markdown(f"**Origem:** {ativo.get('origem', 'Desconhecida')}")
        st.markdown(f"**Nacionalidade:** {ativo.get('nacionalidade', 'Desconhecida')}")

        if ativo.get("link_sofifa"):
            st.markdown(f"[📄 Ficha Técnica (SoFIFA)]({ativo['link_sofifa']})", unsafe_allow_html=True)

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
            tempo = leilao.get("tempo_minutos", 2)
            fim = agora + timedelta(minutes=tempo)
            supabase.table("leiloes").update({
                "ativo": True,
                "inicio": agora.isoformat(),
                "fim": fim.isoformat()
            }).eq("id", leilao["id"]).execute()
        st.success("✅ Novos leilões iniciados automaticamente.")
        st.experimental_rerun()
    else:
        st.info("✅ Nenhum leilão ativo. Fila vazia.")

# 📄 Leilões aguardando validação
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
        nome = item.get("nome_jogador") or "Jogador sem nome"
        posicao = item.get("posicao_jogador") or "Posição indefinida"
        valor = item.get("valor_atual", 0)
        id_time = item.get("id_time_atual")

        st.markdown(f"**{nome}** ({posicao}) - R$ {valor:,.0f}".replace(",", "."))

        if item.get("link_sofifa"):
            st.markdown(f"[📄 Ficha Técnica (SoFIFA)]({item['link_sofifa']})", unsafe_allow_html=True)

        if st.button(f"✅ Validar Leilão de {nome}", key=f"validar_{item['id']}"):
            try:
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": nome,
                    "posicao": posicao,
                    "overall": item["overall_jogador"],
                    "valor": valor,
                    "origem": item.get("origem", ""),
                    "nacionalidade": item.get("nacionalidade", ""),
                    "imagem_url": item.get("imagem_url", ""),
                    "link_sofifa": item.get("link_sofifa", "")
                }).execute()

                saldo_res = supabase.table("times").select("saldo, nome").eq("id", id_time).execute()
                if saldo_res.data:
                    saldo = saldo_res.data[0]["saldo"]
                    nome_time = saldo_res.data[0]["nome"]
                    novo_saldo = saldo - valor
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    registrar_movimentacao(
                        id_time=id_time,
                        tipo="saida",
                        valor=valor,
                        descricao=f"Compra do jogador {nome} via leilão",
                        jogador=nome,
                        categoria="leilao",
                        origem=item.get("origem", ""),
                        destino=nome_time
                    )

                supabase.table("leiloes").update({
                    "validado": True,
                    "finalizado": True,
                    "enviado_bid": True,
                    "aguardando_validacao": False
                }).eq("id", item["id"]).execute()

                st.success(f"✅ {nome} foi validado e adicionado ao elenco com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao validar o leilão: {e}")

# 🪨 Botão para limpar histórico de leilões
st.markdown("---")
st.subheader("🪨 Limpar Histórico de Leilões Enviados ao BID")

if st.button("🪩 Apagar Histórico de Leilões Enviados"):
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
