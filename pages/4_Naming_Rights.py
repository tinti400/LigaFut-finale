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
res_estadio = supabase.table("estadios").select("nome", "nivel").eq("id_time", id_time).execute()
estadio_data = res_estadio.data[0] if res_estadio.data else None
nome_estadio = estadio_data["nome"] if estadio_data else f"Estádio {nome_time}"
nivel_atual = estadio_data["nivel"] if estadio_data else 1

# 💰 Tabela de valores por nível
valor_por_nivel = {
    1: 250_000_000,
    2: 350_000_000,
    3: 450_000_000,
    4: 550_000_000
}
valor_evolucao = valor_por_nivel.get(nivel_atual, 0)

st.markdown(f"## 🏟️ Naming Rights do {nome_estadio}")

if contrato_ativo:
    st.success("📢 Você já possui um contrato ativo de naming rights.")
    st.markdown(f"**Estádio nomeado:** `{contrato_ativo['nome_estadio_custom']}`")
    st.markdown(f"**Patrocinador:** `{contrato_ativo['nome_patrocinador']}`")
    st.markdown(f"**Início:** `{contrato_ativo['data_inicio'][:10]}`")
    st.markdown(f"**Fim:** `{contrato_ativo['data_fim'][:10]}`")
    st.markdown(f"**Valor pago:** `R${contrato_ativo['entrada_caixa']:,}`".replace(",", "."))
    st.markdown(f"**Benefício extra:** `{contrato_ativo['beneficio_extra']}`")
    st.stop()

# 🏷️ Propostas disponíveis (valor será definido dinamicamente)
beneficios = [
    {"marca": "NeoBank", "nome": "NeoBank Arena", "beneficio": "duracao_3_turnos", "descricao": "Contrato mais longo: 3 turnos", "duracao_turnos": 3},
    {"marca": "FastFuel", "nome": "FastFuel Stadium", "beneficio": "estacionamento", "descricao": "Gera +R$5 por torcedor (estacionamento)", "duracao_turnos": 2},
    {"marca": "GoMobile", "nome": "GoMobile Park", "beneficio": "bonus_venda_atletas", "descricao": "+5% nas vendas de jogadores", "duracao_turnos": 2},
    {"marca": "TechOne", "nome": "TechOne Field", "beneficio": "vip_gold", "descricao": "Adiciona setor VIP ao estádio", "duracao_turnos": 2},
    {"marca": "SuperBet", "nome": "Arena SuperBet", "beneficio": "desconto_salarios", "descricao": "-10% no custo dos salários dos jogadores", "duracao_turnos": 2},
    {"marca": "PlayZone", "nome": "Estádio PlayZone", "beneficio": "renda_bonus", "descricao": "+10% na renda total dos jogos", "duracao_turnos": 2},
    {"marca": "Brahza", "nome": "Brahza Arena", "beneficio": "comida_bebida", "descricao": "+5% extra com vendas de bebidas/comidas", "duracao_turnos": 2},
]

st.markdown("### 📜 Propostas de Naming Rights Disponíveis")

for prop in beneficios:
    with st.expander(f"{prop['nome']} - {prop['descricao']}"):
        st.markdown(f"- 📢 Patrocinador: **{prop['marca']}**")
        st.markdown(f"- 🧠 Benefício extra: **{prop['beneficio']}**")
        st.markdown(f"- ⏱️ Duração: **{prop['duracao_turnos']} turnos**")
        st.markdown(f"💰 Valor a receber: **R${valor_evolucao:,.0f}**".replace(",", "."))
        if st.button(f"📄 Assinar contrato com {prop['marca']}", key=prop["marca"]):
            agora = datetime.now()
            fim = agora + timedelta(weeks=prop["duracao_turnos"] * 5)

            entrada_caixa = valor_evolucao
            id_contrato = str(uuid.uuid4())

            # 💾 Salvar contrato
            supabase.table("naming_rights").insert({
                "id": id_contrato,
                "id_time": id_time,
                "nome_patrocinador": prop["marca"],
                "nome_estadio_custom": prop["nome"],
                "percentual_cobertura": 100,
                "entrada_caixa": entrada_caixa,
                "data_inicio": agora.isoformat(),
                "data_fim": fim.isoformat(),
                "ativo": True,
                "beneficio_extra": prop["beneficio"],
                "desconto_upgrade": 0
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
