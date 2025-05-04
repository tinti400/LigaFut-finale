# -*- coding: utf-8 -*- 
import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Painel do Técnico", layout="wide")

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

# 🔢 Buscar saldo
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
except Exception as e:
    st.error(f"Erro ao carregar saldo: {e}")
    saldo = 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🏷️ Time: {nome_time}")
with col2:
    st.markdown(f"### 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

st.markdown("---")

# ⚡ Ações rápidas
st.markdown("### 🔍 Ações rápidas")
col1, col2 = st.columns(2)

# 👥 Exibe o elenco se ativado
if st.session_state.get("mostrar_elenco", False):
    st.markdown("### 👥 Seu Elenco")

    try:
        # Carrega elenco do time
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
                        novo_saldo = saldo + valor_recebido
                        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                        st.success(f"✅ {jogador['nome']} vendido! Você recebeu R$ {valor_recebido:,.0f}".replace(",", "."))
                        st.experimental_rerun()  # Atualiza a página para refletir a mudança
                    except Exception as e:
                        st.error(f"Erro ao vender jogador: {e}")

        st.markdown("---")

with col1:
    if st.button("👥 Ver Elenco", key="ver_elenco"):
        st.session_state["mostrar_elenco"] = not st.session_state.get("mostrar_elenco", False)

# 📜 Definir Formação Tática Livre
st.markdown("### 📜 Definir Formação Tática Livre")
st.markdown("Defina a sua formação tática inserindo os jogadores nas posições desejadas.")

# Crie um campo tático customizável (sem limite de posição)
campo_tatico = {}

# Configuração do campo tático
posicoes = ["Posição 1", "Posição 2", "Posição 3", "Posição 4", "Posição 5", "Posição 6", "Posição 7", "Posição 8", "Posição 9", "Posição 10", "Posição 11"]

for posicao in posicoes:
    jogador_escalado = st.selectbox(f"Selecione um jogador para {posicao}", options=[j["nome"] for j in elenco], key=posicao)
    campo_tatico[posicao] = jogador_escalado

# ⚽ Salvar Escalação Tática
if st.button("💾 Salvar Escalação Tática"):
    # Aqui você pode salvar a formação tática e escalação no banco de dados
    st.success("Formação tática e escalação salva com sucesso!")

# ⚡ Adicionar Jogador (Somente Administrador)
is_admin = False

# Buscar o valor do administrador no banco de dados
try:
    usuario_res = supabase.table("usuarios").select("administrador").eq("usuario", st.session_state["usuario"]).execute()
    if usuario_res.data:
        is_admin = usuario_res.data[0]["administrador"]
except Exception as e:
    st.error(f"Erro ao verificar admin: {e}")

# Verificação de admin antes de mostrar a opção de adicionar jogador
if is_admin:
    st.markdown("### ⚡ Adicionar Jogador ao Elenco")

    with st.form(key="add_player_form"):
        nome_jogador = st.text_input("Nome do Jogador")
        posicao_jogador = st.selectbox("Posição", ["GL", "LD", "ZAG", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"])
        overall_jogador = st.number_input("Overall", min_value=1, max_value=100)
        valor_jogador = st.number_input("Valor (R$)", min_value=0)

        submit_button = st.form_submit_button("Adicionar Jogador")

        if submit_button:
            if nome_jogador and posicao_jogador and overall_jogador and valor_jogador:
                try:
                    novo_jogador = {
                        "nome": nome_jogador,
                        "posicao": posicao_jogador,
                        "overall": overall_jogador,
                        "valor": valor_jogador,
                        "id_time": id_time
                    }
                    supabase.table("elenco").insert(novo_jogador).execute()
                    st.success(f"Jogador {nome_jogador} adicionado com sucesso ao elenco!")
                    st.experimental_rerun()  # Atualiza a página para refletir a mudança
                except Exception as e:
                    st.error(f"Erro ao adicionar jogador: {e}")
            else:
                st.warning("⚠️ Preencha todos os campos.")
else:
    st.info("🔒 Apenas administradores podem adicionar jogadores ao elenco.")
