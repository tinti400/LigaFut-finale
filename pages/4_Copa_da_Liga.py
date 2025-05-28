def exibir_card(jogo):
    id_m = jogo.get("mandante_ida")
    id_v = jogo.get("visitante_ida")

    mandante = times.get(id_m, {"nome": "Aguardando", "escudo_url": ""})
    visitante = times.get(id_v, {"nome": "Aguardando", "escudo_url": ""})

    # Gols de ida
    gm_ida = jogo.get("gols_ida_m", "?") if jogo.get("gols_ida_m") is not None else "?"
    gv_ida = jogo.get("gols_ida_v", "?") if jogo.get("gols_ida_v") is not None else "?"

    # Gols de volta
    gm_volta = jogo.get("gols_volta_v", "?") if jogo.get("gols_volta_v") is not None else "?"
    gv_volta = jogo.get("gols_volta_m", "?") if jogo.get("gols_volta_m") is not None else "?"

    # Soma dos gols
    try:
        gm_total = int(gm_ida) + int(gm_volta)
        gv_total = int(gv_ida) + int(gv_volta)
        agregado = f"{gm_total} x {gv_total}"
    except:
        agregado = "? x ?"

    # Resultado detalhado entre parênteses
    detalhes = f"({gm_ida} x {gv_ida} / {gm_volta} x {gv_volta})"

    card = f"""
    <div style='background:#222;padding:10px;border-radius:10px;margin-bottom:10px;color:white'>
        <div style='display:flex;align-items:center;justify-content:space-between;'>
            <div style='text-align:center;width:45%'>
                {'<img src="'+mandante['escudo_url']+'" width="40"><br>' if mandante['escudo_url'] else ''}
                {mandante["nome"]}
            </div>
            <div style='width:10%; text-align:center;'>
                <div style='font-size:12px'>{detalhes}</div>
                <div style='font-size:20px; font-weight:bold'>{agregado}</div>
            </div>
            <div style='text-align:center;width:45%'>
                {'<img src="'+visitante['escudo_url']+'" width="40"><br>' if visitante['escudo_url'] else ''}
                {visitante["nome"]}
            </div>
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)
