# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao, registrar_bid

st.set_page_config(page_title="💼 Mercado de Transferências - LigaFut", layout="wide")

# ✅ Verifica sessão
if "usuario_id" not in st.session_state or "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🌟 Dados do usuário e time
usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

# ❌ Verifica restrição ao mercado
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
    restricoes = {}
    if res_restricoes.data and isinstance(res_restricoes.data[0], dict):
        restricoes = res_restricoes.data[0].get("restricoes", {})

    if restricoes.get("mercado", False):
        st.error("🚫 Seu time está proibido de acessar o Mercado de Transferências.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

# ✅ Verifica se o mercado está aberto
res_status = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = res_status.data[0]["mercado_aberto"] if res_status.data else False
if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento.")
    st.stop()

# 💰 Saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
saldo_time = res_saldo.data[0]["saldo"] if res_saldo.data else 0
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# 🔍 Filtros
st.markdown("### 🔍 Filtros de Pesquisa")
filtro_nome = st.text_input("Nome do jogador").strip().lower()
filtro_posicao = st.text_input("Posição").strip().lower()
filtro_nacionalidade = st.text_input("Nacionalidade").strip().lower()
filtro_ordenacao = st.selectbox("Ordenar por", ["Nenhum", "Maior Overall", "Menor Overall", "Nome A-Z", "Nome Z-A"])

# 🔃 Carregar jogadores disponíveis
res = supabase.table("mercado_transferencias").select("*").execute()
mercado = res.data if res.data else []

# 🔍 Aplicar filtros
jogadores_filtrados = [
    j for j in mercado
    if filtro_nome in j.get("nome", "").lower()
    and filtro_posicao in j.get("posicao", "").lower()
    and filtro_nacionalidade in str(j.get("nacionalidade", "")).lower()
]

# 🔢 Ordenação
if filtro_ordenacao == "Maior Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0), reverse=True)
elif filtro_ordenacao == "Menor Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0))
elif filtro_ordenacao == "Nome A-Z":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower())
elif filtro_ordenacao == "Nome Z-A":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower(), reverse=True)

# 📃 Paginação
jogadores_por_pagina = 15
total_jogadores = len(jogadores_filtrados)
total_paginas = (total_jogadores - 1) // jogadores_por_pagina + 1

if "pagina_mercado" not in st.session_state:
    st.session_state["pagina_mercado"] = 1

pagina_atual = st.session_state["pagina_mercado"]
inicio = (pagina_atual - 1) * jogadores_por_pagina
fim = inicio + jogadores_por_pagina
jogadores_pagina = jogadores_filtrados[inicio:fim]

# 🗉️ Elenco atual
res_elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
qtde_elenco = len(res_elenco.data) if res_elenco.data else 0

# 🗳️ Exibição dos jogadores
st.title("📈 Mercado de Transferências")
st.markdown(f"**Página {pagina_atual} de {total_paginas}**")

selecionados = set()

for jogador in jogadores_pagina:
    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
    with col1:
        st.image(jogador.get("foto") or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)

    with col2:
        st.markdown(f"**{jogador.get('nome')}**")
        st.markdown(f"📌 {jogador.get('posicao')} | ⭐ {jogador.get('overall')}")
        st.markdown(f"🌍 {jogador.get('nacionalidade', 'Não informada')}")

    with col3:
        st.markdown(f"💰 Valor: R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
        st.markdown(f"🏠 Origem: {jogador.get('time_origem', 'Desconhecido')}")

    with col4:
        if qtde_elenco >= 35:
            st.warning("⚠️ Elenco cheio (35 jogadores)")
        else:
            if st.button(f"Comprar {jogador['nome']}", key=jogador["id"]):
                check = supabase.table("mercado_transferencias").select("id").eq("id", jogador["id"]).execute()
                if not check.data:
                    st.error("❌ Este jogador já foi comprado.")
                    st.experimental_rerun()

                res_atual = supabase.table("times").select("saldo").eq("id", id_time).execute()
                saldo_atual = res_atual.data[0]["saldo"] if res_atual.data else 0

                if saldo_atual < jogador["valor"]:
                    st.error("❌ Saldo insuficiente.")
                else:
                    try:
                        valor = int(float(jogador["valor"]))
                        salario = int(float(jogador.get("salario", valor * 0.01)))

                        supabase.table("elenco").insert({
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": valor,
                            "salario": salario,
                            "id_time": id_time,
                            "nacionalidade": jogador.get("nacionalidade"),
                            "foto": jogador.get("foto"),
                            "origem": jogador.get("origem", jogador.get("time_origem", "Desconhecido"))
                        }).execute()

                        supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                        registrar_movimentacao(
                            id_time=id_time,
                            tipo="saida",
                            valor=valor,
                            descricao=f"Compra de {jogador['nome']} no mercado"
                        )

                        novo_saldo = saldo_atual - valor
                        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                        # 🔎 DEBUG do BID
                        registro_debug = {
                            "id_time": id_time,
                            "tipo": "compra",
                            "categoria": "mercado",
                            "jogador": jogador["nome"],
                            "valor": valor,
                            "origem": jogador.get("origem", jogador.get("time_origem", "Desconhecido")),
                            "destino": nome_time
                        }
                        st.markdown("### 🔎 DEBUG - Registro BID")
                        st.json(registro_debug)

                        registrar_bid(
                            id_time=id_time,
                            tipo="compra",
                            categoria="mercado",
                            jogador=jogador["nome"],
                            valor=valor,
                            origem=jogador.get("origem", jogador.get("time_origem", "Desconhecido")),
                            destino=nome_time
                        )

                        st.success(f"{jogador['nome']} comprado com sucesso!")
                        st.experimental_rerun()

                    except Exception as e:
                        st.error(f"Erro ao comprar jogador: {e}")

# 🚧 Admin - exclusão em massa
if is_admin:
    st.markdown("---")
    st.markdown("### 📅 Ações em massa (admin)")
    if selecionados:
        st.warning(f"{len(selecionados)} jogadores selecionados.")
        if st.button("🚮 Excluir selecionados do mercado"):
            try:
                for id_jogador in selecionados:
                    supabase.table("mercado_transferencias").delete().eq("id", id_jogador).execute()
                st.success("✅ Jogadores excluídos com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao excluir múltiplos jogadores: {e}")
    else:
        st.info("Selecione jogadores acima para habilitar a exclusão.")

# 🔀 Navegação
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅ Página anterior") and pagina_atual > 1:
        st.session_state["pagina_mercado"] -= 1
        st.experimental_rerun()
with col3:
    if st.button("➡ Próxima página") and pagina_atual < total_paginas:
        st.session_state["pagina_mercado"] += 1
        st.experimental_rerun()





