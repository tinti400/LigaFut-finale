import streamlit as st
from supabase import create_client, Client

# 🔐 Conexão com Supabase usando secrets
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Cadastro - LigaFut", page_icon="📝", layout="centered")
st.title("📝 Cadastro de Técnico + Time")

# 📄 Formulário de cadastro
with st.form("cadastro_form"):
    usuario = st.text_input("Usuário (e-mail)")
    senha = st.text_input("Senha", type="password")
    nome_time = st.text_input("Nome do novo time")
    divisao = st.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
    botao_cadastrar = st.form_submit_button("Cadastrar")

# ✅ Lógica do cadastro
if botao_cadastrar:
    if usuario and senha and nome_time and divisao:
        try:
            # Verifica se já existe usuário com mesmo e-mail
            existe = supabase.table("usuarios").select("*").ilike("usuario", usuario).execute()
            if existe.data:
                st.warning("⚠️ Usuário já existe. Tente outro e-mail.")
            else:
                # Cria o novo time com saldo inicial de R$350 milhões
                time_res = supabase.table("Times").insert({
                    "nome": nome_time,
                    "saldo": 350_000_000
                }).execute()

                time_id = time_res.data[0]["id"]

                # Cria o novo usuário vinculado ao time e à divisão
                supabase.table("usuarios").insert({
                    "usuario": usuario,
                    "senha": senha,
                    "time_id": time_id,
                    "divisao": divisao
                }).execute()

                st.success("✅ Técnico e time cadastrados com sucesso!")
                st.info("Agora você já pode fazer login.")
        except Exception as e:
            st.error(f"Erro no cadastro: {e}")
    else:
        st.warning("⚠️ Preencha todos os campos.")
