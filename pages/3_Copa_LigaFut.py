# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
import uuid
import re

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🏆 Copa LigaFut - Mata-mata")

# 🔐 Login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("Apenas administradores podem acessar esta página.")
    st.stop()

# 🧰 Validador de UUID
def is_valid_uuid(u):
    try:
        uuid.UUID(u)
        return True
    except:
        return False

# 📊 Buscar times válidos da tabela "times"
res_info = supabase.table("times").select("id", "nome", "logo").execute()
times_map = {
    t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
    for t in res_info.data
    if t.get("nome") and is_valid_uuid(t["id"])
}
time_ids = list(times_map.keys())

# ⚖️ Gerar confrontos de forma segura
def gerar_confrontos(times, fase):
    random.shuffle(times)
    jogos = []
    for i in range(0, len(times), 2):
        if i + 1 < len(times):
            jogos.append({
                "id": str(uuid.uuid4()),
                "fase": fase,
                "numero": len(jogos) + 1,
                "id_mandante": times[i],
                "id_visitante": times[i + 1],
                "gols_mandante": None,
                "gols_visitante": None
            })
        else:
            nome = times_map.get(times[i], {}).get("nome", times[i])
            st.warning(f"⚠️ O time **{nome}** ficou sem adversário e foi ignorado.")
    return jogos

# 🔄 Gera nova copa
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    if len(time_ids) < 2:
        st.warning("⚠️ É preciso ao menos 2 times para iniciar a copa.")
        st.stop()
    try:
        supabase.table("copa_ligafut").delete().neq("id", "").execute()
        fase = "Preliminar" if len(time_ids) > 16 else "Oitavas"
        jogos = gerar_confrontos(time_ids, fase)
        for j in jogos:
            supabase.table("copa_ligafut").insert(j).execute()
        st.success("✅ Primeira fase criada com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 📅 Exibir jogos
st.markdown("---")
st.subheader("🕛 Jogos da Copa")

try:
    res_jogos = supabase.table("copa_ligafut").select("*").order("numero").execute()
    jogos = res_jogos.data

    if not jogos:
        st.info("Nenhum jogo cadastrado. Gere a copa para começar.")
    else:
        fases_ordem = ["Preliminar", "Oitavas", "Quartas", "Semifinal", "Final"]
        fases = sorted(set(j["fase"] for j in jogos), key=lambda x: fases_ordem.index(x))

        for fase in fases:
            st.markdown(f"### 🌟 {fase}")
            jogos_fase = [j for j in jogos if j["fase"] == fase]

            for j in jogos_fase:
                m_id = j.get("id_mandante")
                v_id = j.get("id_visitante")
                m_nome = times_map.get(m_id, {}).get("nome", m_id)
                v_nome = times_map.get(v_id, {}).get("nome", v_id)

                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                with col1:
                    st.markdown(f"**{m_nome}**")
                with col2:
                    gm = st.number_input("", key=f"gm_{j['id']}", min_value=0, value=j.get("gols_mandante") or 0)
                with col3:
                    st.markdown("**x**")
                with col4:
                    gv = st.number_input("", key=f"gv_{j['id']}", min_value=0, value=j.get("gols_visitante") or 0)
                with col5:
                    st.markdown(f"**{v_nome}**")

                if st.button("Salvar", key=f"btn_{j['id']}"):
                    try:
                        supabase.table("copa_ligafut").update({
                            "gols_mandante": gm,
                            "gols_visitante": gv
                        }).eq("id", j["id"]).execute()
                        st.success("Resultado salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
except Exception as e:
    st.error(f"Erro ao carregar jogos: {e}")
