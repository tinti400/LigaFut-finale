# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="🏷️ Naming Rights - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_sessao()

if "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.warning("Você precisa estar logado com um time válido para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("🏷️ Propostas de Naming Rights do Estádio")

# 🔎 Verifica contrato ativo
res_nr = supabase.table("naming_rights").select("*").eq("id_time", id_time).eq("ativo", True).execute()
contrato_ativo = res_nr.data[0] if res_nr.data else None

if contrato_ativo:
    st.success(f"✅ Contrato ativo com **{contrato_ativo['nome_patrocinador']}** até **{contrato_ativo['data_fim'][:10]}**")
    st.markdown(f"🏟️ Estádio renomeado como: **{contrato_ativo['nome_estadio_custom']}**")
    st.warning("❌ Você só pode ter 1 contrato ativo por vez.")
    st.stop()

# 🔄 Buscar nível do estádio
res_estadio = supabase.table("estadios").select("*").eq("id_time", id_time).execute()
estadio = res_estadio.data[0] if res_estadio.data else None
if not estadio:
    st.error("Estádio não encontrado.")
    st.stop()

nivel_atual = estadio.get("nivel", 1)
custo_upgrade = 250_000_000 + (nivel_atual * 120_000_000)

# 🧾 Propostas configuradas
propostas = [
    {
        "marca": "NeoBank", "cobertura": 85, "nome": "NeoBank Arena",
        "beneficio": "duracao_3_turnos", "descricao": "Contrato mais longo: 3 turnos (sem novo contrato nesse período)", "duracao_turnos": 3
    },
    {
        "marca": "FastFuel", "cobertura": 60, "nome": "FastFuel Stadium",
        "beneficio": "estacionamento", "descricao": "Gera +R$5 por torcedor em jogos em casa (estacionamento)", "duracao_turnos": 2
    },
    {
        "marca": "GoMobile", "cobertura": 50, "nome": "GoMobile Park",
        "beneficio": "bonus_venda_atletas", "descricao": "+5% de lucro em vendas de jogadores durante o contrato", "duracao_turnos": 2
    },
    {
        "marca": "TechOne", "cobertura": 40, "nome": "TechOne Field",
        "beneficio": "vip_gold", "descricao": "Adiciona setor VIP no estádio com ingresso mais caro", "duracao_turnos": 2
    },
    {
        "marca": "SuperBet", "cobertura": 30, "nome": "Arena SuperBet",
        "beneficio": "mais_publico", "descricao": "+10% no público estimado em jogos em casa", "duracao_turnos": 2
    },
    {
        "marca": "PlayZone", "cobertura": 70, "nome": "Estádio PlayZone",
        "beneficio": "renda_bonus", "descricao": "+10% na renda total de cada jogo em casa", "duracao_turnos": 2
    },
    {
        "marca": "Brahza", "cobertura": 25, "nome": "Brahza Arena",
        "beneficio": "comida_bebida", "descricao": "+5% de renda extra com vendas de bebidas/comidas", "duracao_turnos": 2
    },
    {
        "marca": "ZaraBank", "cobertura": 90, "nome": "ZaraBank Stadium",
        "beneficio": "desconto_salarios", "descricao": "-7% no custo dos salários dos jogadores", "duracao_turnos": 2
    },
]

# 🎯 Interface com propostas
st.markdown("## 💼 Escolha sua proposta:")

for i, prop in enumerate(propostas):
    cobertura_valor = int(custo_upgrade * (prop["cobertura"] / 100))
    entrada_caixa = custo_upgrade - cobertura_valor

    with st.expander(f"{prop['marca']} - {prop['cobertura']}% cobertura | Entrada: R$ {entrada_caixa:,.0f}"):
        st.markdown(f"🏟️ Estádio será renomeado para: **{prop['nome']}**")
        st.markdown(f"📅 Duração: **{prop['duracao_turnos']} turnos**")
        st.markdown(f"🎁 Benefício exclusivo: **{prop['descricao']}**")
        if st.button(f"🤝 Fechar com {prop['marca']}", key=f"contrato_{i}"):
            try:
                agora = datetime.now()
                fim = (agora + timedelta(weeks=prop["duracao_turnos"] * 9)).isoformat()

                # Atualiza saldo com entrada
                res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
                saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
                novo_saldo = saldo_atual + entrada_caixa
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                # Salva contrato
                supabase.table("naming_rights").insert({
                    "id_time": id_time,
                    "nome_patrocinador": prop["marca"],
                    "nome_estadio_custom": prop["nome"],
                    "percentual_cobertura": prop["cobertura"],
                    "entrada_caixa": entrada_caixa,
                    "data_inicio": agora.isoformat(),
                    "data_fim": fim,
                    "ativo": True,
                    "beneficio_extra": prop["beneficio"]
                }).execute()

                # Atualiza nome do estádio
                supabase.table("estadios").update({"nome": prop["nome"]}).eq("id_time", id_time).execute()

                # Movimentação financeira
                registrar_movimentacao(id_time, "entrada", entrada_caixa, f"Contrato Naming Rights - {prop['marca']}")

                st.success("🎉 Contrato fechado com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao fechar contrato: {e}")
