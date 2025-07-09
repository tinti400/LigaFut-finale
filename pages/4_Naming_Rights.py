# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao
import uuid

st.set_page_config(page_title="💼 Naming Rights - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão
verificar_sessao()

# 📌 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🧾 Verifica contrato ativo
res = supabase.table("naming_rights").select("*").eq("id_time", id_time).eq("ativo", True).execute()
contrato_ativo = res.data[0] if res.data else None

# 🏟️ Informações do estádio
res_estadio = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res_estadio.data[0] if res_estadio.data else None
nome_estadio = estadio["nome"] if estadio else f"Estádio {nome_time}"
nivel_atual = estadio.get("nivel", 1)

# 💰 Valores de evolução por nível
preco_por_nivel = {
    1: 370_000_000,
    2: 490_000_000,
    3: 610_000_000,
    4: 750_000_000,
    5: 0
}
preco_evolucao = preco_por_nivel.get(nivel_atual, 0)

# 🎯 Título
st.markdown(f"<h2 style='color:#0e1117;'>🏟️ Naming Rights do <span style='color:#4CAF50'>{nome_estadio}</span></h2>", unsafe_allow_html=True)

# ✅ Contrato já assinado
if contrato_ativo:
    st.success("📢 Você já possui um contrato ativo de naming rights.")
    with st.container():
        st.markdown(f"🔹 **Estádio nomeado:** `{contrato_ativo['nome_estadio_custom']}`")
        st.markdown(f"🔹 **Patrocinador:** `{contrato_ativo['nome_patrocinador']}`")
        st.markdown(f"📆 **Início:** `{contrato_ativo['data_inicio'][:10]}`")
        st.markdown(f"📆 **Fim:** `{contrato_ativo['data_fim'][:10]}`")
        st.markdown(f"💰 **Cobertura:** `{contrato_ativo['percentual_cobertura']}%`")
        if contrato_ativo.get("beneficio_extra"):
            st.markdown(f"🎁 **Benefício:** `{contrato_ativo['beneficio_extra']}`")
    st.stop()

# 📦 Lista de propostas
propostas = [
    {
        "marca": "NeoBank",
        "nome": "NeoBank Arena",
        "duracao_turnos": 3,
        "bonus_fixo": 25_000_000,
        "beneficio": "duracao_3_turnos",
        "descricao_beneficio": "Contrato mais longo (3 turnos) e recebe R$25 milhões extras ao assinar"
    },
    {
        "marca": "FastFuel",
        "nome": "FastFuel Stadium",
        "duracao_turnos": 2,
        "beneficio": "estacionamento",
        "descricao_beneficio": "R$5 extras por torcedor nos jogos como mandante (estacionamento)"
    },
    {
        "marca": "GoMobile",
        "nome": "GoMobile Park",
        "duracao_turnos": 2,
        "beneficio": "bonus_venda_atletas",
        "descricao_beneficio": "Recebe 5% a mais sempre que vender um jogador"
    },
    {
        "marca": "TechOne",
        "nome": "TechOne Field",
        "duracao_turnos": 2,
        "beneficio": "vip_gold",
        "descricao_beneficio": "Seu estádio ganha setor VIP, aumentando a renda geral"
    },
    {
        "marca": "SuperBet",
        "nome": "Arena SuperBet",
        "duracao_turnos": 2,
        "beneficio": "desconto_salarios",
        "descricao_beneficio": "Reduz em 10% o custo mensal dos salários do elenco"
    },
    {
        "marca": "PlayZone",
        "nome": "Estádio PlayZone",
        "duracao_turnos": 2,
        "beneficio": "renda_bonus",
        "descricao_beneficio": "Você ganha +10% em toda renda dos jogos como mandante"
    },
    {
        "marca": "Brahza",
        "nome": "Brahza Arena",
        "duracao_turnos": 2,
        "beneficio": "comida_bebida",
        "descricao_beneficio": "Lucro extra de 5% com vendas de bebidas e alimentos no estádio"
    },
    {
        "marca": "ZaraBank",
        "nome": "ZaraBank Stadium",
        "duracao_turnos": 2,
        "beneficio": "bonus_visitante",
        "descricao_beneficio": "Aumenta sua torcida em jogos como visitante em 12%"
    },
]

# 💼 Exibição das propostas
st.markdown("### 💼 <u>Escolha sua proposta de Naming Rights</u>", unsafe_allow_html=True)

cols = st.columns(2)
for i, prop in enumerate(propostas):
    with cols[i % 2]:
        with st.container():
            st.markdown(f"#### 🏢 {prop['nome']} ({prop['marca']})")
            st.markdown(f"🕒 **Duração:** `{prop['duracao_turnos']} turnos`")
            st.markdown(f"🎁 **Benefício:** `{prop['descricao_beneficio']}`")

            valor_total = preco_evolucao + prop.get("bonus_fixo", 0)
            st.markdown(f"💰 <span style='color:green;font-size:18px;'>Valor total a receber: R${valor_total:,.2f}</span>", unsafe_allow_html=True)

            if st.button(f"📄 Assinar contrato com {prop['marca']}", key=prop['marca']):
                agora = datetime.now()
                fim = agora + timedelta(weeks=prop["duracao_turnos"] * 5)

                id_contrato = str(uuid.uuid4())

                supabase.table("naming_rights").insert({
                    "id": id_contrato,
                    "id_time": id_time,
                    "nome_patrocinador": prop["marca"],
                    "nome_estadio_custom": prop["nome"],
                    "percentual_cobertura": 100,
                    "entrada_caixa": valor_total,
                    "data_inicio": agora.isoformat(),
                    "data_fim": fim.isoformat(),
                    "ativo": True,
                    "beneficio_extra": prop["beneficio"]
                }).execute()

                res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
                saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
                novo_saldo = saldo_atual + valor_total
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                registrar_movimentacao(
                    id_time=id_time,
                    tipo="entrada",
                    valor=valor_total,
                    descricao=f"Contrato naming rights com {prop['marca']}",
                    categoria="naming_rights"
                )

                st.success(f"✅ Contrato com {prop['marca']} assinado com sucesso!")
                st.rerun()
