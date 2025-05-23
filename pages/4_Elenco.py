import streamlit as st
from supabase import create_client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>👥 Elenco do Técnico</h1><hr>", unsafe_allow_html=True)

# 🔢 Buscar elenco
try:
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    elenco = []

if not elenco:
    st.info("📭 Seu elenco está vazio.")
else:
    # Exibe os jogadores do elenco
    for jogador in elenco:
        col1, col2, col3, col4, col5 = st.columns([2.5, 2.5, 1.5, 1.5, 2])
        with col1:
            st.markdown(f"**👤 Nome:** {jogador.get('nome', '')}")
        with col2:
            st.markdown(f"**📌 Posição:** {jogador.get('posicao', '')}")
        with col3:
            st.markdown(f"**⭐ Overall:** {jogador.get('overall', '')}")
        with col4:
            st.markdown(f"**💰 Valor:** R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
        with col5:
            # Botão de Vender com chave única
            if st.button(f"❌ Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):  # Usando ID do jogador para chave única
                try:
                    valor_jogador = jogador.get("valor", 0)
                    valor_recebido = round(valor_jogador * 0.7)  # 70% do valor do jogador

                    # 1. Remove do elenco
                    supabase.table("elenco").delete().eq("id_time", id_time).eq("id", jogador["id"]).execute()

                    # 2. Adiciona no mercado com valor cheio
                    jogador_mercado = {
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": jogador["valor"]
                    }
                    supabase.table("mercado_transferencias").insert(jogador_mercado).execute()

                    # 3. Atualiza saldo
                    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
                    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
                    novo_saldo = saldo + valor_recebido
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    st.success(f"✅ {jogador['nome']} vendido! Você recebeu R$ {valor_recebido:,.0f}".replace(",", "."))
                    st.experimental_rerun()  # Força atualização da tela
                except Exception as e:
                    st.error(f"Erro ao vender jogador: {e}")

# ⚡ Botão de voltar ao painel do técnico
if st.button("🔙 Voltar ao Painel"):
    st.session_state["pagina"] = "usuario"  # Navegar de volta ao painel
    st.experimental_rerun()
