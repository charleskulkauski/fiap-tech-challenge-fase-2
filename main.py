import copy
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import random

from streamlit_folium import st_folium

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from algoritmo_genetico.algoritmo_genetico import order_crossover, mutacao, calculo_fitness_matriz_distancia, matriz_distancia

from database.endereco_service import buscar_coordenadas_por_veiculo, buscar_endereco_por_id, buscar_enderecos, buscar_enderecos_por_veiculo, buscar_por_rua, cadastrar_endereco, excluir_rota
from database.insumo_service import buscar_detalhes_insumo_e_veiculo, buscar_insumos, cadastrar_insumo, excluir_insumo
from database.frota_service import atualizar_capacidade_veiculo, buscar_veiculo_por_id, buscar_veiculo_por_placa, buscar_veiculos, cadastrar_veiculo, capacidade_disponivel_veiculo, excluir_veiculo
from database.ponto_base_service import buscar_enderecos_bases, buscar_ponto_base_por_veiculo, cadastrar_ponto_base, excluir_ponto_base

geolocator = Nominatim(user_agent="logistica_hospitalar", timeout=10)
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=2,
    max_retries=3,
    swallow_exceptions=False
)

coords = []

def converter_endereco_para_coords(endereco):
    try:
        location = geocode(endereco)

        if location is None:
            return None, None

        return location.latitude, location.longitude

    except Exception as e:
        print(f"Erro ao geocodificar endereço '{endereco}': {e}")
        return None, None
    
    
def preparar_coordenadas_geograficas(veiculo_id):
    coords = buscar_coordenadas_por_veiculo(veiculo_id)
    
    if not coords:
        return None, "Nenhuma coordenada encontrada"
    
    return (coords), []

horarios = []
for h in range(24):
    for m in [0, 30]:
        horarios.append(f"{h:02d}:{m:02d}")
        
# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Logística Hospitalar", layout="wide")

# --- SIDEBAR DE NAVEGAÇÃO ---
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Selecione a Gestão:", ["📦 Insumos", "🚛 Veículos", "📍 Rota dos Veículos","🏠 Partida Inicial de Veículos", "🚀 Otimização"])

# --- PÁGINA: GESTÃO DE INSUMOS ---
if pagina == "📦 Insumos":
    st.title("Gestão de Inventário")
    st.write("Gerencie os insumos hospitalares")

    with st.container(border=True):
        st.header("Novo Insumo")    
        veiculos = ["Nenhum"]
        veiculos.extend([v['placa'] for v in buscar_veiculos()])
        veiculo = st.selectbox("Veículo Designado (Placa)", veiculos, key="veiculo")
            
        if veiculo != "Nenhum":
            veiculo_id = buscar_veiculo_por_placa(veiculo)
            rotas = buscar_enderecos_por_veiculo(veiculo_id['veiculo_id'])
                
            opcoes_rotas = [
                f"{r['rua']}, {r['numero']} - {r['cidade']} ({r['cep']})" for r in rotas
            ]   
            rota = st.selectbox("Rota Entrega", opcoes_rotas, key=f"rota_{veiculo}")

        else:
            st.selectbox("Rota Designada", [], key="rota_vazia")
                
                
    with st.form("form_insumo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Insumo")
            qtd = st.number_input("Quantidade", min_value=0)
        with col2:
            crit = st.selectbox("Nível Crítico", ["Baixo", "Médio", "Alto"])            
            col_ini, col_fim = st.columns(2)
            with col_ini:
                hora_inicio = st.selectbox("Janela de Início", horarios, index=16)
            with col_fim:
                hora_fim = st.selectbox("Horario Final", horarios, index=36)
        col3 = st.columns(1)[0]
        with col3:
            peso = st.number_input("Peso Unitário (kg)", min_value=0.0)
            
            
        if st.form_submit_button("Cadastrar Insumo"):
            if nome and qtd:
                capacidade_atual = capacidade_disponivel_veiculo(veiculo)
                rota_id = buscar_por_rua(rota.split(",")[0], int(rota.split(",")[1].split("-")[0].strip()), rota.split("(")[1].replace(")","").strip())['rota_id'] if veiculo != "Nenhum" else None
                janela = f"{hora_inicio} - {hora_fim}"
                
                if capacidade_atual > 0 and (peso * qtd) > capacidade_atual:
                    st.error(f"⚠️ Capacidade excedida! O veículo {veiculo} suporta até {capacidade_atual}kg.")
                else:
                    atualizar_capacidade_veiculo(veiculo, capacidade_atual - (peso * qtd))
                    cadastrar_insumo(nome, qtd, peso, crit, janela, rota_id, veiculo)
                    st.toast("Insumo cadastrado!", icon="✅")
                    st.rerun()

    st.divider()
    
    with st.container(border=True):
        st.header("Insumos Cadastrados")
        for item in buscar_insumos():
            
            endereco = buscar_endereco_por_id(item['rota_designada_produto'])
            with st.container(border=True):
                c_dados, c_btn = st.columns([0.9, 0.1])
                with c_dados:
                    st.subheader(f"📦 {item['nome']}")
                    st.write(f"**Peso:** {item['peso']}KG | **Qtd:** {item['quantidade']} | **Entrega:** {item['janela_entrega']}h | **Crítico:** `{item['nivel_criticidade']}` | **Veículo:** `{item['veiculo_designado_produto']}`")
                    st.write(f"**Rota:** {endereco['rua']}, {endereco['numero']} - {endereco['cidade']} ({endereco['cep']})")
                with c_btn:
                    if st.button("🗑️", key=f"del_ins_{item['produto_id']}"):
                        excluir_insumo(item['produto_id'])
                        st.rerun()

