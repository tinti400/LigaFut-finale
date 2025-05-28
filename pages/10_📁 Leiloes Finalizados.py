import streamlit as st
from supabase import create_client
from datetime import datetime
from dateutil.parser import parse

st.set_page_config(page_title="Leilões Finalizados - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.title("📜 Leilões Finalizados")

# 🔎 Buscar todos os leilões finalizados
try:
    leiloes_ref = supabase.table("leiloes").select("*").eq("finalizado", True).order("fim", desc=True).execute()
    leiloes = leiloes_ref.data

    if not leiloes:
        st.info("Nenhum leilão finalizado até o momento.")
    else:
        for leilao in leiloes:
            jogador = leilao.get("jogador", {})
            nome_jogador = jogador.get("nome", "Desconhecido")
            posicao = jogador.get("posicao", "-")
            overall = jogador.get("overall", "N/A")
            valor = leilao.get("valor_atual", 0)
            time_vencedor = leilao.get("time_vencedor", "Sem vencedor")
            fim = leilao.get("fim")

            # Verificar e formatar a data de fim corretamente
            if isinstance(fim, str):
                fim_dt = parse(fim)
                fim_str = fim_dt.strftime("%d/%m/%Y %H:%M")
            else:
                fim_str = "Data desconhecida"

            with st.container():
                st.markdown("---")
                st.markdown(f"**🎯 Jogador:** {nome_jogador} ({posicao}) - ⭐ {overall}")
                st.markdown(f"**💰 Valor Final:** R$ {valor:,.0f}".replace(",", "."))
                st.markdown(f"**🏆 Time Vencedor:** {time_vencedor}")
                st.markdown(f"**🕒 Finalizado em:** {fim_str}")

except Exception as e:
    st.error(f"Erro ao carregar leilões finalizados: {e}")
