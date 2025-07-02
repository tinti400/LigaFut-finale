# 20_🔧 Admin Leilao.py (completo e atualizado)
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

# 📊 Importação Excel
st.markdown("### 📊 Importar Jogadores via Excel com origem e nacionalidade")
uploaded_file = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().lower() for col in df.columns]
        colunas_esperadas = ["nome", "posicao", "overall", "valor", "imagem_url", "link_sofifa", "origem", "nacionalidade"]
        faltando = [col for col in colunas_esperadas if col not in df.columns]
        if faltando:
            st.error(f"❌ Colunas ausentes na planilha: {faltando}")
        else:
            df = df.fillna("")
            st.dataframe(df)
            if st.button("📥 Enviar jogadores para a fila"):
                for _, row in df.iterrows():
                    try:
                        supabase.table("fila_leilao").insert({
                            "id": str(uuid.uuid4()),
                            "nome": row.get("nome", "").strip(),
                            "posicao": row.get("posicao", "").strip(),
                            "overall": int(row["overall"]) if row["overall"] != "" else 0,
                            "valor": int(row["valor"]) if row["valor"] != "" else 0,
                            "imagem_url": row.get("imagem_url", ""),
                            "link_sofifa": row.get("link_sofifa", ""),
                            "origem": row.get("origem", "Desconhecido"),
                            "nacionalidade": row.get("nacionalidade", "Desconhecida"),
                            "status": "aguardando"
                        }).execute()
                    except Exception as e:
                        st.error(f"❌ Erro ao inserir jogador {row.get('nome', '')}: {e}")
                st.success("✅ Jogadores importados com sucesso!")
                st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")

# 📥 Fila de jogadores aguardando leilão
st.subheader("📥 Jogadores na Fila de Leilão (Aguardando Inclusão)")
fila = supabase.table("fila_leilao").select("*").eq("status", "aguardando").execute().data
ids_exclusao = []
if fila:
    for jogador in fila:
        with st.container():
            cols = st.columns([0.2, 2, 1, 1, 1])
            selecionado = cols[0].checkbox("", key=f"check_{jogador['id']}")
            cols[1].markdown(f"**{jogador.get('nome')}** | `{jogador.get('posicao')}` | Overall: `{jogador.get('overall')}`")
            cols[1].markdown(f"🏷️ Origem: `{jogador.get('origem', '-')}` | 🌍 Nacionalidade: `{jogador.get('nacionalidade', '-')}`")
            cols[2].image(jogador.get("imagem_url", ""), width=60)
            if jogador.get("link_sofifa"):
                cols[3].markdown(f"[📄 Ficha Técnica](https://{jogador['link_sofifa'].lstrip('https://')})")
            if cols[4].button("📢 Criar Leilão", key=f"criar_{jogador['id']}"):
                try:
                    agora = datetime.utcnow()
                    fim = agora + timedelta(minutes=2)
                    supabase.table("leiloes").insert({
                        "nome_jogador": jogador.get("nome"),
                        "posicao_jogador": jogador.get("posicao"),
                        "overall_jogador": jogador.get("overall"),
                        "valor_inicial": jogador.get("valor"),
                        "valor_atual": jogador.get("valor"),
                        "incremento_minimo": 3000000,
                        "inicio": agora.isoformat(),
                        "fim": fim.isoformat(),
                        "ativo": False,
                        "finalizado": False,
                        "imagem_url": jogador.get("imagem_url", ""),
                        "link_sofifa": jogador.get("link_sofifa", ""),
                        "origem": jogador.get("origem", "Desconhecido"),
                        "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                        "enviado_bid": False,
                        "validado": False,
                        "aguardando_validacao": False,
                        "tempo_minutos": 2
                    }).execute()
                    supabase.table("fila_leilao").update({"status": "enviado"}).eq("id", jogador["id"]).execute()
                    st.success(f"{jogador['nome']} movido para leilão.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao criar leilão: {e}")
            if selecionado:
                ids_exclusao.append(jogador["id"])

    # Botão para excluir os selecionados
    if ids_exclusao:
        if st.button("🗑️ Excluir Selecionados da Fila"):
            try:
                for id_excluir in ids_exclusao:
                    supabase.table("fila_leilao").delete().eq("id", id_excluir).execute()
                st.success(f"{len(ids_exclusao)} jogadores excluídos da fila.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
else:
    st.info("Nenhum jogador aguardando.")

# 🔄 Ativação automática de leilões
ativos = supabase.table("leiloes").select("*").eq("ativo", True).eq("finalizado", False).execute().data
if not ativos:
    inativos = supabase.table("leiloes").select("*").eq("ativo", False).eq("finalizado", False).eq("aguardando_validacao", False).order("valor_atual").limit(3).execute().data
    if inativos:
        agora = datetime.utcnow()
        for leilao in inativos:
            fim = agora + timedelta(minutes=leilao.get("tempo_minutos", 2))
            supabase.table("leiloes").update({"ativo": True, "inicio": agora.isoformat(), "fim": fim.isoformat()}).eq("id", leilao["id"]).execute()
        st.success("Novos leilões ativados.")
        st.experimental_rerun()

# 📄 Leilões aguardando validação
st.subheader("📄 Leilões Aguardando Validação")
pendentes = supabase.table("leiloes").select("*").eq("aguardando_validacao", True).eq("validado", False).order("fim", desc=True).limit(5).execute().data
if pendentes:
    for item in pendentes:
        nome = item["nome_jogador"]
        posicao = item["posicao_jogador"]
        valor = item["valor_atual"]
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
                        id_time, "saida", valor,
                        f"Compra do jogador {nome} via leilão",
                        nome, "leilao",
                        item.get("origem", ""),
                        nome_time
                    )

                supabase.table("leiloes").update({
                    "validado": True,
                    "finalizado": True,
                    "enviado_bid": True,
                    "aguardando_validacao": False
                }).eq("id", item["id"]).execute()

                st.success(f"{nome} validado e adicionado ao elenco.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao validar leilão: {e}")

# 🧹 Apagar histórico
st.markdown("---")
st.subheader("🪨 Limpar Histórico de Leilões Enviados")
if st.button("🪩 Apagar Histórico"):
    try:
        supabase.table("leiloes").delete().eq("finalizado", True).eq("enviado_bid", True).execute()
        st.success("Histórico apagado.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao apagar histórico: {e}")
