# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é administrador
email_usuario = st.session_state.get("usuario", "")

try:
    admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
    eh_admin = admin_ref.data and admin_ref.data[0].get("administrador", False)

    if not eh_admin:
        st.error("🔒 Acesso restrito! Esta página é exclusiva para administradores.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar permissões de administrador: {e}")
    st.stop()
# -*- coding: utf-8 -*- 
import streamlit as st 
from supabase import create_client 
from datetime import datetime, timedelta

st.set_page_config(page_title="Admin - Leilão", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")

if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = len(admin_ref.data) > 0

if not eh_admin:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧾 Título
st.markdown("<h1 style='text-align: center;'>🧑‍⚖️ Administração de Leilão</h1><hr>", unsafe_allow_html=True)

# 📝 Formulário para criar novo leilão
with st.form("form_leilao"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
    valor_inicial = st.number_input("Valor Inicial (R$)", min_value=100000, step=50000)
    incremento_minimo = st.number_input("Incremento mínimo entre lances (R$)", min_value=100000, step=50000, value=3000000)
    duracao = st.slider("Duração do Leilão (minutos)", min_value=1, max_value=10, value=2)
    botao_criar = st.form_submit_button("Criar Leilão")

# 🔄 Cria ou atualiza o leilão
if botao_criar:
    if not nome:
        st.warning("Informe o nome do jogador.")
    else:
        fim = datetime.utcnow() + timedelta(minutes=duracao)
        inicio = datetime.utcnow()

        dados_leilao = {
            "id": "leilao_sistema",
            "jogador": {
                "nome": nome,
                "posicao": posicao,
                "overall": overall
            },
            "valor_inicial": valor_inicial,
            "valor_atual": valor_inicial,
            "incremento_minimo": incremento_minimo,
            "id_time_atual": None,
            "ultimo_lance": None,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "ativo": True,
            "time_vencedor": ""
        }

        try:
            supabase.table("configuracoes").upsert(dados_leilao).execute()
            st.success(f"✅ Leilão do jogador **{nome}** criado com sucesso!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao criar leilão: {e}")

# 🔘 Controle de ativação do leilão
st.markdown("---")
st.markdown("### ⚙️ Controle de Leilão Ativo")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Ativar Leilão"):
        try:
            supabase.table("configuracoes").update({"ativo": True}).eq("id", "leilao_sistema").execute()
            st.success("Leilão ativado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ativar leilão: {e}")

with col2:
    if st.button("🛑 Desativar Leilão"):
        try:
            supabase.table("configuracoes").update({"ativo": False}).eq("id", "leilao_sistema").execute()
            st.success("Leilão desativado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao desativar leilão: {e}")

# 🔄 Atualização de lances no leilão
st.markdown("---")
st.markdown("### 🏆 Últimos Lances")

leilao_ref = supabase.table("configuracoes").select("*").eq("id", "leilao_sistema").execute()
leilao_data = leilao_ref.data[0] if leilao_ref.data else None

if leilao_data and leilao_data["ativo"]:
    st.markdown(f"**Jogador:** {leilao_data['jogador']['nome']}")
    st.markdown(f"**Posição:** {leilao_data['jogador']['posicao']}")
    st.markdown(f"**Valor Atual:** R$ {leilao_data['valor_atual']:,.0f}".replace(",", "."))

    incremento_minimo = leilao_data.get("incremento_minimo", 3000000)
    lance_minimo = leilao_data["valor_atual"] + incremento_minimo
    
    lance_input = st.number_input(f"Digite seu lance (mínimo de R$ {lance_minimo:,.0f})", min_value=lance_minimo)

    if st.button(f"💸 Dar Lance de R$ {lance_input:,.0f}"):
        try:
            if lance_input >= lance_minimo:
                supabase.table("configuracoes").update({
                    "valor_atual": lance_input,
                    "ultimo_lance": datetime.utcnow().isoformat(),
                    "id_time_atual": st.session_state.get("id_time"),
                    "time_vencedor": f"Time {st.session_state.get('id_time')}"
                }).eq("id", "leilao_sistema").execute()

                st.success(f"✅ Lance de R$ {lance_input:,.0f} realizado com sucesso!")
                st.balloons()
            else:
                st.error(f"❌ O lance deve ser **maior ou igual** a R$ {lance_minimo:,.0f}!")
        except Exception as e:
            st.error(f"Erro ao dar lance: {e}")
else:
    st.info("🔒 O leilão não está ativo.")