# --- PÁGINA: GESTÃO DE FROTAS ---
elif pagina == "🚛 Veículos":
    st.title("Gestão de Frotas")
    st.write("Cadastre e monitore os veículos de entrega")

    with st.form("form_veiculo", clear_on_submit=True):
        st.header("Novo Veículo")
        col1, col2 = st.columns(2)
        with col1:
            modelo = st.text_input("Modelo do Caminhão")
            placa = st.text_input("Placa")
        with col2:
            capacidade = st.number_input("Capacidade Máxima (kg)", min_value=0.0)
            capacidade_disponivel = capacidade
            autonomia = st.number_input("Autonomia Total (km)", min_value=0)
        
        if st.form_submit_button("Cadastrar Veículo"):
            if modelo and placa:
                try:
                    cadastrar_veiculo(modelo, placa, capacidade, capacidade_disponivel, autonomia)
                    st.toast(f"Veículo {placa} cadastrado!", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()

    with st.container(border=True):
        st.header("Veículos Cadastrados")
        veiculos = buscar_veiculos()
        if not veiculos:
            st.info("Nenhum caminhão cadastrado.")
        else:
            for v in veiculos:
                with st.container(border=True):
                    col_info, col_del = st.columns([0.9, 0.1])
                    with col_info:
                        st.subheader(f"🚛 {v['modelo_caminhao']}")
                        st.markdown(f"""
                        **Placa:** `{v['placa']}` | 
                        **Capacidade:** {v['capacidade_maxima']} kg | 
                        **Autonomia:** {v['autonomia_total']} km
                        """)
                    with col_del:
                        if st.button("🗑️", key=f"del_v_{v['veiculo_id']}", help="Excluir veículo"):
                            excluir_veiculo(v['veiculo_id'])
                            st.rerun()

# --- PÁGINA: GESTÃO DE ENDEREÇOS ---                        
elif pagina == "📍 Rota dos Veículos":
    st.title("Gestão de Pontos de Entrega")
    st.write("Cadastre os locais de destino para otimização da sua rota. Apenas uma rota por caminhão")

    # 1. FORMULÁRIO DE CADASTRO
    with st.form("form_rota", clear_on_submit=True):
        st.header("Nova Rota de Entrega")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            rua = st.text_input("Rua", placeholder="Ex: Av. Paulista")
        with col2:
            numero = st.number_input("Número", min_value=0, step=1)
            
        col3, col4 = st.columns(2)
        with col3:
            complemento = st.text_input("Complemento", placeholder="Ex: Bloco A / Próximo ao Hospital")
        with col4:
            veiculos = buscar_veiculos()
            lista_placas = [v['placa'] for v in veiculos]
            veiculo_selecionado = st.selectbox("Veículo", lista_placas)
        col5, col6 = st.columns(2)
        with col5:
            cidade = st.text_input("Cidade", placeholder="Ex: São Paulo")
        with col6:
            cep = st.text_input("CEP", placeholder="Ex: 01311-000")

        if st.form_submit_button("Cadastrar Endereço"):
            if rua and numero:
                placa_envio = None if veiculo_selecionado == "Nenhum" else veiculo_selecionado

                endereco = f"{rua}, {numero}, {cidade}, {cep}"
                latitude, longitude = converter_endereco_para_coords(endereco)

                if latitude is None:
                    st.warning(f"Endereço inválido: {endereco}")
                
                try:
                    sucesso = cadastrar_endereco(rua, numero, complemento, cidade, cep, placa_envio, latitude, longitude)
                    if sucesso:
                        st.toast(f"Endereço {rua}, {numero} cadastrado!", icon="📍")
                        st.rerun()
                    else:
                        st.error("Erro técnico ao salvar no banco.")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.warning("Por favor, preencha o endereço e o número.")
    st.divider()
    
    # 2. LISTAGEM DE ENDEREÇOS
    with st.container(border=True):
        st.header("Pontos de Entrega Cadastrados")
        rotas = buscar_enderecos()
        
        if not rotas:
            st.info("Nenhum endereço cadastrado para as rotas.")
        else:
            for r in rotas:
                with st.container(border=True):
                    placa_veiculo = buscar_veiculo_por_id(r['veiculo_designado_rota'])['placa'] if r['veiculo_designado_rota'] else None
                    col_info, col_del = st.columns([0.9, 0.1])
                    with col_info:
                        st.subheader(f"📍 {r['rua']}, {r['numero']} - {r['cep']}")
                        
                        info_complemento = r['complemento'] if r['complemento'] else "Sem complemento"
                        designacao = f"Placa: {placa_veiculo}" if placa_veiculo else "ERRO! Veículo não cadastrado"
                        
                        st.markdown(f"""
                        **Complemento:** {info_complemento} | 
                        **Veículo:** `{designacao}`
                        """)
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_rota_{r['rota_id']}", help="Remover endereço"):
                            if excluir_rota(r['rua'], r['numero']):
                                st.toast("Endereço removido!", icon="🗑️")
                                st.rerun()

# -- PÁGINA: GESTÃO DE PONTOS DE PARTIDA DE VEÍCULOS ---
elif pagina == "🏠 Partida Inicial de Veículos":
    st.title("Configuração de Ponto de Partida")
    st.write("Cadastre a base/depósito de onde o veículo iniciará a rota.")

    with st.form("form_ponto_base"):
        veiculos = buscar_veiculos()        
            
        col1, col2 = st.columns([3, 1])
        with col1:
            rua_b = st.text_input("Rua", placeholder="Ex: Av. Paulista")
        with col2:
            numero_b = st.number_input("Número", min_value=0, step=1)
            
        col3 = st.columns(1)[0]
        with col3:
            veiculos = buscar_veiculos()
            lista_placas = [v['placa'] for v in veiculos]
            placa_v = st.selectbox("Veículo", lista_placas)
        
        col4, col5 = st.columns(2)
        with col4:
            cidade_b = st.text_input("Cidade", placeholder="Ex: São Paulo")
        with col5:
            cep_b = st.text_input("CEP", placeholder="Ex: 01311-000")
        
        col6 = st.columns(1)[0]
        with col6:
            nome_b = st.text_input("Nome do Ponto Base", placeholder="Ex: Depósito Central")

        if st.form_submit_button("Salvar Ponto Base"):
            id_v = next(v['veiculo_id'] for v in veiculos if v['placa'] == placa_v)
            
            veiculo_cadastrado = buscar_ponto_base_por_veiculo(id_v)
            
            if veiculo_cadastrado:
                st.error(f"⚠️ O veículo {placa_v} já possui um ponto base cadastrado.")
            else:
                endereco = f"{rua_b}, {numero_b}, {cidade_b}, {cep_b}"
                latitude, longitude = converter_endereco_para_coords(endereco)

            if latitude is None:
                st.warning(f"Endereço inválido: {endereco}")
                
            cadastrar_ponto_base(rua_b, numero_b, cidade_b, id_v, cep_b, nome_b, latitude, longitude)
            st.success("Ponto base definido com sucesso!")
            st.rerun()
            
    with st.container(border=True):
        st.header("Pontos de Entrega Cadastrados")
        rotas = buscar_enderecos_bases()
        
        if not rotas:
            st.info("Nenhum endereço cadastrado para as rotas.")
        else:
            for r in rotas:
                with st.container(border=True):
                    placa_veiculo = buscar_veiculo_por_id(r['veiculo_id'])['placa'] if r['veiculo_id'] else None
                    col_info, col_del = st.columns([0.9, 0.1])
                    with col_info:
                        st.subheader(f"📍 {r['rua']}, {r['numero']} - {r['cep']}")
                        designacao = f"Placa: {placa_veiculo}"
                        
                        st.markdown(f"""
                        **Nome do Ponto Base:** {r['nome_da_base']} |
                        **Veículo:** `{designacao}`
                        """)
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_rota_{r['ponto_base_id']}", help="Remover endereço"):
                            if excluir_ponto_base(r['rua'], r['numero'], r['cep']):
                                st.toast("Endereço removido!", icon="🗑️")
                                st.rerun()
                
# --- PÁGINA: GESTÃO DE OTIMIZAÇÃO DE ROTAS ---                      
elif pagina == "🚀 Otimização":
    st.title("🚑 Sistema de Roteamento Hospitalar Inteligente")
    st.markdown("Use Algoritmos Genéticos para otimizar a entrega de insumos médicos (Tech Challenge - Fase 2).")

    placa_selecionada = None
    with st.container(border=True):
        # -- SEÇÃO 1: CONFIGURAR VEICULO E ROTA
        st.markdown("### 🚚 Seleção de Veículo e Rota")
        veiculos = buscar_veiculos()
        
        dict_veiculos = {v['placa']: v['veiculo_id'] for v in veiculos}
        placa_selecionada = st.selectbox("Selecione o Veículo para Otimização", list(dict_veiculos.keys()))
        
        rota_id_para_indice = {
            rota['rota_id']: idx + 1 
            for idx, rota in enumerate(buscar_enderecos_por_veiculo(dict_veiculos[placa_selecionada]))
        }
        
        veiculo_id = dict_veiculos[placa_selecionada]
        
        ponto_saida = buscar_ponto_base_por_veiculo(veiculo_id)
        rotas_do_veiculo = buscar_enderecos_por_veiculo(veiculo_id)
        
        if not ponto_saida:
                st.error(f"⚠️ O veículo {placa_selecionada} não possui um Ponto Base cadastrado. Cadastre-o primeiro.")
        elif not rotas_do_veiculo:
            st.warning(f"O veículo {placa_selecionada} não possui destinos vinculados.")
        else:
            with st.container(border=True):
                st.subheader(f"📍 Roteiro para {placa_selecionada}")
                
                st.info(f"🏠 **Ponto de Saída:** {ponto_saida['rua']}, {ponto_saida['numero']} - {ponto_saida['cidade']}")
                
                st.write("**Destinos de Entrega:**")
                for r in rotas_do_veiculo:
                    with st.expander(f"📦 {r['rua']}, {r['numero']}"):
                        st.write(f"Cidade: {r['cidade']} | Complemento: {r['complemento']}")

            if st.button("Calcular Melhor Rota", type="primary"):
                veiculo_selecionado = next(v for v in veiculos if v['veiculo_id'] == veiculo_id)
        
                dados_produtos = buscar_detalhes_insumo_e_veiculo(veiculo_id)
                lista_destinos = rotas_do_veiculo
                
                produtos_por_parada = {}
                
                if not dados_produtos:
                    st.warning("Este veículo não tem produtos cadastrados.")
                
                for produto in dados_produtos:
                    rota_id = produto['rota_designada_produto']
                    
                    if rota_id not in rota_id_para_indice:
                        continue
                    
                    indice_ag = rota_id_para_indice[rota_id]
                    
                    if indice_ag not in produtos_por_parada:
                        produtos_por_parada[indice_ag] = []
                        
                    produtos_por_parada[indice_ag].append(produto)

                mapa_dados_por_indice = {}
                carga_total_demandada = 0
                
                for indice_ag in range(1, len(lista_destinos) + 1):
                    
                    insumos = produtos_por_parada.get(indice_ag, [])
                    
                    if insumos:
                        peso_total = sum(float(p['peso']) for p in insumos)
                        criticidade_max = max(int(p['nivel_criticidade']) for p in insumos)
                        
                        item_critico = max(insumos, key=lambda x: int(x['nivel_criticidade']))
                        janela_inicio = item_critico['janela_entrega'].split(" - ")[0]
                        janela_fim = item_critico['janela_entrega'].split(" - ")[1]
                        
                        mapa_dados_por_indice[indice_ag] = {
                            'peso': peso_total,
                            'janela_inicio': janela_inicio,
                            'janela_fim': janela_fim,
                            'nivel_criticidade': criticidade_max,
                            'qtd_itens': len(insumos)
                        }   
                        
                        carga_total_demandada += peso_total
                        
                    else:
                        mapa_dados_por_indice[indice_ag] = {
                            'peso': 0,
                            'janela_inicio': "08:00",
                            'janela_fim': "18:00",
                            'nivel_criticidade': 0,
                            'qtd_itens': 0
                        }
                        
                if carga_total_demandada > veiculo_selecionado['capacidade_maxima']:
                    st.warning(f"⚠️ Atenção: A carga total ({carga_total_demandada}kg) excede a capacidade do veículo ({veiculo_selecionado['capacidade_maxima']}kg). O algoritmo tentará, mas haverá penalidades altas.")

                st.session_state['dados_otimizacao'] = {
                    'ponto_base': ponto_saida,
                    'destinos': lista_destinos,
                    'veiculo': veiculo_selecionado,
                    'mapa_dados': mapa_dados_por_indice,
                    'info_veiculo': {
                        'capacidade_maxima': veiculo_selecionado['capacidade_maxima'],
                        'autonomia_total': veiculo_selecionado['autonomia_total']
                    }
                }
                st.success(f"Dados carregados! {len(dados_produtos)} insumos distribuídos em {len(lista_destinos)} paradas.")
                
    
    st.markdown("### ⚙️ 1. Configuração dos Parâmetros do GA")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        populacao_size = c1.slider("Tamanho da População", 10, 200, 50)
        n_geracoes = c2.slider("Número de Gerações", 10, 500, 100)
        mutation_prob = c3.slider("Taxa de Mutação", 0.0, 1.0, 0.2)
            
        btn_processar = st.button("▶ Executar Algoritmo Genético", type="primary", use_container_width=True)

    # --- SEÇÃO 2: EXECUÇÃO ---
    if btn_processar:
        def selecao_torneio(pop, fits, k=3):
            selecionados = random.sample(list(zip(fits, pop)), k)
            selecionados.sort(key=lambda x: x[0])
            return copy.deepcopy(selecionados[0][1])
        
        if 'dados_otimizacao' not in st.session_state:
            st.error("Por favor, clique em 'Calcular Melhor Rota' primeiro para carregar os dados.")
            st.stop()
            
        else:
            dados = st.session_state['dados_otimizacao']
            
            st.markdown("### 🧬 2. Evolução em Tempo Real")

            lista_completa_pontos = [dados['ponto_base']] + dados['destinos']
            dados_paradas = dados['mapa_dados']
            info_veiculo = dados['info_veiculo']
            
            enderecos_formatados = [f"{p['rua']}, {p['numero']}, {p['cidade']}" for p in lista_completa_pontos]
            
            dados_geo, nao_encontrados = preparar_coordenadas_geograficas(veiculo_id)

            if nao_encontrados:
                st.error("Endereços inválidos impedem a execução.")
                st.stop()

        coords = buscar_coordenadas_por_veiculo(veiculo_id)
        dist_matrix = matriz_distancia(coords)
        
        num_entregas = len(coords) 
        
        indices_entregas = list(range(1, len(coords))) 
        
        populacao = []
        for _ in range(populacao_size):
            rota = indices_entregas[:]
            random.shuffle(rota)
            populacao.append([0] + rota + [0])


        primeira_distancia_real = calculo_fitness_matriz_distancia(populacao[0], dist_matrix, dados_paradas, info_veiculo)
        scores_iniciais = [calculo_fitness_matriz_distancia(ind, dist_matrix, dados_paradas, info_veiculo) for ind in populacao]
        initial_best_fitness = min(scores_iniciais)
        
        best_fitness_values = []
        start_time = time.time()
        
        col_mapa, col_grafico = st.columns(2)
        col_fitness = st.columns(4)[3]
        with col_mapa:
            st.markdown("##### Visualização da Rota")
            mapa_placeholder = st.empty()

        with col_grafico:
            st.markdown("##### Evolução")             
            grafico_placeholder = st.empty()
            
        with col_fitness:
            metric_placeholder = st.empty()
            
        for generation in range(n_geracoes):
            
            scores = [calculo_fitness_matriz_distancia(ind, dist_matrix, dados_paradas, info_veiculo) for ind in populacao]
            
            pop_ordenada = [x for _, x in sorted(zip(scores, populacao))]
            melhor_score = min(scores)
            melhor_ind = pop_ordenada[0]
            best_fitness_values.append(melhor_score)    

            nova_populacao = [melhor_ind] 
            
            while len(nova_populacao) < populacao_size:
                p1 = selecao_torneio(populacao, scores, k=3)
                p2 = selecao_torneio(populacao, scores, k=3)
            
                filho = order_crossover(p1, p2)
                filho = mutacao(filho, mutation_prob)
                nova_populacao.append(filho)
                
            populacao = nova_populacao

            # --- ATUALIZAÇÃO DA VISUALIZAÇÃO ---
            if generation % 5 == 0 or generation == n_geracoes - 1:                
                fig_mapa, ax_mapa = plt.subplots(figsize=(5,4))
                coords_np = np.array(coords)
                rota_coords = coords_np[melhor_ind]
                    
                ax_mapa.scatter(coords_np[1:, 1], coords_np[1:, 0], c='blue')
                ax_mapa.scatter(coords_np[0, 1], coords_np[0, 0], c='red', marker='H', s=100)
                ax_mapa.plot(rota_coords[:, 1], rota_coords[:, 0], c='green', alpha=0.6)
                ax_mapa.set_title(f"Geração {generation} | Custo: {melhor_score:.2f}")
                    
                mapa_placeholder.pyplot(fig_mapa)
                plt.close(fig_mapa)
                    
                fig_fit, ax_fit = plt.subplots(figsize=(5,4))
                ax_fit.plot(best_fitness_values, color='red')
                ax_fit.set_title("Curva de Convergência")
                ax_fit.set_xlabel("Geração")
                ax_fit.set_ylabel("Custo")
                grafico_placeholder.pyplot(fig_fit)
                plt.close(fig_fit)
                
                diff = melhor_score - initial_best_fitness
                metric_placeholder.metric(
                    label="Fitness Atual", 
                    value=f"{melhor_score:.2f}",
                    delta=f"{diff:.2f}",
                    delta_color="inverse"
                )
            
                time.sleep(0.02) 
       
                 
        metric_placeholder.empty()
            
        best_fitness = melhor_score

        # --- SEÇÃO 3: RESULTADOS FINAIS & LLM ---
        st.divider()
        st.markdown("### 📊 3. Resultado")
        
        total_time = time.time() - start_time
        improvement = ((initial_best_fitness - melhor_score) / initial_best_fitness) * 100
        
        c1, c2, c3 = st.columns(3)
        
        c1.metric("Tempo de Execução", f"{total_time:.2f} s")
        c2.metric("Inicial (Aleatório)", f"{initial_best_fitness:.2g}")
        c3.metric("Custo Final (Otimizado)", f"{melhor_score:.2f} ({improvement:.2f}% de melhoria)")

        if melhor_score > 5000:
             st.warning("⚠️ Atenção: A rota encontrada viola restrições de carga ou autonomia. Tente trocar o veículo ou reduzir as paradas.")


