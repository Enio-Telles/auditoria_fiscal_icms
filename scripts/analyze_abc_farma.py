#!/usr/bin/env python3
"""
Script para analisar a estrutura da Tabela ABC Farma existente
"""

import pandas as pd
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def analyze_abc_farma():
    """Analisa a estrutura da Tabela ABC Farma existente"""

    try:
        # Caminho para o arquivo
        file_path = "data/raw/Tabela_ABC_Farma.xlsx"

        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return

        print("📊 Analisando Tabela ABC Farma...")

        # Ler todas as abas
        xls = pd.ExcelFile(file_path)
        print(f"📄 Abas encontradas: {xls.sheet_names}")

        for sheet_name in xls.sheet_names:
            print(f"\n🔍 Analisando aba: {sheet_name}")

            # Ler a aba
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"   📐 Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            print(f"   📋 Colunas: {list(df.columns)}")

            # Mostrar tipos de dados
            print("   🏷️ Tipos de dados:")
            for col in df.columns:
                print(f"      {col}: {df[col].dtype}")

            # Mostrar algumas amostras
            print("   📝 Primeiras 3 linhas:")
            print(df.head(3).to_string(index=False))

            # Verificar valores únicos em colunas importantes
            if "codigo_barras" in df.columns or "codigo_barra" in df.columns:
                codigo_col = (
                    "codigo_barras" if "codigo_barras" in df.columns else "codigo_barra"
                )
                print(f"   🔢 Códigos de barras únicos: {df[codigo_col].nunique()}")

            if "ncm" in df.columns:
                print(f"   🏷️ NCMs únicos: {df['ncm'].nunique()}")
                print("   🏷️ NCMs mais frequentes:")
                print(df["ncm"].value_counts().head(5))

            if "cest" in df.columns:
                print(f"   ⚡ CESTs únicos: {df['cest'].nunique()}")
                print("   ⚡ CESTs mais frequentes:")
                print(df["cest"].value_counts().head(5))

            print("\n" + "=" * 60)

    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_abc_farma()
