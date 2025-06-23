# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="👥 Elenco - LigaFut", layout="wide")

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

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

# 🧾 Título e separador
st.markdown(f"""
    <h1 style='text-align:center;'>👥 Elenco do {nome_time}</h1>
    <hr style='border:1px solid #444;'>
""", unsafe_allow_html=True)

# 💰 Saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

# 📦 Buscar elenco
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

# 📊 Estatísticas
quantidade = len(jogadores)
valor_total = sum(j.get("valor", 0) for j in jogadores)
salario_total = sum(
    int(j.get("salario")) if j.get("salario") is not None else int(float(j.get("valor", 0)) * 0.01)
    for j in jogadores
)

st.markdown(
    f"""
    <div style='text-align:center;'>
        <h3 style='color:green;'>💰 Saldo em caixa: <strong>R$ {saldo:,.0f}</strong></h3>
        <h4>👥 Jogadores no elenco: <strong>{quantidade}</strong> | 📈 Valor total: <strong>R$ {valor_total:,.0f}</strong> | 💵 Salário total: <strong style="color:#28a745;">R$ {salario_total:,.0f}</strong></h4>
    </div>
    <hr>
    """.replace(",", "."),
    unsafe_allow_html=True
)

# 🎯 Filtro de classificação
classificacoes = ["Todos", "Titular", "Reserva", "Negociavel", "Sem classificação"]
classificacao_selecionada = st.selectbox("📌 Filtrar por classificação:", classificacoes)

if classificacao_selecionada == "Sem classificação":
    jogadores_filtrados = [j for j in jogadores if not j.get("classificacao")]
elif classificacao_selecionada == "Todos":
    jogadores_filtrados = jogadores
else:
    jogadores_filtrados = [j for j in jogadores if j.get("classificacao") == classificacao_selecionada.lower()]

# 📋 Listagem
for jogador in jogadores_filtrados:
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 2.5, 1.5, 1.2, 1.2, 2.5, 2])

    with col1:
        imagem = jogador.get("imagem_url", "")
        if imagem:
            st.markdown(f"<img src='{imagem}' width='60' style='border-radius: 8px; border: 1px solid #ccc;'>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='width:60px;height:60px;border-radius:8px;border:1px solid #ccc;background:#eee;'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"**{jogador.get('nome', 'Sem nome')}**")
        st.markdown(f"🌍 {jogador.get('nacionalidade', 'Desconhecida')}")

    with col3:
        st.markdown(f"📌 {jogador.get('posicao', '-')}")

    with col4:
        st.markdown(f"⭐ {jogador.get('overall', '-')}")

    with col5:
        classificacao_atual = jogador.get("classificacao", "Sem classificação")
        nova_classificacao = st.selectbox(
            "",
            ["Titular", "Reserva", "Negociavel", "Sem classificação"],
            index=["Titular", "Reserva", "Negociavel", "Sem classificação"].index(
                classificacao_atual.capitalize() if classificacao_atual else "Sem classificação"
            ),
            key=f"class_{jogador['id']}"
        )
        if nova_classificacao.lower() != classificacao_atual:
            supabase.table("elenco").update({"classificacao": nova_classificacao.lower()}).eq("id", jogador["id"]).execute()
            st.experimental_rerun()

    with col6:
        valor = jogador.get("valor", 0)
        salario_jogador = int(jogador.get("salario")) if jogador.get("salario") is not None else int(valor * 0.01)
        origem = jogador.get("origem", "Desconhecida")
        st.markdown(
            f"""
            <div style='line-height:1.4'>
                💰 <strong>R$ {valor:,.0f}</strong><br>
                🏠 {origem}<br>
                💳 <span style='color:#28a745;'>Salário: R$ {salario_jogador:,.0f}</span>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True
        )

    with col7:
        if st.button(f"💸 Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
            try:
                # 🔢 Cálculo do valor da venda
                valor_venda = round(jogador["valor"] * 0.7)

                # 💰 Atualiza saldo do time
                res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
                saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
                novo_saldo = saldo_atual + valor_venda
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                # ❌ Remove do elenco
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                # 📥 Insere no mercado de transferências
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time,
                    "time_origem": nome_time,
                    "imagem_url": jogador.get("imagem_url", ""),
                    "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                    "origem": jogador.get("origem", "Desconhecida"),
                    "classificacao": jogador.get("classificacao", ""),
                    "salario": jogador.get("salario") if jogador.get("salario") is not None else int(jogador.get("valor", 0) * 0.01)
                }).execute()

                # 🧾 Registra movimentação financeira
                registrar_movimentacao(
                    id_time=id_time,
                    tipo="entrada",
                    valor=valor_venda,
                    descricao=f"Venda de {jogador['nome']} para o mercado"
                )

                st.success(f"{jogador['nome']} foi vendido com sucesso!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Erro ao vender jogador: {e}")
