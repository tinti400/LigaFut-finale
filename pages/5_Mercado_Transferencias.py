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
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
    if restricoes.get("mercado", False):
        st.error("🚫 Seu time está proibido de acessar o Mercado de Transferências.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

# ✅ Verifica se o mercado está aberto
res_status = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = res_status.data[0]["mercado_aberto"] if res_status.data else False
if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento. As compras estão temporariamente indisponíveis.")

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
res_elenco = supabase.table("elenco").select("id", "nome", "posicao").eq("id_time", id_time).execute()
elenco_atual = res_elenco.data if res_elenco.data else []
qtde_elenco = len(elenco_atual)

# 📦 Lista de jogadores selecionados (somente admins)
selecionados = set()

st.title("📈 Mercado de Transferências")
st.markdown(f"**Página {pagina_atual} de {total_paginas}**")

for jogador in jogadores_pagina:
    col1, col2, col3, col4, col5 = st.columns([0.3, 1.8, 2, 2, 2])
    if is_admin:
        selecionado = col1.checkbox("", key=f"check_{jogador['id']}")
        if selecionado:
            selecionados.add(jogador["id"])
    else:
        col1.markdown("")

    with col2:
        st.image(jogador.get("foto") or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)

    with col3:
        st.markdown(f"**{jogador.get('nome')}**")
        st.markdown(f"📌 {jogador.get('posicao')} | ⭐ {jogador.get('overall')}")
        st.markdown(f"🌍 {jogador.get('nacionalidade', 'Não informada')}")

        # 📄 Link SoFIFA
        link_sofifa = jogador.get("link_sofifa", "")
        if link_sofifa:
            st.markdown(f"<a href='{link_sofifa}' target='_blank'>📄 Ficha Técnica</a>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"💰 Valor: R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
        st.markdown(f"🏠 Origem: {jogador.get('time_origem', 'Desconhecido')}")
        if is_admin:
            novo_valor = st.number_input(f"Editar valor de {jogador['nome']}", min_value=1, step=1,
                                         value=int(jogador["valor"]), key=f"val_{jogador['id']}")
            if st.button(f"💾 Salvar valor", key=f"edit_{jogador['id']}"):
                try:
                    supabase.table("mercado_transferencias").update({"valor": novo_valor}).eq("id", jogador["id"]).execute()
                    st.success(f"Valor de {jogador['nome']} atualizado com sucesso!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar valor: {e}")

    with col5:
        if qtde_elenco >= 35:
            st.warning("⚠️ Elenco cheio (35 jogadores)")
        elif not mercado_aberto:
            st.info("⛔ Mercado fechado")
        else:
            if st.button(f"Comprar {jogador['nome']}", key=jogador["id"]):
                try:
                    saldo_atual = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                    if saldo_atual < jogador.get("valor", 0):
                        st.error("❌ Saldo insuficiente.")
                        st.stop()

                    for j in elenco_atual:
                        if j["nome"].lower() == jogador["nome"].lower() and j["posicao"] == jogador["posicao"]:
                            st.error(f"❌ {jogador['nome']} já está no seu elenco.")
                            st.stop()

                    res_delete = supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()
                    if not res_delete.data:
                        st.error("❌ Este jogador já foi comprado por outro time.")
                        st.experimental_rerun()

                    valor = int(jogador.get("valor", 0))
                    salario_raw = jogador.get("salario")
                    salario = int(salario_raw) if salario_raw else int(valor * 0.01)

                    supabase.table("elenco").insert({
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": valor,
                        "salario": salario,
                        "id_time": id_time,
                        "nacionalidade": jogador.get("nacionalidade"),
                        "foto": jogador.get("foto"),
                        "origem": jogador.get("origem", jogador.get("time_origem", "Desconhecido")),
                        "link_sofifa": jogador.get("link_sofifa", "")
                    }).execute()

                    registrar_movimentacao(id_time, "saida", valor, f"Compra de {jogador['nome']} no mercado")
                    supabase.table("times").update({"saldo": saldo_atual - valor}).eq("id", id_time).execute()

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

# 🧹 Excluir múltiplos jogadores (admin)
if is_admin and selecionados:
    st.markdown("---")
    st.warning(f"{len(selecionados)} jogador(es) selecionado(s).")
    if st.button("🚮 Excluir todos os selecionados do mercado"):
        try:
            for jogador_id in selecionados:
                supabase.table("mercado_transferencias").delete().eq("id", jogador_id).execute()
            st.success("✅ Jogadores excluídos com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao excluir jogadores: {e}")

# 🧼 Exclusão por intervalo de overall (admin)
if is_admin:
    st.markdown("---")
    st.subheader("🧼 Exclusão por Overall")
    col_min, col_max = st.columns(2)
    with col_min:
        overall_min = st.number_input("⭐ Overall mínimo", min_value=0, max_value=99, value=0)
    with col_max:
        overall_max = st.number_input("⭐ Overall máximo", min_value=0, max_value=99, value=99)

    if st.button("🚮 Excluir todos nesse intervalo"):
        try:
            jogadores_para_excluir = [
                j for j in mercado
                if overall_min <= j.get("overall", 0) <= overall_max
            ]
            if not jogadores_para_excluir:
                st.info("🔍 Nenhum jogador encontrado nesse intervalo.")
            else:
                for jogador in jogadores_para_excluir:
                    supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()
                st.success(f"✅ {len(jogadores_para_excluir)} jogador(es) excluído(s).")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao excluir jogadores por overall: {e}")

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
