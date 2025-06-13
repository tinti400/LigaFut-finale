# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao
import pandas as pd

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

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", st.session_state.get("usuario", "")).execute()
eh_admin = bool(res_admin.data)

st.title(f"👥 Elenco do {nome_time}")

# 💰 Buscar saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

# 📦 Buscar elenco do time
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

# 📤 Upload de Planilha (.xlsx)
with st.expander("📥 Importar jogadores via planilha (.xlsx)"):
    arquivo = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            for _, row in df.iterrows():
                jogador = {
                    "nome": row["nome"],
                    "posicao": row["posição"],
                    "overall": int(row["overall"]),
                    "valor": int(float(row["valor"])),
                    "nacionalidade": row.get("nacionalidade", "Desconhecida"),
                    "origem": row.get("origem", "Importado"),
                    "imagem_url": row.get("imagem_url", ""),
                    "id_time": id_time
                }
                supabase.table("elenco").insert(jogador).execute()
            st.success("✅ Jogadores importados com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

# 🧹 Limpar elenco (somente ADM)
if eh_admin and jogadores:
    if st.button("🧹 Limpar elenco COMPLETO"):
        try:
            supabase.table("elenco").delete().eq("id_time", id_time).execute()
            st.success("✅ Elenco limpo com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao limpar elenco: {e}")

if not jogadores:
    st.info("📃 Nenhum jogador encontrado no elenco.")
    st.stop()

# 🧮 Estatísticas
quantidade = len(jogadores)
valor_total = sum(j.get("valor", 0) for j in jogadores)

# 💬 Exibir informações
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

# 🧑‍💼 Exibir jogadores
for jogador in jogadores:
    col1, col2, col3, col4, col5, col6 = st.columns([1, 2.5, 1.5, 1.5, 2.5, 2])

    # Imagem do jogador (circular)
    with col1:
        imagem = jogador.get("imagem_url", "")
        if imagem:
            st.markdown(
                f"<img src='{imagem}' width='60' style='border-radius: 50%; border: 2px solid #ddd;'/>",
                unsafe_allow_html=True
            )
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
        valor_formatado = "R$ {:,.0f}".format(jogador.get("valor", 0)).replace(",", ".")
        origem = jogador.get("origem", "Desconhecida")
        st.markdown(f"💰 **{valor_formatado}**")
        st.markdown(f"🏟️ {origem}")

    with col6:
        if st.button(f"💸 Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
            try:
                # 🗑️ Remover do elenco
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                # 🛒 Inserir no mercado
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

                # 💰 Registrar movimentação
                registrar_movimentacao(
                    id_time=id_time,
                    jogador=jogador["nome"],
                    valor=round(jogador["valor"] * 0.7),
                    tipo="mercado",
                    categoria="venda",
                    destino="Mercado"
                )

                st.success(f"{jogador['nome']} foi vendido para o mercado com sucesso.")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Erro ao vender jogador: {e}")

st.markdown("---")
st.button("🔄 Atualizar", on_click=st.experimental_rerun)





