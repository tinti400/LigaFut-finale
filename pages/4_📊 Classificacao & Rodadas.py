## 📊 Tabela de classificação
if classificacao:
    df = pd.DataFrame([{
        "Posição": i + 1,
        "Time": f"<img src='{t['logo']}' width='25'> <b>{t['nome']}</b><br><small>{t['tecnico']}</small>",
        "Pontos": t["pontos"],
        "Jogos": t["v"] + t["e"] + t["d"],
        "Vitórias": t["v"],
        "Empates": t["e"],
        "Derrotas": t["d"],
        "Gols Pró": t["gp"],
        "Gols Contra": t["gc"],
        "Saldo de Gols": t["sg"]
    } for i, (tid, t) in enumerate(classificacao)])

    def aplicar_estilo(df):
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<thead><tr>" + ''.join(f"<th>{col}</th>" for col in df.columns) + "</tr></thead><tbody>"
        for i, row in df.iterrows():
            cor = "#d4edda" if i < 4 else "#f8d7da" if i >= len(df) - 2 else "white"
            linha = "<tr style='background-color: {};'>".format(cor)
            linha += ''.join(f"<td>{val}</td>" for val in row)
            linha += "</tr>"
            html += linha
        html += "</tbody></table>"
        return html

    st.markdown(aplicar_estilo(df), unsafe_allow_html=True)
else:
    st.info("Nenhum dado de classificação disponível.")

# 📅 Filtro de rodada
st.markdown("---")
st.subheader("📅 Rodadas da Temporada")

rodadas_disponiveis = sorted(set(r["numero"] for r in rodadas))
rodada_selecionada = st.selectbox("Escolha a rodada que deseja visualizar", rodadas_disponiveis)

for rodada in rodadas:
    if rodada["numero"] != rodada_selecionada:
        continue

    st.markdown(f"<h4 style='margin-top: 30px;'>🔢 Rodada {rodada_selecionada}</h4>", unsafe_allow_html=True)
    for jogo in rodada.get("jogos", []):
        m_id, v_id = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
        m = times_map.get(m_id, {}); v = times_map.get(v_id, {})

        m_logo = m.get("logo", "https://cdn-icons-png.flaticon.com/512/147/147144.png")
        v_logo = v.get("logo", "https://cdn-icons-png.flaticon.com/512/147/147144.png")
        m_nome = m.get("nome", "Desconhecido")
        v_nome = v.get("nome", "Desconhecido")

        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            st.markdown(f"<div style='text-align: right;'><img src='{m_logo}' width='30'> <b>{m_nome}</b></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<h5 style='text-align: center;'>{gm}</h5>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<h5 style='text-align: center;'>x</h5>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<h5 style='text-align: center;'>{gv}</h5>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div style='text-align: left;'><img src='{v_logo}' width='30'> <b>{v_nome}</b></div>", unsafe_allow_html=True)

        # 💰 Renda variável do mandante
        if gm != "" and gv != "":
            try:
                descricao = f"Renda da partida rodada {rodada_selecionada}"
                check = supabase.table("movimentacoes_financeiras").select("id").eq("id_time", m_id).eq("descricao", descricao).execute()
                if not check.data:
                    res_estadio = supabase.table("estadios").select("*").eq("id_time", m_id).execute()
                    estadio = res_estadio.data[0] if res_estadio.data else None
                    if estadio:
                        renda, publico = calcular_renda_jogo(estadio)
                        saldo_atual = supabase.table("times").select("saldo").eq("id", m_id).execute().data[0]["saldo"]
                        novo_saldo = saldo_atual + renda
                        supabase.table("times").update({"saldo": novo_saldo}).eq("id", m_id).execute()
                        registrar_movimentacao(m_id, "entrada", renda, f"{descricao} (público: {publico:,})")
                        st.success(f"💰 Renda registrada: R${renda:,.2f} para {m_nome}")
            except Exception as e:
                st.warning(f"Erro ao calcular renda do jogo: {e}")
