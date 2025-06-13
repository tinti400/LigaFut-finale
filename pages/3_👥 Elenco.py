# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "")
email_usuario = st.session_state.get("usuario", "")

# ⚙️ Verifica se é ADM
admin_check = supabase.table("admins").select("*").eq("email", email_usuario).execute()
is_admin = len(admin_check.data) > 0

st.title(f"👥 Elenco do {nome_time}")

# 💰 Buscar saldo
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

# 📦 Buscar elenco
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

# 🧮 Estatísticas
quantidade = len(jogadores)
valor_total = sum(j.get("valor", 0) for j in jogadores)

st.markdown(
    f"""
    <div style='text-align:center;'>
        <h3 style='color:green;'>💰 Saldo em caixa: <strong>R$ {saldo:,.0f}</strong></h3>
        <h4>👥 Jogadores no elenco: <strong>{quantidade}</strong> | 📈 Valor total do elenco: <strong>R$ {valor_total:,.0f}</strong></h4>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True
)

st.markdown("---")

# 📤 Upload de planilha (somente para ADM)
if is_admin:
    st.subheader("📥 Importar jogadores via Excel")
    planilha = st.file_uploader("Envie um arquivo .xlsx com os jogadores", type=["xlsx"])
    if planilha:
        try:
            df = pd.read_excel(planilha)
            for _, row in df.iterrows():
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": row.get("nome"),
                    "posicao": row.get("posição", ""),
                    "overall": int(row.get("overall", 0)),
                    "valor": float(row.get("valor", 0)),
                    "origem": row.get("origem", "Importado"),
                    "nacionalidade": row.get("nacionalidade", "Desconhecida"),
                    "imagem_url": row.get("imagem_url", "")
                }).execute()
            st.success("✅ Jogadores importados com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

st.markdown("---")

# 🧑‍💼 Lista de jogadores
for jogador in jogadores:
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2.5, 1.5, 1.5, 2.5, 2, 1])

    # 📷 Imagem
    with col1:
        img = jogador.get("imagem_url", "")
        if img:
            st.markdown(f"<img src='{img}' width='60' style='border-radius: 50%; border: 2px solid #ddd;'/>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='width:60px;height:60px;border-radius:50%;border:2px solid #ddd;background:#eee;'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**{jogador.get('nome', 'Sem nome')}**")
        st.markdown(f"🌍 {jogador.get('nacionalidade', 'Desconhecida')}")

    with col3:
        st.markdown(f"📌 {jogador.get('posicao', '-')}")

    with col4:
        st.markdown(f"⭐ {jogador.get('overall', '-')}")

    with col5:
        valor_fmt = "R$ {:,.0f}".format(jogador.get("valor", 0)).replace(",", ".")
        origem = jogador.get("origem", "Desconhecida")
        st.markdown(f"💰 **{valor_fmt}**")
        st.markdown(f"🏟️ {origem}")

    with col6:
        if st.button(f"💸 Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
            try:
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time,
                    "time_origem": nome_time,
                    "imagem_url": jogador.get("imagem_url", ""),
                    "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                    "origem": origem
                }).execute()
                registrar_movimentacao(
                    id_time=id_time,
                    jogador=jogador["nome"],
                    valor=round(jogador["valor"] * 0.7),
                    tipo="mercado",
                    categoria="venda",
                    destino="Mercado"
                )
                st.success(f"{jogador['nome']} foi vendido para o mercado.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao vender jogador: {e}")

    # ❌ Excluir direto (ADM)
    with col7:
        if is_admin and st.button("🗑️", key=f"del_{jogador['id']}"):
            try:
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
                st.success(f"{jogador['nome']} excluído do elenco.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")

st.markdown("---")
st.button("🔄 Atualizar", on_click=st.experimental_rerun)
