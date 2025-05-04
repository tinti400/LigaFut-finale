import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Admin - Mercado", layout="wide")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state.usuario_id
email_usuario = st.session_state.get("usuario", "")

# 👑 Verifica se é admin
admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0

if not eh_admin:
    st.warning("🔒 Acesso permitido apenas para administradores.")
    st.stop()

# 🧭 Título
st.markdown("<h1 style='text-align: center;'>⚙️ Admin - Mercado de Transferências</h1><hr>", unsafe_allow_html=True)

# 🔓 Status do mercado
mercado_cfg_ref = supabase.table("configuracoes").select("aberto").eq("id", 1).execute()
mercado_aberto = mercado_cfg_ref.data[0].get("aberto", False) if mercado_cfg_ref.data else False

st.markdown(f"### 🛒 Status atual do mercado: **{'Aberto' if mercado_aberto else 'Fechado'}**")

# 🔘 Botões de controle
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    if st.button("🟢 Abrir Mercado"):
        try:
            supabase.table("configuracoes").update({"aberto": True}).eq("id", 1).execute()
            st.success("✅ Mercado aberto com sucesso!")
        except Exception as e:
            st.error(f"Erro ao abrir mercado: {e}")

with col2:
    if st.button("🔴 Fechar Mercado"):
        try:
            supabase.table("configuracoes").update({"aberto": False}).eq("id", 1).execute()
            st.success("✅ Mercado fechado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao fechar mercado: {e}")

with col3:
    if st.button("🧹 Limpar Mercado"):
        try:
            supabase.table("mercado_transferencias").delete().execute()
            st.success("🧹 Todos os jogadores foram removidos do mercado!")
        except Exception as e:
            st.error(f"Erro ao limpar mercado: {e}")

# 📝 Cadastro de jogador no mercado
st.markdown("---")
st.subheader("📥 Adicionar Jogador ao Mercado")

with st.form("form_mercado"):
    nome = st.text_input("Nome do Jogador").strip()
    posicao = st.selectbox("Posição", [
        "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
        "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
        "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
    ])
    overall = st.number_input("Overall", min_value=1, max_value=99, step=1)
    valor = st.number_input("Valor (R$)", min_value=100_000, step=50_000)
    time_origem = st.text_input("Time de Origem").strip()
    nacionalidade = st.text_input("Nacionalidade").strip()
    botao = st.form_submit_button("Adicionar ao Mercado")

if botao:
    if not nome:
        st.warning("Digite o nome do jogador.")
    else:
        try:
            # Adicionar jogador ao mercado no Supabase
            supabase.table("mercado_transferencias").insert({
                "nome": nome,
                "posicao": posicao,
                "overall": overall,
                "valor": valor,
                "time_origem": time_origem if time_origem else "N/A",
                "nacionalidade": nacionalidade if nacionalidade else "N/A"
            }).execute()
            st.success(f"✅ {nome} foi adicionado ao mercado!")
        except Exception as e:
            st.error(f"Erro ao adicionar jogador: {e}")

# 📋 Listagem de jogadores no mercado
st.markdown("---")
st.subheader("📋 Jogadores no Mercado")

try:
    # Carregar todos os jogadores do mercado
    jogadores_mercado_ref = supabase.table("mercado_transferencias").select("*").execute()
    jogadores_mercado = jogadores_mercado_ref.data
    if jogadores_mercado:
        jogadores_df = pd.DataFrame(jogadores_mercado)
        st.dataframe(jogadores_df)

        # Excluir jogadores do mercado
        for jogador in jogadores_mercado:
            if st.button(f"❌ Excluir {jogador['nome']}", key=f"excluir_{jogador['id']}"):
                try:
                    # Excluir jogador do mercado
                    supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()
                    st.success(f"✅ Jogador {jogador['nome']} removido do mercado!")
                    # Atualiza a tabela sem usar st.rerun()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir jogador: {e}")
    else:
        st.info("📭 Nenhum jogador no mercado.")
except Exception as e:
    st.error(f"Erro ao carregar jogadores do mercado: {e}")
