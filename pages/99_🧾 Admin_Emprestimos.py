# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
from utils import registrar_movimentacao

st.set_page_config(page_title="🧾 Admin - Cobrança de Empréstimos", layout="wide")

# 🔐 Conexão
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica se é admin
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state["usuario"]
res_admin = supabase.table("admins").select("*").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito apenas para administradores.")
    st.stop()

st.title("🧾 Painel de Cobrança de Empréstimos")
st.markdown("Use o botão abaixo para **cobrar a parcela por turno** de todos os clubes com empréstimo ativo.")

# 🔍 Buscar todos os empréstimos ativos
emprestimos = supabase.table("emprestimos").select("*").eq("status", "ativo").execute().data

if not emprestimos:
    st.success("✅ Nenhum empréstimo ativo no momento.")
    st.stop()

st.info(f"Total de empréstimos ativos: **{len(emprestimos)}**")

# 📋 Exibir empréstimos em tabela
for emp in emprestimos:
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🏷️ Time:** {emp['nome_time']}")
        st.markdown(f"**💵 Valor Total:** R$ {emp['valor_total']:,}")
        st.markdown(f"**📆 Parcelas Totais:** {emp['parcelas_totais']}")
        st.markdown(f"**🔁 Restantes:** {emp['parcelas_restantes']}")
    with col2:
        st.markdown(f"**💸 Valor por Turno:** R$ {emp['valor_parcela']:,}")
        st.markdown(f"**📈 Juros:** {int(emp['juros'] * 100)}%")
        st.markdown(f"**📅 Início:** {datetime.fromisoformat(emp['data_inicio']).strftime('%d/%m/%Y %H:%M')}")

    if "jogador_garantia" in emp:
        g = emp["jogador_garantia"]
        st.markdown(f"🎯 **Garantia:** {g['nome']} ({g['posicao']}) - R$ {g['valor']:,}")

# 🚨 Botão de cobrança
if st.button("💰 Cobrar parcelas deste turno de todos os clubes"):
    erros = 0
    cobrados = 0

    for emp in emprestimos:
        try:
            id_time = emp["id_time"]
            parcela = emp["valor_parcela"]
            parcelas_restantes = emp["parcelas_restantes"]
            novo_restante = parcelas_restantes - 1
            status_final = "quitado" if novo_restante <= 0 else "ativo"

            # Buscar saldo atual
            res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
            saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
            novo_saldo = saldo_atual - parcela

            # Atualizar time
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            # Atualizar empréstimo
            supabase.table("emprestimos").update({
                "parcelas_restantes": novo_restante,
                "status": status_final
            }).eq("id", emp["id"]).execute()

            # Registrar movimentação
            registrar_movimentacao(
                id_time=id_time,
                tipo="saida",
                valor=parcela,
                descricao="Cobrança de parcela do empréstimo (por turno)",
                categoria="empréstimo"
            )

            cobrados += 1
        except:
            erros += 1

    st.success(f"✅ Parcelas cobradas com sucesso para {cobrados} clubes.")
    if erros > 0:
        st.warning(f"⚠️ {erros} empréstimos não foram cobrados por erro.")
    st.rerun()
