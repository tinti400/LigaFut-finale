import streamlit as st
from supabase import create_client, Client

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# 🖼️ Estilo visual da página
st.set_page_config(page_title="Cadastro - LigaFut", layout="centered")
st.markdown(
    """
    <style>
    body {
        background-color: #0b0c10;
    }
    .titulo-principal {
        font-size: 32px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin-bottom: 30px;
    }
    .stTextInput>div>div>input {
        background-color: #1f2833;
        color: white;
    }
    .stPasswordInput>div>div>input {
        background-color: #1f2833;
        color: white;
    }
    .stSelectbox>div>div {
        background-color: #1f2833;
        color: white;
    }
    .stButton>button {
        background-color: #66fcf1;
        color: black;
        font-weight: bold;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🧾 Título
st.markdown('<div class="titulo-principal">📝 Cadastro de Técnico + Time</div>', unsafe_allow_html=True)

# 📄 Formulário centralizado
with st.form("cadastro_form"):
    usuario = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    nome_time = st.text_input("Nome do novo time")
    divisao = st.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
    botao_cadastrar = st.form_submit_button("Cadastrar")

# 🔄 Cadastro
if botao_cadastrar:
    if usuario and senha and nome_time and divisao:
        try:
            # Verifica duplicidade
            existe = supabase.table("usuarios").select("*").eq("usuario", usuario).execute()
            if existe.data:
                st.warning("⚠️ Usuário já existe. Tente outro e-mail.")
            else:
                # Cria o time
                time_res = supabase.table("times").insert({
                    "nome": nome_time,
                    "saldo": 350_000_000,
                    "tecnico": usuario
                }).execute()

                if not time_res.data:
                    st.error("❌ Erro ao criar o time.")
                else:
                    time_id = time_res.data[0]["id"]

                    # Cria o usuário vinculado ao time
                    supabase.table("usuarios").insert({
                        "usuario": usuario,
                        "senha": senha,
                        "time_id": time_id,
                        "Divisão": divisao
                    }).execute()

                    st.success("✅ Técnico e time cadastrados com sucesso!")
                    st.info("Agora você já pode fazer login.")
        except Exception as e:
            st.error(f"❌ Erro no cadastro: {e}")
    else:
        st.warning("⚠️ Preencha todos os campos.")
