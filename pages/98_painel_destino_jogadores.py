# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Painel de Destino dos Jogadores", layout="wide")
st.title("🎯 Painel de Destino dos Jogadores")

# 🔎 Buscar todos jogadores da base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

if not jogadores:
    st.info("👭 Nenhum jogador encontrado na base.")
    st.stop()

# 📋 Converter para DataFrame
df = pd.DataFrame(jogadores)

# 🔍 Filtros
colf1, colf2, colf3 = st.columns(3)
with colf1:
    filtro_nome = st.text_input("🔍 Filtrar por nome:")
with colf2:
    posicoes = ["Todas"] + sorted(df["posicao"].dropna().unique())
    filtro_posicao = st.selectbox("📌 Filtrar por posição:", posicoes)
with colf3:
    nacs = ["Todas"] + sorted(df["nacionalidade"].dropna().unique())
    filtro_nac = st.selectbox("🌍 Filtrar por nacionalidade:", nacs)

# 🧐 Aplicar filtros
df_filtrado = df[df["nome"].str.lower().str.contains(filtro_nome.lower())]
if filtro_posicao != "Todas":
    df_filtrado = df_filtrado[df_filtrado["posicao"] == filtro_posicao]
if filtro_nac != "Todas":
    df_filtrado = df_filtrado[df_filtrado["nacionalidade"] == filtro_nac]

# 🔢 Contadores
total = len(df_filtrado)
disp = len(df_filtrado[df_filtrado["destino"] == "nenhum"])
merc = len(df_filtrado[df_filtrado["destino"] == "mercado"])
leil = len(df_filtrado[df_filtrado["destino"] == "leilao"])
atri = total - disp - merc - leil

st.markdown(f"""
<div style='background-color:#f8f9fa; padding:10px; border-radius:10px;'>
<b>📊 Totais:</b> {total} jogadores | 🔵 Disponíveis: {disp} | 📅 Mercado: {merc} | 🔨 Leilão: {leil} | 👥 Atribuídos: {atri}
</div>
""", unsafe_allow_html=True)

# 📂 Abas
aba = st.selectbox("🔹 Selecione a aba:", ["Todos", "Disponíveis", "Mercado", "Leilão", "Atribuídos"])

# 🌐 Filtro por aba
if aba == "Disponíveis":
    df_ordenado = df_filtrado[df_filtrado["destino"] == "nenhum"].sort_values(by="overall", ascending=False)
elif aba == "Mercado":
    df_ordenado = df_filtrado[df_filtrado["destino"] == "mercado"].sort_values(by="overall", ascending=False)
elif aba == "Leilão":
    df_ordenado = df_filtrado[df_filtrado["destino"] == "leilao"].sort_values(by="overall", ascending=False)
elif aba == "Atribuídos":
    df_ordenado = df_filtrado[~df_filtrado["destino"].isin(["nenhum", "mercado", "leilao"])]
else:
    df_ordenado = df_filtrado.sort_values(by="overall", ascending=False)

cores_destino = {
    "nenhum": "#e0f0ff",
    "mercado": "#fff3cd",
    "leilao": "#ffe5b4",
}

# 🔄 Renderizar
for row in df_ordenado.itertuples():
    destino = row.destino
    cor_fundo = cores_destino.get(destino, "#d4edda")

    with st.container():
        st.markdown(f"<div style='background-color:{cor_fundo}; padding:10px; border-radius:10px; margin-bottom:10px'>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1.2, 1.2])

        with col1:
            st.markdown(f"**{row.nome}**")
            st.caption(f"{row.posicao} | Overall: {row.overall} | R$ {row.valor:,.0f}".replace(",", "."))
            if getattr(row, "link_sofifa", ""):
                st.markdown(f"[\ud83d\udcc4 Ficha Técnica](https://sofifa.com{row.link_sofifa})", unsafe_allow_html=True)

        if aba == "Disponíveis":
            with col2:
                if st.button("\ud83d\udce4 Mercado", key=f"mercado_{row.id}"):
                    ja = supabase.table("mercado_transferencias").select("id").eq("id_jogador_base", row.id).execute()
                    if ja.data:
                        st.warning("⚠️ Já está no mercado.")
                    else:
                        supabase.table("mercado_transferencias").insert({
                            "id_jogador_base": row.id,
                            "nome": row.nome,
                            "posicao": row.posicao,
                            "overall": row.overall,
                            "valor": row.valor,
                            "imagem_url": row.imagem_url,
                            "nacionalidade": row.nacionalidade,
                            "clube_original": row.clube_original
                        }).execute()
                        supabase.table("jogadores_base").update({"destino": "mercado"}).eq("id", row.id).execute()
                        st.success(f"{row.nome} enviado ao mercado.")
                        st.experimental_rerun()
            with col3:
                if st.button("\ud83d\udd28 Leilão", key=f"leilao_{row.id}"):
                    ja = supabase.table("leiloes").select("id").eq("nome_jogador", row.nome).eq("finalizado", False).execute()
                    if ja.data:
                        st.warning("⚠️ Já está em leilão.")
                    else:
                        supabase.table("leiloes").insert({
                            "nome_jogador": row.nome,
                            "posicao_jogador": row.posicao,
                            "overall_jogador": row.overall,
                            "valor_inicial": row.valor,
                            "valor_atual": row.valor,
                            "incremento_minimo": 3000000,
                            "tempo_minutos": 2,
                            "ativo": False,
                            "finalizado": False,
                            "aguardando_validacao": False,
                            "validado": False,
                            "enviado_bid": False,
                            "origem": row.clube_original,
                            "nacionalidade": row.nacionalidade,
                            "imagem_url": row.imagem_url,
                            "link_sofifa": getattr(row, "link_sofifa", "")
                        }).execute()
                        supabase.table("jogadores_base").update({"destino": "leilao"}).eq("id", row.id).execute()
                        st.success(f"{row.nome} enviado ao leilão.")
                        st.experimental_rerun()
            with col4:
                with st.expander("⚽ Time"):
                    novo_destino = st.text_input(f"ID do time para {row.nome}", key=f"time_{row.id}")
                    if st.button("✅ Atribuir", key=f"atribuir_{row.id}"):
                        if novo_destino.strip():
                            supabase.table("jogadores_base").update({"destino": novo_destino}).eq("id", row.id).execute()
                            st.success(f"{row.nome} atribuido ao time: {novo_destino}")
                            st.experimental_rerun()

        with col5:
            if row.imagem_url:
                st.image(row.imagem_url, width=60)

        st.markdown("</div>", unsafe_allow_html=True)
