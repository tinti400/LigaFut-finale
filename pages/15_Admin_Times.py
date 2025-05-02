import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Admin - Times", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# Verifica se é admin por e-mail
email_usuario = st.session_state.get("usuario", "")

if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

# Verifica se o usuário é admin
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = len(admin_ref.data) > 0

if not eh_admin:
    st.warning("🔒 Acesso restrito apenas para administradores.")
    st.stop()

st.title("🛠️ Administração de Times")

# 📦 Buscar todos os times
times_ref = supabase.table("times").select("id", "nome", "saldo").execute()
times = times_ref.data

# 🔽 Selecionar time para adicionar ou ajustar saldo
nomes_times = [f"{t['nome']} (ID: {t['id']})" for t in times]
escolhido = st.selectbox("Selecione um time:", nomes_times)

indice = nomes_times.index(escolhido)
time = times[indice]
id_time = time["id"]
nome_time = time["nome"]
saldo_atual = time.get("saldo", 0)

st.markdown(f"### 💼 {nome_time}")
st.markdown(f"**Saldo atual:** R$ {saldo_atual:,.0f}".replace(",", "."))

# ➕ Adicionar valor ao saldo
st.subheader("➕ Adicionar valor ao saldo")
valor = st.number_input("💰 Valor a adicionar (R$)", min_value=1_000_000, step=500_000, format="%d")

if st.button("✅ Adicionar saldo"):
    if valor > 0:
        try:
            novo_saldo = saldo_atual + valor
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            # Registrar movimentação
            st.success(f"✅ R$ {valor:,.0f} adicionados ao clube {nome_time}".replace(",", "."))
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar saldo: {e}")
    else:
        st.warning("Informe um valor válido.")

# ✏️ Ajustar diretamente o valor do saldo
st.markdown("---")
st.subheader("✏️ Atualização direta do saldo")

novo_valor_manual = st.number_input("💼 Novo valor de saldo (R$)", min_value=0, step=1_000_000, format="%d")

if st.button("✏️ Atualizar saldo manualmente"):
    try:
        diferenca = novo_valor_manual - saldo_atual
        tipo = "entrada" if diferenca > 0 else "saida"
        descricao = "Ajuste manual de saldo pelo administrador"

        supabase.table("times").update({"saldo": novo_valor_manual}).eq("id", id_time).execute()
        # Registrar movimentação
        st.success(f"✅ Saldo do time {nome_time} atualizado para R$ {novo_valor_manual:,.0f}".replace(",", "."))
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao atualizar saldo manualmente: {e}")
