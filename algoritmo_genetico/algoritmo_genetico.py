from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import random
import math
import copy 

from database.frota_service import atualizar_capacidade_veiculo, buscar_veiculo_por_id, buscar_veiculos, cadastrar_veiculo, capacidade_disponivel_veiculo, excluir_veiculo
from database.insumo_service import buscar_detalhes_insumo_e_veiculo
from algoritmo_genetico.utils.utils import convert_hours_to_minutes

def criar_rota_inicial(lista_ids_produtos):
    rota = lista_ids_produtos[:]
    random.shuffle(rota)
    return [0] + rota + [0]

def matriz_distancia(cities_locations):
    matriz = {}
    
    for i, (lat1, lon1) in enumerate(cities_locations):
        matriz[i] = {}
        for j, (lat2, lon2) in enumerate(cities_locations):
            if i == j:
                matriz[i][j] = 0
            else:
                dx = (lat1 - lat2) * 111
                dy = (lon1 - lon2) * 111
                matriz[i][j] = math.sqrt(dx*dx + dy*dy)
    return matriz

def calculo_fitness_matriz_distancia(individuo, matriz_distancia, dados_paradas, info_veiculo):
    distancia_total = 0
    tempo_atual = 480  # 08:00 em minutos
    peso_total_acumulado = 0
    penalidade = 0 
    
    MULTA_ATRASO = 100
    MULTA_CAPACIDADE = 1000  # Multa pesada
    MULTA_AUTONOMIA = 5000   # Multa gravíssima
    
    for i in range(len(individuo) - 1):
        ponto_A = individuo[i]
        ponto_B = individuo[i+1]
        
        trecho = matriz_distancia[ponto_A][ponto_B]
        distancia_total += trecho
        tempo_atual += trecho * 1.5  # Velocidade média
        
        if ponto_B != 0: 
            p = dados_paradas.get(ponto_B)
            if p:
                peso_total_acumulado += p['peso']
                
                ini_min = convert_hours_to_minutes(p['janela_inicio'])
                fim_min = convert_hours_to_minutes(p['janela_fim'])
                
                if tempo_atual < ini_min:
                    tempo_atual = ini_min
                
                if tempo_atual > fim_min:
                    atraso = tempo_atual - fim_min
                    penalidade += atraso * MULTA_ATRASO * p['nivel_criticidade']
                
                tempo_atual += 15

    if peso_total_acumulado > info_veiculo['capacidade_maxima']:
        excesso = peso_total_acumulado - info_veiculo['capacidade_maxima']
        penalidade += excesso * MULTA_CAPACIDADE

    if distancia_total > info_veiculo['autonomia_total']:
        excesso_km = distancia_total - info_veiculo['autonomia_total']
        penalidade += (excesso_km **2) * MULTA_AUTONOMIA

    return distancia_total + penalidade
    
def order_crossover(parent1, parent2):    
    p1_middle = parent1[1:-1]
    p2_middle = parent2[1:-1]
    
    
    start, end = sorted(random.sample(range(len(p1_middle)), 2))
    
    child_middle = [None] * len(p1_middle)
    child_middle[start:end] = p1_middle[start:end]
    
    p2_remaining = [gene for gene in p2_middle if gene not in child_middle]
    
    ptr = 0
    
    for i in range(len(child_middle)):
        if child_middle[i] is None:
            child_middle[i] = p2_remaining[ptr]
            ptr += 1
            
    return [0] + child_middle + [0]    
    
def mutacao(solution, mutation_probability):

    mutated_solution = copy.deepcopy(solution)
    
    if random.random() < mutation_probability:
        
        if len(solution) > 3:
            idx1, idx2 = random.sample(range(1, len(solution) - 1), 2)
        
            mutated_solution[idx1], mutated_solution[idx2] = \
                mutated_solution[idx2], mutated_solution[idx1]
                
                
    return mutated_solution



