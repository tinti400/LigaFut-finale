import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Importar Mercado", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 👑 Verifica se é admin por e-mail
email_usuario = st.session_state.get("usuario", "")
if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

# Verifica se o usuário é administrador no caminho correto (tabela 'usuarios', campo 'administrador')
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()

# Checa se o usuário é um administrador
eh_admin = admin_ref.data and admin_ref.data[0]["administrador"] is True  # Verifica se é True

if not eh_admin:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧭 Título
st.markdown("<h1 style='text-align: center;'>📦 Importar Jogadores para o Mercado</h1><hr>", unsafe_allow_html=True)

# 📤 Upload do arquivo
arquivo = st.file_uploader("📂 Selecione um arquivo .xlsx com os jogadores", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)

        # Tratamento de colunas com nomes diferentes
        colunas_esperadas = {
            "foto": "foto",
            "nome": "nome",
            "posicao": "posicao",
            "posição": "posicao",
            "overall": "overall",
            "valor": "valor",
            "nacionalidade": "nacionalidade",
            "time de origem": "time_origem",
            "time_origem": "time_origem"
        }

        # Renomeando colunas de forma mais robusta
        df = df.rename(columns={col.lower(): colunas_esperadas.get(col.lower(), col) for col in df.columns})

        obrigatorias = ["nome", "posicao", "overall", "valor", "nacionalidade", "time_origem"]
        if not all(col in df.columns for col in obrigatorias):
            st.error(f"❌ A planilha deve conter as colunas: {', '.join(obrigatorias)}")
            st.stop()

        with st.expander("👀 Visualizar Jogadores Importados"):
            st.dataframe(df)

        if st.button("🚀 Enviar jogadores ao mercado"):
            count = 0
            for _, row in df.iterrows():
                try:
                    # Verificar se o jogador já está no mercado
                    existing_player = supabase.table("mercado_transferencias").select("id").eq("nome", row["nome"]).execute().data
                    if existing_player:
                        st.warning(f"⚠️ O jogador {row['nome']} já está no mercado.")
                        continue

                    # Adicionando jogador no mercado
                    supabase.table("mercado_transferencias").insert({
                        "nome": str(row["nome"]),
                        "posicao": str(row["posicao"]),
                        "overall": int(row["overall"]),
                        "valor": float(row["valor"]),
                        "nacionalidade": str(row["nacionalidade"]),
                        "time_origem": str(row["time_origem"]),
                        "foto": str(row["foto"]) if "foto" in row and pd.notna(row["foto"]) else ""
                    }).execute()

                    count += 1
                except Exception as e:
                    st.error(f"Erro ao adicionar jogador: {e}")
            st.success(f"✅ {count} jogadores adicionados ao mercado com sucesso!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
