import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="BID da LigaFut", layout="wide")
st.title("📋 BID da LigaFut")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔄 Recupera últimas 100 movimentações (qualquer time)
try:
    mov_ref = supabase.table("movimentacoes").select("*").order("data", desc=True).limit(100).execute()
    movimentacoes = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    movimentacoes = []

# 🔁 Mapeia os IDs dos times para nomes
try:
    times_res = supabase.table("times").select("id", "nome").execute()
    times_map = {t["id"]: t["nome"] for t in times_res.data}
except Exception as e:
    st.error(f"Erro ao buscar nomes dos times: {e}")
    times_map = {}

# 📋 Exibe histórico
if not movimentacoes:
    st.info("Nenhuma movimentação registrada ainda.")
else:
    for mov in movimentacoes:
        jogador = mov.get("jogador", "Desconhecido")
        categoria = mov.get("categoria", "N/A")  # Ex: "Roubo", "Proposta", "Leilão", "Multa"
        tipo = mov.get("tipo", "N/A")            # Ex: "Compra", "Venda"
        valor = mov.get("valor", 0)
        data = mov.get("data", "")
        id_time = mov.get("id_time", "")
        nome_time = times_map.get(id_time, "Desconhecido")

        # Formata data
        try:
            data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = "Data inválida"

        # Formata valor
        valor_str = f"R$ {valor:,.0f}".replace(",", ".")

        # Exibição
        st.markdown("###")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"📅 **Data:** {data_formatada}")
        with col2:
            st.markdown(f"🏷️ **Time:** {nome_time}")

        st.markdown(f"**👤 Jogador:** {jogador}")
        st.markdown(f"**📂 Categoria:** {categoria}")
        st.markdown(f"**💬 Tipo:** {tipo}")
        st.markdown(f"**💰 Valor:** {valor_str}")
        st.markdown("---")
