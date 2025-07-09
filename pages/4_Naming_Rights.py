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

# 🔍 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

# 📄 Consulta naming rights ativos
res = supabase.table("naming_rights").select("*").eq("id_time", id_time).eq("ativo", True).execute()
contrato_ativo = res.data[0] if res.data else None

# 📄 Consulta estádio
res_estadio = supabase.table("estadios").select("nome").eq("id_time", id_time).execute()
nome_estadio = res_estadio.data[0]["nome"] if res_estadio.data else f"Estádio {nome_time}"

st.markdown(f"## 🏟️ Naming Rights do {nome_estadio}")

if contrato_ativo:
    st.success("📢 Você já possui um contrato ativo de naming rights.")
    st.markdown(f"**Estádio nomeado:** `{contrato_ativo['nome_estadio_custom']}`")
    st.markdown(f"**Patrocinador:** `{contrato_ativo['nome_patrocinador']}`")
    st.markdown(f"**Início:** `{contrato_ativo['data_inicio'][:10]}`")
    st.markdown(f"**Fim:** `{contrato_ativo['data_fim'][:10]}`")
    st.markdown(f"**Cobertura:** `{contrato_ativo['percentual_cobertura']}%`")
    if contrato_ativo.get("beneficio_extra"):
        st.markdown(f"**Benefício extra:** `{contrato_ativo['beneficio_extra']}`")
    if contrato_ativo.get("desconto_upgrade"):
        st.markdown(f"**Desconto evolução estádio:** `{contrato_ativo['desconto_upgrade']}%`")
    st.stop()

# 🏷️ Propostas disponíveis
propostas = [
    {"marca": "NeoBank", "cobertura": 85, "nome": "NeoBank Arena", "beneficio": "duracao_3_turnos", "descricao": "Contrato mais longo: 3 turnos", "duracao_turnos": 3, "desconto_upgrade": 0},
    {"marca": "FastFuel", "cobertura": 60, "nome": "FastFuel Stadium", "beneficio": "estacionamento", "descricao": "Gera +R$5 por torcedor (estacionamento)", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "GoMobile", "cobertura": 50, "nome": "GoMobile Park", "beneficio": "bonus_venda_atletas", "descricao": "+5% nas vendas de jogadores", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "TechOne", "cobertura": 40, "nome": "TechOne Field", "beneficio": "vip_gold", "descricao": "Adiciona setor VIP ao estádio", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "SuperBet", "cobertura": 30, "nome": "Arena SuperBet", "beneficio": "desconto_salarios", "descricao": "-10% no custo dos salários dos jogadores", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "PlayZone", "cobertura": 70, "nome": "Estádio PlayZone", "beneficio": "renda_bonus", "descricao": "+10% na renda total dos jogos", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "Brahza", "cobertura": 25, "nome": "Brahza Arena", "beneficio": "comida_bebida", "descricao": "+5% extra com vendas de bebidas/comidas", "duracao_turnos": 2, "desconto_upgrade": 0},
    {"marca": "ZaraBank", "cobertura": 90, "nome": "ZaraBank Stadium", "beneficio": "desconto_upgrade", "descricao": "-70% no custo da próxima evolução do estádio", "duracao_turnos": 2, "desconto_upgrade": 70},
]

st.markdown("### 📜 Propostas de Naming Rights Disponíveis")

for prop in propostas:
    with st.expander(f"{prop['nome']} - {prop['descricao']} ({prop['cobertura']}%)"):
        st.markdown(f"- 📢 Patrocinador: **{prop['marca']}**")
        st.markdown(f"- 📈 Cobertura: **{prop['cobertura']}%**")
        st.markdown(f"- 🧠 Benefício extra: **{prop['beneficio']}**")
        st.markdown(f"- ⏱️ Duração: **{prop['duracao_turnos']} turnos**")
        valor = int((prop["cobertura"] / 100) * 250_000_000)
        st.markdown(f"💰 Valor a receber: **R${valor:,.2f}**")
        if st.button(f"📄 Assinar contrato com {prop['marca']}", key=prop["marca"]):
            agora = datetime.now()
            fim = agora + timedelta(weeks=prop["duracao_turnos"] * 5)

            entrada_caixa = valor
            id_contrato = str(uuid.uuid4())

            # 💾 Salvar contrato
            supabase.table("naming_rights").insert({
                "id": id_contrato,
                "id_time": id_time,
                "nome_patrocinador": prop["marca"],
                "nome_estadio_custom": prop["nome"],
                "percentual_cobertura": prop["cobertura"],
                "entrada_caixa": entrada_caixa,
                "data_inicio": agora.isoformat(),
                "data_fim": fim.isoformat(),
                "ativo": True,
                "beneficio_extra": prop["beneficio"],
                "desconto_upgrade": prop.get("desconto_upgrade", 0)
            }).execute()

            # 💰 Atualizar saldo do time
            res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
            saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
            novo_saldo = saldo_atual + entrada_caixa
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

            # 💼 Registrar movimentação
            registrar_movimentacao(id_time, tipo="entrada", valor=entrada_caixa, descricao=f"Contrato naming rights com {prop['marca']}", categoria="naming_rights")

            st.success(f"✅ Contrato com {prop['marca']} assinado com sucesso!")
            st.rerun()

