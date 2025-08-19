#!/usr/bin/env python3
"""
Análise da Tabela ABC Farma V2
Analisa a estrutura da nova versão da tabela farmacêutica
"""
import pandas as pd
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_abc_farma_v2():
    """Analisa a estrutura da Tabela ABC Farma V2"""
    
    try:
        # Caminho para o arquivo
        file_path = "data/raw/Tabela_ABC_Farma_V2.xlsx"
        
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return
        
        print("📊 Analisando Tabela ABC Farma V2...")
        
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
            print("   📝 Primeiras 5 linhas:")
            print(df.head(5).to_string(index=False))
            
            # Verificar valores únicos em colunas importantes
            if 'codigo_barras' in df.columns or 'codigo_barra' in df.columns:
                codigo_col = 'codigo_barras' if 'codigo_barras' in df.columns else 'codigo_barra'
                print(f"   🔢 Códigos de barras únicos: {df[codigo_col].nunique()}")
                print(f"   🔢 Total de códigos: {len(df[codigo_col])}")
            
            if 'ncm' in df.columns:
                print(f"   🏷️ NCMs únicos: {df['ncm'].nunique()}")
                print(f"   🏷️ NCMs mais frequentes:")
                print(df['ncm'].value_counts().head(10))
            
            if 'cest' in df.columns:
                print(f"   ⚡ CESTs únicos: {df['cest'].nunique()}")
                print(f"   ⚡ CESTs mais frequentes:")
                print(df['cest'].value_counts().head(10))
            
            # Verificar se há campos de descrição
            desc_cols = [col for col in df.columns if 'desc' in col.lower()]
            if desc_cols:
                print(f"   📝 Colunas de descrição: {desc_cols}")
                for desc_col in desc_cols:
                    print(f"      {desc_col}: {df[desc_col].nunique()} descrições únicas")
            
            # Verificar se há campos relacionados a medicamentos
            med_cols = [col for col in df.columns if any(term in col.lower() for term in ['med', 'farm', 'principio', 'laboratorio', 'concent'])]
            if med_cols:
                print(f"   💊 Colunas farmacêuticas: {med_cols}")
            
            print("\n" + "="*80)
    
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_abc_farma_v2()
