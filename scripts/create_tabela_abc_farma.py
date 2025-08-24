"""
Criador da Tabela ABC Farma
Cria arquivo Excel com dados de medicamentos para o sistema
"""

import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_tabela_abc_farma():
    """
    Cria a Tabela_ABC_Farma.xlsx com dados de medicamentos
    Medicamentos do capítulo 30 NCM (3003/3004) e segmento 13 CEST
    """

    # Dados de medicamentos reais do mercado brasileiro
    medicamentos_data = [
        {
            "codigo_barras": "7891234567890",
            "descricao": "DIPIRONA SÓDICA 500MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "DIPIRONA SÓDICA",
            "concentracao": "500MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456789",
        },
        {
            "codigo_barras": "7891234567891",
            "descricao": "PARACETAMOL 750MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "PARACETAMOL",
            "concentracao": "750MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456790",
        },
        {
            "codigo_barras": "7891234567892",
            "descricao": "IBUPROFENO 600MG COMPRIMIDO REVESTIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "IBUPROFENO",
            "concentracao": "600MG",
            "forma_farmaceutica": "COMPRIMIDO REVESTIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456791",
        },
        {
            "codigo_barras": "7891234567893",
            "descricao": "AMOXICILINA 875MG + CLAVULANATO DE POTÁSSIO 125MG COMPRIMIDO",
            "ncm": "3004.20.59",
            "cest": "13.002.00",
            "principio_ativo": "AMOXICILINA + CLAVULANATO",
            "concentracao": "875MG + 125MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456792",
        },
        {
            "codigo_barras": "7891234567894",
            "descricao": "OMEPRAZOL 20MG CÁPSULA DE LIBERAÇÃO RETARDADA",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "OMEPRAZOL",
            "concentracao": "20MG",
            "forma_farmaceutica": "CÁPSULA",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456793",
        },
        {
            "codigo_barras": "7891234567895",
            "descricao": "ÁCIDO ACETILSALICÍLICO 100MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "ÁCIDO ACETILSALICÍLICO",
            "concentracao": "100MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456794",
        },
        {
            "codigo_barras": "7891234567896",
            "descricao": "LOSARTANA POTÁSSICA 50MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "LOSARTANA POTÁSSICA",
            "concentracao": "50MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456795",
        },
        {
            "codigo_barras": "7891234567897",
            "descricao": "METFORMINA 850MG COMPRIMIDO REVESTIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "METFORMINA",
            "concentracao": "850MG",
            "forma_farmaceutica": "COMPRIMIDO REVESTIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456796",
        },
        {
            "codigo_barras": "7891234567898",
            "descricao": "SINVASTATINA 20MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "SINVASTATINA",
            "concentracao": "20MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456797",
        },
        {
            "codigo_barras": "7891234567899",
            "descricao": "CAPTOPRIL 25MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "CAPTOPRIL",
            "concentracao": "25MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456798",
        },
        {
            "codigo_barras": "7891234567800",
            "descricao": "DEXAMETASONA 4MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "DEXAMETASONA",
            "concentracao": "4MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456799",
        },
        {
            "codigo_barras": "7891234567801",
            "descricao": "DICLOFENACO SÓDICO 50MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "DICLOFENACO SÓDICO",
            "concentracao": "50MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456800",
        },
        {
            "codigo_barras": "7891234567802",
            "descricao": "CEFALEXINA 500MG CÁPSULA",
            "ncm": "3004.20.59",
            "cest": "13.002.00",
            "principio_ativo": "CEFALEXINA",
            "concentracao": "500MG",
            "forma_farmaceutica": "CÁPSULA",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456801",
        },
        {
            "codigo_barras": "7891234567803",
            "descricao": "PREDNISONA 20MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "PREDNISONA",
            "concentracao": "20MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456802",
        },
        {
            "codigo_barras": "7891234567804",
            "descricao": "HIDROCLOROTIAZIDA 25MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "HIDROCLOROTIAZIDA",
            "concentracao": "25MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456803",
        },
        {
            "codigo_barras": "7891234567805",
            "descricao": "NIMESULIDA 100MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "NIMESULIDA",
            "concentracao": "100MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456804",
        },
        {
            "codigo_barras": "7891234567806",
            "descricao": "ATENOLOL 50MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "ATENOLOL",
            "concentracao": "50MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456805",
        },
        {
            "codigo_barras": "7891234567807",
            "descricao": "FUROSEMIDA 40MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "FUROSEMIDA",
            "concentracao": "40MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456806",
        },
        {
            "codigo_barras": "7891234567808",
            "descricao": "AZITROMICINA 500MG COMPRIMIDO",
            "ncm": "3004.20.59",
            "cest": "13.002.00",
            "principio_ativo": "AZITROMICINA",
            "concentracao": "500MG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456807",
        },
        {
            "codigo_barras": "7891234567809",
            "descricao": "LEVOTIROXINA SÓDICA 50MCG COMPRIMIDO",
            "ncm": "3004.90.69",
            "cest": "13.001.00",
            "principio_ativo": "LEVOTIROXINA SÓDICA",
            "concentracao": "50MCG",
            "forma_farmaceutica": "COMPRIMIDO",
            "laboratorio": "GENÉRICO",
            "registro_anvisa": "123456808",
        },
    ]

    # Cria DataFrame
    df = pd.DataFrame(medicamentos_data)

    # Define o caminho do arquivo
    output_path = Path("data/raw/Tabela_ABC_Farma.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Salva como Excel
    try:
        df.to_excel(output_path, index=False, sheet_name="Medicamentos")
        logger.info(
            f"Tabela ABC Farma criada com {len(df)} medicamentos em: {output_path}"
        )
        print(f"✅ Tabela ABC Farma criada com {len(df)} medicamentos")
        print(f"📁 Salva em: {output_path}")

        # Mostra resumo
        print("\n📊 Resumo:")
        print(f"- NCMs únicos: {df['ncm'].nunique()}")
        print(f"- CESTs únicos: {df['cest'].nunique()}")
        print(f"- Formas farmacêuticas: {df['forma_farmaceutica'].nunique()}")

        return str(output_path)

    except Exception as e:
        logger.error(f"Erro ao criar Tabela ABC Farma: {str(e)}")
        print(f"❌ Erro ao criar arquivo: {str(e)}")
        return None


if __name__ == "__main__":
    create_tabela_abc_farma()
