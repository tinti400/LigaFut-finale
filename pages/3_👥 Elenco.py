# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao, registrar_bid

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
salario_total = sum(int(j.get("valor", 0) * 0.007) for j in jogadores)

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

# 🎯 Filtro
classificacoes = ["Todos", "Titular", "Reserva", "Negociavel", "Sem classificação"]
classificacao_selecionada = st.selectbox("📌 Filtrar por classificação:", classificacoes)

if classificacao_selecionada == "Sem classificação":
    jogadores_filtrados = [j for j in jogadores if not j.get("classificacao")]
elif classificacao_selecionada == "Todos":
    jogadores_filtrados = jogadores
else:
    jogadores_filtrados = [j for j in jogadores if j.get("classificacao") == classificacao_selecionada.lower()]

# 📋 Exibição dos cards
cols = st.columns(4)
for idx, jogador in enumerate(jogadores_filtrados):
    with cols[idx % 4]:
        nome = jogador.get("nome", "Sem nome")
        posicao = jogador.get("posicao", "-")
        overall = jogador.get("overall", "-")
        valor = jogador.get("valor", 0)
        imagem = jogador.get("imagem_url") or ""
        jogos = jogador.get("jogos", 0)
        link_sofifa = jogador.get("link_sofifa", "")
        classificacao = (jogador.get("classificacao") or "Sem classificação").capitalize()
        nacionalidade = jogador.get("nacionalidade", "🌍")
        origem = jogador.get("origem", "Desconhecida")
        salario = int(valor * 0.007)

        if (
            not imagem.strip()
            or ".svg" in imagem
            or "player_0" in imagem
            or imagem.startswith("data:")
            or not imagem.startswith("http")
        ):
            imagem = "https://cdn-icons-png.flaticon.com/512/147/147144.png"

        st.markdown(f"""
        <div style="border-radius:15px; padding:10px; background:linear-gradient(145deg, #f0e6d2, #e2d6be); box-shadow: 2px 2px 6px rgba(0,0,0,0.1); text-align:center; font-family:Arial; margin-bottom:20px;">
            <div style="font-size:26px; font-weight:bold;">{overall}</div>
            <div style="font-size:13px; margin-top:-4px;">{posicao}</div>
            <div style="font-size:20px; margin:6px 0;"><strong>{nome}</strong></div>
            <img src="{imagem}" style="width:80px;height:80px;border-radius:8px;border:1px solid #999;"><br>
            <div style="font-size:14px;margin-top:10px;">
                🌍 {nacionalidade}<br>
                🏠 {origem}<br>
                💰 <strong>R$ {valor:,.0f}</strong><br>
                💳 Salário: R$ {salario:,.0f}<br>
                🏷️ {classificacao}<br>
                🎯 Jogos: <strong>{jogos}</strong><br>
        """.replace(",", "."), unsafe_allow_html=True)

        if link_sofifa:
            st.markdown(f'<a href="{link_sofifa}" target="_blank">🔗 Ver no SoFIFA</a>', unsafe_allow_html=True)

        nova_classificacao = st.selectbox(
            "Classificação", ["Titular", "Reserva", "Negociavel", "Sem classificação"],
            index=["Titular", "Reserva", "Negociavel", "Sem classificação"].index(classificacao),
            key=f"class_{jogador['id']}"
        )
        if nova_classificacao.lower() != jogador.get("classificacao", ""):
            supabase.table("elenco").update({"classificacao": nova_classificacao.lower()}).eq("id", jogador["id"]).execute()
            st.experimental_rerun()

        if st.button(f"💸 Vender", key=f"vender_{jogador['id']}"):
            if jogos < 3:
                st.warning(f"❌ {nome} ainda não pode ser vendido. É necessário completar 3 jogos.")
            else:
                try:
                    valor_venda = round(valor * 0.7)

                    # 🟢 Verifica bônus extra do naming rights
                    res_bonus = supabase.table("naming_rights").select("beneficio_extra").eq("id_time", id_time).eq("ativo", True).execute()
                    beneficio = res_bonus.data[0]["beneficio_extra"] if res_bonus.data else None
                    if beneficio == "bonus_venda_atletas":
                        valor_venda = round(valor_venda * 1.05)

                    res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
                    saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
                    novo_saldo = saldo_atual + valor_venda
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                    supabase.table("mercado_transferencias").insert({
                        "nome": nome,
                        "posicao": posicao,
                        "overall": overall,
                        "valor": valor,
                        "id_time": id_time,
                        "time_origem": nome_time,
                        "imagem_url": imagem,
                        "nacionalidade": nacionalidade,
                        "origem": origem,
                        "classificacao": nova_classificacao.lower(),
                        "salario": salario,
                        "link_sofifa": link_sofifa
                    }).execute()

                    registrar_movimentacao(
                        id_time=id_time,
                        tipo="entrada",
                        valor=valor_venda,
                        descricao=f"Venda de {nome} para o mercado",
                        jogador=nome,
                        categoria="venda",
                        origem="elenco",
                        destino="mercado"
                    )

                    registrar_bid(
                        id_time=id_time,
                        tipo="venda",
                        categoria="mercado",
                        jogador=nome,
                        valor=valor_venda,
                        origem=nome_time
                    )

                    st.success(f"{nome} foi vendido com sucesso!")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Erro ao vender jogador: {e}")

        if is_admin and st.button(f"🗑️ Excluir", key=f"excluir_{jogador['id']}"):
            try:
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
                st.success(f"✅ {nome} foi excluído do elenco com sucesso!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao excluir jogador: {e}")

        st.markdown("</div>", unsafe_allow_html=True)
