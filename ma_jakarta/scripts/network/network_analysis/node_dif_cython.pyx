def centrality_difference(list node_data_normal, list node_data_flooded, str centrality_value):

    print("Starting to calculate centrality difference")

    cent_dif = []
    for normal in node_data_normal:
        for flooded in node_data_flooded:
            if normal[1]['osmid'] == flooded[1]['osmid']:
                cent_dif.append([flooded[0], flooded[1]['enum_id'], flooded[1]['enum_id_ce'], flooded[1][centrality_value]-normal[1][centrality_value]])
    print('done')

    return cent_dif
