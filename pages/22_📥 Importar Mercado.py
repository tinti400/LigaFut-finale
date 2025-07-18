import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Importar Mercado", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 👑 Verificação de Admin
email_usuario = st.session_state.get("usuario", "")
if not email_usuario or "/" in email_usuario:
    st.error("⚠️ E-mail inválido para verificação de admin.")
    st.stop()

admin_check = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_check.data and admin_check.data[0].get("administrador", False)

if not eh_admin:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧭 Título
st.markdown("<h1 style='text-align: center;'>📦 Importar Jogadores para o Mercado</h1><hr>", unsafe_allow_html=True)

# 📤 Upload
arquivo = st.file_uploader("📂 Selecione um arquivo .xlsx com os jogadores", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)

        # 🔁 Normalização de Colunas
        colunas_esperadas = {
            "foto": "foto",
            "nome": "nome",
            "posicao": "posicao",
            "posição": "posicao",
            "overall": "overall",
            "valor": "valor",
            "nacionalidade": "nacionalidade",
            "time de origem": "time_origem",
            "time_origem": "time_origem",
            "link_sofifa": "link_sofifa",
            "link sofifa": "link_sofifa"
        }
        df.rename(columns={col: colunas_esperadas.get(col.lower(), col) for col in df.columns}, inplace=True)

        # Filtrar colunas válidas
        colunas_validas = ["nome", "posicao", "overall", "valor", "nacionalidade", "time_origem", "foto", "link_sofifa"]
        df = df[[col for col in colunas_validas if col in df.columns]]

        obrigatorias = ["nome", "posicao", "overall", "valor", "nacionalidade", "time_origem"]
        if not all(col in df.columns for col in obrigatorias):
            st.error(f"❌ A planilha deve conter as colunas obrigatórias: {', '.join(obrigatorias)}")
            st.stop()

        with st.expander("👀 Visualizar Jogadores Importados"):
            st.dataframe(df)

        if st.button("🚀 Enviar jogadores ao mercado"):
            adicionados = 0
            for _, row in df.iterrows():
                try:
                    # ✅ Verifica se já existe no mercado
                    existing = supabase.table("mercado_transferencias").select("id").eq("nome", str(row["nome"])).execute()
                    if existing.data:
                        st.warning(f"⚠️ O jogador {row['nome']} já está no mercado.")
                        continue

                    # ✅ Insere jogador (aceitando link_sofifa)
                    supabase.table("mercado_transferencias").insert({
                        "nome": str(row["nome"]),
                        "posicao": str(row["posicao"]),
                        "overall": int(row["overall"]),
                        "valor": float(row["valor"]),
                        "nacionalidade": str(row["nacionalidade"]),
                        "time_origem": str(row["time_origem"]),
                        "foto": str(row.get("foto", "")) if pd.notna(row.get("foto", "")) else "",
                        "link_sofifa": str(row.get("link_sofifa", "")) if pd.notna(row.get("link_sofifa", "")) else ""
                    }).execute()
                    adicionados += 1

                except Exception as e:
                    st.error(f"❌ Erro ao adicionar {row['nome']}: {e}")

            st.success(f"✅ {adicionados} jogadores adicionados ao mercado com sucesso!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
