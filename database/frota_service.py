import mysql.connector
from database.get_connection import get_connection


def capacidade_disponivel_veiculo(placa):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        cursor.execute("SELECT capacidade_disponivel FROM veiculo WHERE placa = %s", (placa, ))
        dado = cursor.fetchone()

        return dado['capacidade_disponivel'] if dado else None
    except mysql.connector.Error as err:
        print(f"Erro ao buscar capacidade disponível do veículo: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
            
def atualizar_capacidade_veiculo(placa, nova_capacidade):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE veiculo SET capacidade_disponivel = %s WHERE placa = %s"
        valores = (nova_capacidade, placa)
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar capacidade do veículo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def buscar_veiculos():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM veiculo")
        dados = cursor.fetchall()
        return dados
    except mysql.connector.Error as err:
        print(f"Erro ao listar veículos: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def buscar_veiculo_por_id(veiculo_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM veiculo WHERE veiculo_id = %s", (veiculo_id, ))
        dado = cursor.fetchone()
        
        return dado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar veículo por ID: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
            
def buscar_veiculo_por_placa(placa):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        cursor.execute("SELECT * FROM veiculo WHERE placa = %s", (placa, ))
        dado = cursor.fetchone()
        
        return dado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar veículo por placa: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def cadastrar_veiculo(modelo, placa, capacidade, capacidade_disponivel, autonomia):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO veiculo 
                 (modelo_caminhao, placa, capacidade_maxima, capacidade_disponivel, autonomia_total) 
                 VALUES (%s, %s, %s, %s, %s)"""
        valores = (modelo, placa, capacidade, capacidade_disponivel, autonomia)
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao cadastrar veículo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def excluir_veiculo(veiculo_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rota WHERE veiculo_designado_rota = %s", (veiculo_id,))
        cursor.execute("DELETE FROM veiculo WHERE veiculo_id = %s", (veiculo_id,))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao deletar veículo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()