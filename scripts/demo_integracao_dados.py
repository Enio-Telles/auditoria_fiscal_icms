#!/usr/bin/env python3
"""
Demo de Integração dos Novos Dados
Demonstra a integração da Tabela ABC Farma e NESH ao sistema de auditoria fiscal
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auditoria_icms.data_processing.structured_loader import StructuredDataLoader
from src.auditoria_icms.data_processing.farmaceutico_processor import FarmaceuticoProcessor
from src.auditoria_icms.data_processing.nesh_processor import NESHProcessor

def demo_integracao_completa():
    """
    Demonstra a integração completa dos novos dados
    """
    print("🏥 === DEMO DE INTEGRAÇÃO - TABELA ABC FARMA + NESH === 🏥\n")
    
    # 1. Inicializar processadores
    print("📋 1. Inicializando processadores...")
    
    loader = StructuredDataLoader()
    farmaceutico = FarmaceuticoProcessor()
    nesh = NESHProcessor()
    
    print("   ✅ Processadores inicializados\n")
    
    # 2. Carregar dados ABC Farma
    print("💊 2. Carregando dados ABC Farma...")
    
    if farmaceutico.carregar_dados():
        stats_farma = farmaceutico.get_estatisticas()
        print(f"   ✅ {stats_farma['total_medicamentos']} medicamentos carregados")
        print(f"   📊 {stats_farma['ncms_unicos']} NCMs únicos: {stats_farma['ncms']}")
        print(f"   ⚡ {stats_farma['cests_unicos']} CESTs únicos: {stats_farma['cests']}")
        print(f"   🏭 {len(stats_farma['laboratorios'])} laboratórios")
        print(f"   💊 {len(stats_farma['formas_farmaceuticas'])} formas farmacêuticas")
    else:
        print("   ❌ Erro ao carregar dados ABC Farma")
        return
    
    print()
    
    # 3. Carregar regras NESH
    print("📖 3. Carregando regras NESH...")
    
    nesh_data = nesh.load_nesh_pdf()
    if nesh_data:
        regras = nesh_data.get('regras_gerais', {})
        print(f"   ✅ {len(regras)} regras gerais carregadas")
        for num, regra in list(regras.items())[:3]:
            print(f"   📜 Regra {num}: {regra['texto'][:100]}...")
    else:
        print("   ❌ Erro ao carregar regras NESH")
        return
    
    print()
    
    # 4. Demonstrar busca integrada
    print("🔍 4. Demonstrando busca integrada...")
    
    # Buscar medicamento por código de barras
    codigo_teste = "7891234567890"
    medicamento = farmaceutico.buscar_por_codigo_barras(codigo_teste)
    
    if medicamento:
        print(f"   🔍 Medicamento encontrado: {medicamento['descricao']}")
        print(f"   🏷️ NCM: {medicamento['ncm']} | CEST: {medicamento['cest']}")
        print(f"   💊 Princípio ativo: {medicamento['principio_ativo']}")
        print(f"   🏭 Laboratório: {medicamento['laboratorio']}")
        
        # Validar NCM com NESH
        ncm = medicamento['ncm']
        validacao = nesh.validate_ncm(ncm, medicamento['descricao'])
        print(f"   ✅ Validação NCM {ncm}: {validacao['valido']}")
        if validacao['observacoes']:
            for obs in validacao['observacoes']:
                print(f"      📝 {obs}")
    
    print()
    
    # 5. Demonstrar busca por similaridade
    print("🔎 5. Demonstrando busca por similaridade...")
    
    termo_busca = "DIPIRONA"
    similares = farmaceutico.buscar_similares(termo_busca, limite=3)
    
    print(f"   🔍 Buscando medicamentos similares a '{termo_busca}':")
    for i, med in enumerate(similares, 1):
        print(f"   {i}. {med['descricao']} (Score: {med['similarity_score']})")
        print(f"      NCM: {med['ncm']} | CEST: {med['cest']}")
    
    print()
    
    # 6. Demonstrar aplicação de regras NESH
    print("📋 6. Demonstrando aplicação de regras NESH...")
    
    # Aplicar regra geral para medicamento
    if medicamento:
        orientacao = nesh.get_classification_guidance(medicamento['descricao'])
        print(f"   📋 Orientação para '{medicamento['descricao'][:30]}...':")
        print(f"   📜 Regras aplicáveis: {orientacao.get('regras_aplicaveis', [])}")
        print(f"   💡 Recomendações: {orientacao.get('recomendacoes', [])}")
    
    print()
    
    # 7. Integração com sistema principal
    print("🔗 7. Demonstrando integração com StructuredDataLoader...")
    
    try:
        # Carregar via loader principal
        farma_data = loader.load_medicamentos_abc_farma()
        nesh_rules = loader.load_nesh_rules()
        
        if farma_data and nesh_rules:
            print("   ✅ Integração com StructuredDataLoader bem-sucedida")
            print(f"   📊 {len(farma_data.get('medicamentos', {}))} medicamentos via loader")
            print(f"   📖 {len(nesh_rules.get('regras_gerais', {}))} regras via loader")
            
            # Teste de validação via loader
            ncm_teste = "3004.90.69"
            validacao_loader = loader.validar_ncm_com_nesh(ncm_teste, "DIPIRONA SÓDICA")
            print(f"   🧪 Validação via loader - NCM {ncm_teste}: {validacao_loader['valido']}")
        else:
            print("   ⚠️ Integração parcial com StructuredDataLoader")
    
    except Exception as e:
        print(f"   ❌ Erro na integração: {e}")
    
    print()
    
    # 8. Estatísticas finais
    print("📈 8. Estatísticas finais da integração...")
    
    total_dados = {
        'medicamentos_abc_farma': len(farmaceutico.medicamentos),
        'ncm_farmaceuticos': len(farmaceutico.ncm_farmaceutico),
        'cest_farmaceuticos': len(farmaceutico.cest_farmaceutico),
        'regras_nesh': len(nesh_data.get('regras_gerais', {})),
        'capitulos_nesh': len(nesh_data.get('capitulos', {})),
        'posicoes_nesh': len(nesh_data.get('posicoes', {}))
    }
    
    print("   📊 Resumo dos dados integrados:")
    for tipo, quantidade in total_dados.items():
        print(f"      📋 {tipo.replace('_', ' ').title()}: {quantidade}")
    
    print()
    
    # 9. Verificar arquivos gerados
    print("💾 9. Verificando arquivos processados...")
    
    arquivos_processados = [
        "data/processed/medicamentos_abc_farma.json",
        "data/processed/nesh_processed.json"
    ]
    
    for arquivo in arquivos_processados:
        if Path(arquivo).exists():
            tamanho = Path(arquivo).stat().st_size
            print(f"   ✅ {arquivo} ({tamanho:,} bytes)")
        else:
            print(f"   ❌ {arquivo} não encontrado")
    
    print()
    print("🎉 === INTEGRAÇÃO CONCLUÍDA COM SUCESSO === 🎉")
    print("📋 Os dados da Tabela ABC Farma e NESH estão agora integrados ao sistema!")
    print("🔗 Use StructuredDataLoader para acessar os dados em outras partes do sistema.")

def demo_caso_uso_pratico():
    """
    Demonstra um caso de uso prático da integração
    """
    print("\n💼 === CASO DE USO PRÁTICO === 💼\n")
    
    # Simular classificação de um produto farmacêutico
    produto_teste = {
        'codigo_barras': '7891234567891',
        'descricao': 'PARACETAMOL 750MG COMPRIMIDO',
        'ncm_informado': '3004.90.69',
        'cest_informado': '13.001.00'
    }
    
    print(f"🧪 Classificando produto: {produto_teste['descricao']}")
    print(f"📊 Código de barras: {produto_teste['codigo_barras']}")
    print(f"🏷️ NCM informado: {produto_teste['ncm_informado']}")
    print(f"⚡ CEST informado: {produto_teste['cest_informado']}")
    
    # Inicializar processadores
    farmaceutico = FarmaceuticoProcessor()
    nesh = NESHProcessor()
    
    if not farmaceutico.carregar_dados():
        print("❌ Erro ao carregar dados farmacêuticos")
        return
    
    nesh_data = nesh.load_nesh_pdf()
    if not nesh_data:
        print("❌ Erro ao carregar regras NESH")
        return
    
    print("\n🔍 Verificações realizadas:")
    
    # 1. Verificar se produto existe na base ABC Farma
    medicamento_ref = farmaceutico.buscar_por_codigo_barras(produto_teste['codigo_barras'])
    if medicamento_ref:
        print(f"   ✅ Produto encontrado na base ABC Farma")
        print(f"   📋 Descrição de referência: {medicamento_ref['descricao']}")
        print(f"   🏷️ NCM de referência: {medicamento_ref['ncm']}")
        print(f"   ⚡ CEST de referência: {medicamento_ref['cest']}")
        
        # Verificar consistência
        ncm_consistente = produto_teste['ncm_informado'] == medicamento_ref['ncm']
        cest_consistente = produto_teste['cest_informado'] == medicamento_ref['cest']
        
        print(f"   🔍 NCM consistente: {'✅' if ncm_consistente else '❌'}")
        print(f"   🔍 CEST consistente: {'✅' if cest_consistente else '❌'}")
    else:
        print(f"   ⚠️ Produto não encontrado na base ABC Farma")
        
        # Buscar produtos similares
        similares = farmaceutico.buscar_similares(produto_teste['descricao'], limite=2)
        if similares:
            print(f"   🔍 Produtos similares encontrados:")
            for sim in similares:
                print(f"      📋 {sim['descricao']} (Score: {sim['similarity_score']})")
                print(f"      🏷️ NCM: {sim['ncm']} | CEST: {sim['cest']}")
    
    # 2. Validar NCM com regras NESH
    print(f"\n📖 Validação NCM {produto_teste['ncm_informado']} com regras NESH:")
    validacao = nesh.validate_ncm(produto_teste['ncm_informado'], produto_teste['descricao'])
    
    print(f"   📋 Resultado: {'✅ Válido' if validacao['valido'] else '❌ Inválido'}")
    for obs in validacao.get('observacoes', []):
        print(f"   📝 {obs}")
    
    # 3. Obter orientação de classificação
    print(f"\n💡 Orientação de classificação:")
    orientacao = nesh.get_classification_guidance(produto_teste['descricao'])
    
    for regra in orientacao.get('regras_aplicaveis', []):
        print(f"   📜 {regra}")
    
    for rec in orientacao.get('recomendacoes', []):
        print(f"   💡 {rec}")
    
    print(f"\n✅ Análise concluída!")

if __name__ == "__main__":
    demo_integracao_completa()
    demo_caso_uso_pratico()
