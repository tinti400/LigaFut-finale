# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
import uuid

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", layout="wide")
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

# ✅ Validar UUID
def is_valid_uuid(u):
    try:
        uuid.UUID(u)
        return True
    except:
        return False

# ⚖️ Gerar confrontos
def gerar_confrontos(times, fase):
    random.shuffle(times)
    jogos = []
    for i in range(0, len(times), 2):
        if i + 1 < len(times):
            m_id = times[i]
            v_id = times[i + 1]
            if is_valid_uuid(m_id) and is_valid_uuid(v_id):
                jogos.append({
                    "id": str(uuid.uuid4()),
                    "fase": fase,
                    "numero": len(jogos) + 1,
                    "id_mandante": m_id,
                    "id_visitante": v_id,
                    "gols_mandante": None,
                    "gols_visitante": None
                })
            else:
                st.warning(f"🚫 Jogo ignorado: ID inválido → mandante='{m_id}', visitante='{v_id}'")
        else:
            st.warning(f"⚠️ Time sem adversário: {times[i]}")
    return jogos

# 🔄 Botão para iniciar copa
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    try:
        res_info = supabase.table("times").select("id", "nome", "logo").execute()
        times_map = {
            t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
            for t in res_info.data
            if t.get("nome") and is_valid_uuid(t["id"])
        }

        time_ids = []
        for tid, info in times_map.items():
            nome = info.get("nome", "").strip()
            if is_valid_uuid(tid) and nome != "":
                time_ids.append(tid)
            else:
                st.warning(f"🚫 Time ignorado: nome='{nome}', id='{tid}' (inválido)")

        st.write("📋 Times válidos para a Copa:", [times_map[tid]["nome"] for tid in time_ids])

        if len(time_ids) < 2:
            st.warning("⚠️ É preciso ao menos 2 times válidos para iniciar a copa.")
            st.stop()

        supabase.table("copa_ligafut").delete().neq("id", "").execute()
        fase = "Preliminar" if len(time_ids) > 16 else "Oitavas"
        jogos = gerar_confrontos(time_ids, fase)

        st.write("🧪 Jogos gerados:", jogos)

        supabase.table("copa_ligafut").insert({
            "numero": 1,
            "fase": fase,
            "jogos": jogos
        }).execute()
        st.success("✅ Primeira fase criada com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")
