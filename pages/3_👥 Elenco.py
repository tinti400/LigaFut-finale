import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown("<h1 style='text-align: center;'>👥 Elenco do Técnico</h1><hr>", unsafe_allow_html=True)

# 🛑 Verifica se o mercado está aberto
try:
    res = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
    mercado_aberto = res.data[0]["mercado_aberto"] if res.data else False
except Exception as e:
    st.error(f"Erro ao verificar status do mercado: {e}")
    mercado_aberto = False

# 🔢 Buscar elenco
try:
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    elenco = []

# 🎯 Filtros
if elenco:
    st.subheader("🎯 Filtros")
    df_elenco = pd.DataFrame(elenco)

    posicoes = sorted(df_elenco["posicao"].unique())
    posicao_selecionada = st.selectbox("📌 Filtrar por posição:", ["Todas"] + posicoes)
    nome_filtrado = st.text_input("🔍 Buscar por nome:")
    overall_min = st.slider("⭐ Filtrar por Overall mínimo:", min_value=0, max_value=100, value=0)

    # Aplicar filtros
    df_filtrado = df_elenco.copy()
    if posicao_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["posicao"] == posicao_selecionada]
    if nome_filtrado:
        df_filtrado = df_filtrado[df_filtrado["nome"].str.contains(nome_filtrado, case=False, na=False)]
    df_filtrado = df_filtrado[df_filtrado["overall"] >= overall_min]

    # Exibir resultado filtrado
    if df_filtrado.empty:
        st.info("Nenhum jogador encontrado com os filtros aplicados.")
    else:
        total_valor = df_filtrado["valor"].sum()
        st.markdown(f"**👥 Jogadores filtrados:** `{len(df_filtrado)}`")
        st.markdown(f"**💰 Valor total:** `R$ {total_valor:,.0f}`".replace(",", "."))

        for _, jogador in df_filtrado.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2.5, 2.5, 1.5, 1.5, 2])
            with col1:
                st.markdown(f"**👤 Nome:** {jogador['nome']}")
            with col2:
                st.markdown(f"**📌 Posição:** {jogador['posicao']}")
            with col3:
                st.markdown(f"**⭐ Overall:** {jogador['overall']}")
            with col4:
                st.markdown(f"**💰 Valor:** R$ {jogador['valor']:,.0f}".replace(",", "."))
            with col5:
                if mercado_aberto:
                    if st.button(f"❌ Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
                        try:
                            valor_jogador = jogador["valor"]
                            valor_recebido = round(valor_jogador * 0.7)

                            # Remove do elenco
                            supabase.table("elenco").delete().eq("id_time", id_time).eq("id", jogador["id"]).execute()

                            # Adiciona ao mercado
                            supabase.table("mercado_transferencias").insert({
                                "nome": jogador["nome"],
                                "posicao": jogador["posicao"],
                                "overall": jogador["overall"],
                                "valor": jogador["valor"]
                            }).execute()

                            # Atualiza saldo
                            saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
                            saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
                            novo_saldo = saldo + valor_recebido
                            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                            # Registra no BID
                            supabase.table("movimentacoes").insert({
                                "jogador": jogador["nome"],
                                "valor": jogador["valor"],
                                "tipo": "Venda",
                                "categoria": "Mercado",
                                "id_time": id_time,
                                "data": datetime.now().isoformat()
                            }).execute()

                            st.success(f"✅ {jogador['nome']} vendido! Você recebeu R$ {valor_recebido:,.0f}".replace(",", "."))
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao vender jogador: {e}")
                else:
                    st.warning("🚫 Mercado fechado")
else:
    st.info("📭 Seu elenco está vazio.")

# 🔙 Voltar ao painel
if st.button("🔙 Voltar ao Painel"):
    st.session_state["pagina"] = "usuario"
    st.experimental_rerun()

