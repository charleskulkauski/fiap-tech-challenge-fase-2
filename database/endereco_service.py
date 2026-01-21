import mysql.connector

from database.frota_service import buscar_veiculo_por_placa
from database.get_connection import get_connection
from database.ponto_base_service import buscar_ponto_base_por_veiculo

def buscar_enderecos():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rota")
        dados = cursor.fetchall()
        return dados
    except mysql.connector.Error as err:
        print(f"Erro ao listar endereços: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def buscar_por_rua(rua, numero, cep):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rota WHERE rua = %s AND numero = %s AND cep = %s", (rua, numero, cep))
        dado = cursor.fetchone()
        return dado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar rua: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def cadastrar_endereco(rua,numero, complemento, cidade, cep, veiculo, latitude, longitude):
    veiculo_id = buscar_veiculo_por_placa(veiculo)['veiculo_id'] if veiculo else None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO rota 
                 (rua, numero, complemento, cidade, cep, veiculo_designado_rota, latitude, longetude) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        valores = (rua, numero, complemento, cidade, cep, veiculo_id, latitude,longitude)
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao cadastrar endereço: {err}")
        return False
    finally:
        cursor.close()
        conn.close()
    
def buscar_enderecos_por_veiculo(veiculo_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)       
        cursor.execute("SELECT * FROM rota WHERE veiculo_designado_rota = %s", (veiculo_id,))
        resultado = cursor.fetchall()
        return resultado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar endereços por veículo: {err}")
        return []
    finally:
        cursor.close()
        conn.close()
    
def buscar_veiculo_por_rota(rua, numero, cep):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.modelo_caminhao, v.placa FROM veiculo v
            JOIN rota r ON v.veiculo_id = r.veiculo_designado_rota
            WHERE r.rua = %s AND r.numero = %s AND r.cep = %s
        """, (rua, numero, cep))
        dado = cursor.fetchone()
        return dado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar veículo por rota: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
        
def buscar_endereco_por_id(rota_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM rota WHERE rota_id = %s", (rota_id,))
        dado = cursor.fetchone()
        return dado
    except mysql.connector.Error as err:
        print(f"Erro ao buscar rota por ID: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
    

def excluir_rota(rua, numero):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rota WHERE rua = %s AND numero = %s", (rua, numero))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao deletar veículo: {err}")
        return False
    finally:
        cursor.close()
        conn.close()
        
        
def buscar_coordenadas_por_veiculo(veiculo_id):
    coords = []
    base = buscar_ponto_base_por_veiculo(veiculo_id)
    
    if not base:
        print(f"Aviso: Veículo {veiculo_id} não possui ponto base.")
        return [], ["Ponto base não encontrado"]
    
    coords.append((float(base['latitude']), float(base['longitude'])))
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT latitude, longitude from rota WHERE veiculo_designado_rota = %s", (veiculo_id,))
        resultado = cursor.fetchall()
        
        for r in resultado:
            if r['latitude'] is not None and r['longitude'] is not None:
                coords.append((float(r['latitude']), float(r['longitude'])))
                
                
        return coords
    
    except mysql.connector.Error as err:
        print(f"Erro ao buscar endereços por veículo: {err}")
        return []
    finally:
        cursor.close()
        conn.close()
    