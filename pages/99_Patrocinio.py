# 26_Gerar_Propostas_Patrocinio.py
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import random

st.set_page_config(page_title="📢 Gerar Propostas de Patrocínio", layout="centered")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("📢 Gerar Propostas de Patrocínio para os Times")

if st.button("🚀 Gerar 9 propostas por time"):
    try:
        # 🎯 Buscar todos os times e suas divisões
        res_times = supabase.table("times").select("id, nome, divisao").execute()
        times = res_times.data

        # 🎯 Buscar todos os patrocinadores cadastrados
        res_pats = supabase.table("patrocinadores").select("*").execute()
        patrocinadores = res_pats.data

        if not patrocinadores:
            st.error("❌ Nenhum patrocinador encontrado.")
            st.stop()

        total_geradas = 0

        for time in times:
            id_time = time["id"]
            nome_time = time["nome"]
            divisao = str(time.get("divisao", "1"))

            # 🧮 Multiplicador por divisão
            multiplicador = {
                "1": 1.0,
                "2": 0.75,
                "3": 0.5
            }.get(divisao, 1.0)

            # 🔁 Para cada tipo de patrocínio
            for tipo in ["master", "material", "secundario"]:
                pats_do_tipo = [p for p in patrocinadores if p["tipo"] == tipo]

                if len(pats_do_tipo) < 3:
                    st.warning(f"⚠️ Menos de 3 patrocinadores do tipo '{tipo}' disponíveis.")
                    continue

                sorteados = random.sample(pats_do_tipo, 3)

                for pat in sorteados:
                    proposta = {
                        "id": str(uuid.uuid4()),
                        "id_time": id_time,
                        "id_patrocinador": pat["id"],
                        "tipo": tipo,
                        "valor_fixo": int(pat["valor_fixo"] * multiplicador),
                        "bonus_vitoria": int(pat["bonus_vitoria"] * multiplicador),
                        "validade": datetime(2025, 12, 31).isoformat(),
                        "status": "pendente",
                        "data_envio": datetime.now().isoformat()
                    }
                    supabase.table("propostas_patrocinio").insert(proposta).execute()
                    total_geradas += 1

        st.success(f"✅ {total_geradas} propostas geradas com sucesso para {len(times)} times!")

    except Exception as e:
        st.error(f"❌ Erro ao gerar propostas: {e}")
