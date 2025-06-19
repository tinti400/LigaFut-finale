# (continuação do código anterior, a partir da visualização das rodadas)

# 📋 Estilização da tabela
def aplicar_estilo_linha(df):
    html = """
    <style>
        td, th { text-align: center; vertical-align: middle; }
        th { background-color: #f0f0f0; }
    </style>
    <table border='1' class='dataframe' style='width: 100%; border-collapse: collapse;'>
    """
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"

    total = len(df)
    for i, row in df.iterrows():
        cor = "#d4edda" if i < 4 else "#f8d7da" if i >= total - 2 else ""
        html += f"<tr style='background-color: {cor};'>" if cor else "<tr>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

if dados:
    df = pd.DataFrame(dados)
    st.markdown(aplicar_estilo_linha(df), unsafe_allow_html=True)
else:
    st.info("Sem dados suficientes para exibir a classificação.")

# 🔧 Admin: reset rodadas
if eh_admin:
    st.markdown("---")
    st.subheader("🔧 Ações administrativas")
    if st.button("🧹 Resetar Tabela de Classificação (apagar rodadas)"):
        try:
            res = supabase.table(nome_tabela_rodadas).select("id").execute()
            for doc in res.data:
                supabase.table(nome_tabela_rodadas).delete().eq("id", doc["id"]).execute()
            st.success("✅ Rodadas da divisão apagadas com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao resetar rodadas: {e}")

# 📅 Rodadas - visualização por página
st.markdown("---")
st.subheader("📅 Rodadas da Temporada")

if not rodadas:
    st.info("Nenhuma rodada encontrada para esta divisão.")
else:
    rodadas_ordenadas = sorted(rodadas, key=lambda r: r.get("numero", 0))
    lista_rodadas = [f"Rodada {r.get('numero', '?')}" for r in rodadas_ordenadas]
    selecao = st.selectbox("🔁 Selecione a rodada para visualizar", lista_rodadas)

    rodada_escolhida = rodadas_ordenadas[lista_rodadas.index(selecao)]
    st.markdown(f"### 🕹️ {selecao}")

    for jogo in rodada_escolhida.get("jogos", []):
        m = jogo.get("mandante")
        v = jogo.get("visitante")
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")

        m_info = times_map.get(m, {"nome": "?", "logo": "", "tecnico": ""})
        v_info = times_map.get(v, {"nome": "?", "logo": "", "tecnico": ""})

        escudo_m = f"<img src='{m_info['logo']}' width='25' style='vertical-align: middle; margin-right: 5px;'>"
        escudo_v = f"<img src='{v_info['logo']}' width='25' style='vertical-align: middle; margin-left: 5px;'>"

        nome_m = f"""
        <div style='display: inline-block; text-align: left;'>
            <b>{m_info['nome']}</b><br>
            <span style='font-size: 10px; color: gray;'>{m_info.get('tecnico', '')}</span>
        </div>
        """

        nome_v = f"""
        <div style='display: inline-block; text-align: right;'>
            <b>{v_info['nome']}</b><br>
            <span style='font-size: 10px; color: gray;'>{v_info.get('tecnico', '')}</span>
        </div>
        """

        placar = f"{gm} x {gv}" if gm is not None and gv is not None else "vs"

        st.markdown(f"<div style='font-size: 16px; display: flex; justify-content: space-between; align-items: center;'>"
                    f"{escudo_m}{nome_m}"
                    f"<div style='margin: 0 10px; font-weight: bold;'>{placar}</div>"
                    f"{nome_v}{escudo_v}"
                    f"</div>", unsafe_allow_html=True)

    st.markdown("---")

# 🏁 Checagem de fim de temporada e geração de histórico
def todos_os_jogos_preenchidos(rodadas):
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            if jogo.get("gols_mandante") is None or jogo.get("gols_visitante") is None:
                return False
    return True

if todos_os_jogos_preenchidos(rodadas):
    st.success("🏁 Temporada concluída! Gerando histórico...")

    campeao = classificacao[0][1]["nome"]
    melhor_ataque = max(classificacao, key=lambda x: x[1]["gp"])[1]["nome"]
    melhor_defesa = min(classificacao, key=lambda x: x[1]["gc"])[1]["nome"]

    temporada_data = {
        "data_fim": datetime.now().isoformat(),
        "divisao": divisao,
        "campeao": campeao,
        "melhor_ataque": melhor_ataque,
        "melhor_defesa": melhor_defesa
    }

    try:
        ja_salvo = supabase.table("historico_temporadas").select("*").eq("divisao", divisao).eq("data_fim", temporada_data["data_fim"]).execute()
        if not ja_salvo.data:
            supabase.table("historico_temporadas").insert(temporada_data).execute()
    except Exception as e:
        st.error(f"Erro ao salvar histórico da temporada: {e}")

    st.markdown("## 🏅 Resumo da Temporada")
    st.markdown(f"**🏆 Campeão:** `{campeao}`")
    st.markdown(f"**🔥 Melhor Ataque:** `{melhor_ataque}`")
    st.markdown(f"**🧱 Melhor Defesa:** `{melhor_defesa}`")
