# 27_Propostas_Recebidas_Patrocinio.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.set_page_config(page_title="📄 Propostas de Patrocínio", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.title("📄 Propostas de Patrocínio")
st.subheader(f"🟢 Time: {nome_time}")

# 🔍 Buscar propostas pendentes com info do patrocinador
res = supabase.table("propostas_patrocinio").select("*, patrocinadores(*)")\
    .eq("id_time", id_time).eq("status", "pendente").execute()
propostas = res.data

if not propostas:
    st.success("✅ Você já escolheu os patrocinadores para esta temporada.")
    st.stop()

# 🎯 Agrupar por tipo
tipos = ["master", "material", "secundario"]
for tipo in tipos:
    st.markdown(f"### 🏷️ Patrocínio **{tipo.upper()}**")
    propostas_tipo = [p for p in propostas if p["tipo"] == tipo]

    if not propostas_tipo:
        st.info("Nenhuma proposta disponível.")
        continue

    for proposta in propostas_tipo:
        pat = proposta["patrocinadores"]
        with st.container():
    st.markdown("---")  # linha divisória manual para dar separação visual
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(pat["logo_url"], width=80)
            with col2:
                st.markdown(f"**🏢 {pat['nome']}**")
                st.markdown(f"📦 Valor fixo: `R$ {proposta['valor_fixo']:,}`")
                st.markdown(f"🎯 Bônus por vitória: `R$ {proposta['bonus_vitoria']:,}`")
                st.markdown(f"📆 Validade até: `{proposta['validade'][:10]}`")

                if st.button(f"✅ Assinar com {pat['nome']}", key=f"{tipo}_{proposta['id']}"):
                    # ✅ Aceita esta
                    supabase.table("propostas_patrocinio").update({"status": "aceita"})\
                        .eq("id", proposta["id"]).execute()

                    # ❌ Recusa outras do mesmo tipo
                    outros_ids = [p["id"] for p in propostas_tipo if p["id"] != proposta["id"]]
                    if outros_ids:
                        supabase.table("propostas_patrocinio").update({"status": "recusada"})\
                            .in_("id", outros_ids).execute()

                    # 💼 Registrar patrocínio ativo
                    supabase.table("patrocinios_ativos").insert({
                        "id": str(uuid.uuid4()),
                        "id_time": id_time,
                        "id_patrocinador": proposta["id_patrocinador"],
                        "inicio": datetime.now().isoformat(),
                        "fim": proposta["validade"],
                        "valor_total": proposta["valor_fixo"]
                    }).execute()

                    # 💰 Atualizar saldo do time
                    saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
                    novo_saldo = saldo + proposta["valor_fixo"]
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    st.success(f"🎉 Patrocínio com {pat['nome']} assinado!")
                    st.experimental_rerun()
