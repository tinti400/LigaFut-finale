import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Histórico de Transferências", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]

st.title("📜 Histórico de Transferências")

# 🔄 Recupera movimentações da tabela 'movimentacoes'
try:
    mov_ref = supabase.table("movimentacoes").select("*").eq("id_time", id_time).order("data", desc=True).execute()
    movimentacoes = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    movimentacoes = []

# 📋 Exibe histórico
if not movimentacoes:
    st.info("Nenhuma movimentação registrada.")
else:
    for mov in movimentacoes:
        jogador = mov.get("jogador", "Desconhecido")
        categoria = mov.get("categoria", "N/A")  # Ex: "Roubo", "Proposta", "Leilão"
        tipo = mov.get("tipo", "N/A")            # Ex: "Compra", "Venda"
        valor = mov.get("valor", 0)
        data = mov.get("data", None)

        # 🔁 Formata data
        if data:
            try:
                data = datetime.fromisoformat(data)
                data_str = data.strftime('%d/%m/%Y %H:%M')
            except:
                data_str = "Data inválida"
        else:
            data_str = "Data não disponível"

        # 💵 Trata valor
        if isinstance(valor, (int, float)):
            valor_str = f"R$ {valor:,.0f}".replace(",", ".")
        else:
            valor_str = "Valor indisponível"

        st.markdown("---")
        st.markdown(f"**👤 Jogador:** {jogador}")
        st.markdown(f"**📂 Categoria:** {categoria}")
        st.markdown(f"**💬 Tipo:** {tipo}")
        st.markdown(f"**💰 Valor:** {valor_str}")
        st.markdown(f"**📅 Data:** {data_str}")
