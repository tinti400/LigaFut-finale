col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 2])

with col1:
    if jogador.get("imagem_url"):
        st.image(jogador["imagem_url"], width=60)

with col2:
    st.markdown(f"**{jogador['nome']}**")
    st.markdown(f"**{jogador.get('nacionalidade', '🇧🇷')}**")  # default 🇧🇷 se vazio

with col3:
    st.markdown(f"**Posição:** {jogador['posicao']}")

with col4:
    st.markdown(f"**Overall:** {jogador['overall']}")

with col5:
    st.markdown("**Valor:** R$ {:,.0f}".format(jogador["valor"]).replace(",", "."))
    origem = jogador.get("origem", "Desconhecida")
    st.markdown(f"**Origem:** {origem}")

with col6:
    if st.button(f"Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
        try:
            # Remove jogador do elenco
            supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

            # Insere no mercado com valor cheio
            supabase.table("mercado_transferencias").insert({
                "nome": jogador["nome"],
                "posicao": jogador["posicao"],
                "overall": jogador["overall"],
                "valor": jogador["valor"],
                "id_time": id_time,
                "time_origem": nome_time,
                "imagem_url": jogador.get("imagem_url", ""),
                "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                "origem": origem
            }).execute()

            registrar_movimentacao(
                id_time=id_time,
                jogador=jogador["nome"],
                valor=round(jogador["valor"] * 0.7),
                tipo="Mercado",
                categoria="Venda",
                destino="Mercado"
            )

            st.success(f"{jogador['nome']} foi vendido para o mercado (sem crédito de valor).")
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erro ao vender jogador: {e}")
