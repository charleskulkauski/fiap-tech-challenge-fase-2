import mysql.connector
from database.frota_service import buscar_veiculo_por_placa

from database.get_connection import get_connection

def buscar_insumos():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produto")
        dados = cursor.fetchall()
        
        if dados:
            for dado in dados:
                if dado['nivel_criticidade'] == 1:
                    dado['nivel_criticidade'] = "Baixo"
                elif dado['nivel_criticidade'] == 2:
                    dado['nivel_criticidade'] = "Médio"
                elif dado['nivel_criticidade'] == 3:
                    dado['nivel_criticidade'] = "Alto"
                    
        return dados
    except mysql.connector.Error as err:
        print(f"Erro ao listar insumos: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def cadastrar_insumo(nome, quantidade, peso, criticidade, janela, rota_designada_produto, veiculo):
    veiculo_id = buscar_veiculo_por_placa(veiculo)['veiculo_id'] if veiculo else None
                
    if criticidade == "Baixo":
        criticidade = 1
    elif criticidade == "Médio":
        criticidade = 2
    elif criticidade == "Alto":
        criticidade = 3
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO produto 
                 (nome, quantidade, peso, nivel_criticidade, janela_entrega, rota_designada_produto, veiculo_designado_produto) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        valores = (nome, quantidade, peso, criticidade, janela, rota_designada_produto, veiculo_id)
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao cadastrar insumo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def excluir_insumo(id_insumo):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produto WHERE produto_id = %s", (id_insumo,))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao deletar insumo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()
    
def buscar_detalhes_insumo_e_veiculo(veiculo_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.produto_id, p.peso, p.janela_entrega, p.nivel_criticidade, p.veiculo_designado_produto, p.rota_designada_produto, v.capacidade_maxima, v.autonomia_total
            FROM produto p
            LEFT JOIN veiculo v ON p.veiculo_designado_produto = v.veiculo_id
            WHERE p.veiculo_designado_produto = %s
         """, (veiculo_id, ))
        dados = cursor.fetchall()
        return dados
    except mysql.connector.Error as err:
        print(f"Erro ao buscar detalhes do insumo e veículo: {err}")
        return []
    finally:
        cursor.close()
        conn.close()