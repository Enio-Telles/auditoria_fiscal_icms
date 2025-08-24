"""
Exemplo de Uso do Sistema de Agentes
====================================

Este arquivo demonstra como usar o sistema completo de agentes para auditoria fiscal,
incluindo criação de agentes, execução de tarefas individuais e workflows completos.
"""

import asyncio
import json
from datetime import datetime
from src.agents import (
    create_audit_agent_system,
    AgentTask,
    TaskPriority,
    quick_classify_product,
    get_agent_capabilities_summary
)


async def exemplo_agentes_individuais():
    """Demonstra uso de agentes individuais."""
    print("=" * 60)
    print("EXEMPLO 1: Uso de Agentes Individuais")
    print("=" * 60)
    
    # Criar sistema de agentes
    agent_manager, agent_coordinator = create_audit_agent_system()
    
    try:
        # Iniciar sistema
        await agent_manager.start()
        await agent_coordinator.start()
        
        # Criar instâncias dos agentes
        await agent_manager.create_agent("ExpansionAgent", "expansion_agent")
        await agent_manager.create_agent("NCMAgent", "ncm_agent")
        await agent_manager.create_agent("CESTAgent", "cest_agent")
        
        # Iniciar agentes
        await agent_manager.start_agent("expansion_agent")
        await agent_manager.start_agent("ncm_agent")
        await agent_manager.start_agent("cest_agent")
        
        # Exemplo 1: Expansão de descrição de produto
        print("\n1. Expandindo descrição de produto...")
        expansion_task = AgentTask(
            type="expand_description",
            data={
                "description": "Pneu aro 15 185/65 R15",
                "additional_info": "Pneu radial para veículos de passeio"
            },
            priority=TaskPriority.HIGH
        )
        
        expansion_result = await agent_manager.execute_task("expansion_agent", expansion_task)
        print(f"Descrição expandida: {expansion_result['expanded_description'][:100]}...")
        print(f"Características técnicas: {expansion_result['technical_specs'][:3]}")
        
        # Exemplo 2: Classificação NCM
        print("\n2. Classificando NCM...")
        ncm_task = AgentTask(
            type="classify_ncm",
            data={
                "description": expansion_result["expanded_description"],
                "technical_specs": expansion_result["technical_specs"]
            }
        )
        
        ncm_result = await agent_manager.execute_task("ncm_agent", ncm_task)
        print(f"NCM classificado: {ncm_result['ncm_code']} - {ncm_result['ncm_description']}")
        print(f"Confiança: {ncm_result['confidence']:.2%}")
        
        # Exemplo 3: Classificação CEST
        print("\n3. Classificando CEST...")
        cest_task = AgentTask(
            type="classify_cest",
            data={
                "description": expansion_result["expanded_description"],
                "ncm_code": ncm_result["ncm_code"],
                "state": "SP"
            }
        )
        
        cest_result = await agent_manager.execute_task("cest_agent", cest_task)
        print(f"CEST classificado: {cest_result['cest_code']} - {cest_result['cest_description']}")
        print(f"Confiança: {cest_result['confidence']:.2%}")
        print(f"ST Requerida: {'Sim' if cest_result['st_analysis']['st_required'] else 'Não'}")
        
        # Mostrar status dos agentes
        print("\n4. Status dos agentes:")
        agents_list = agent_manager.list_agents()
        for agent_info in agents_list:
            print(f"  - {agent_info['name']}: {agent_info['status']} "
                  f"(Tarefas completadas: {agent_info['tasks_completed']})")
    
    finally:
        # Limpar recursos
        await agent_manager.stop()
        await agent_coordinator.stop()


async def exemplo_workflow_completo():
    """Demonstra uso de workflow completo."""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Workflow Completo de Classificação")
    print("=" * 60)
    
    # Criar sistema de agentes
    agent_manager, agent_coordinator = create_audit_agent_system()
    
    try:
        # Iniciar sistema
        await agent_manager.start()
        await agent_coordinator.start()
        
        # Criar todos os agentes necessários
        await agent_manager.create_agent("ExpansionAgent", "expansion_agent")
        await agent_manager.create_agent("NCMAgent", "ncm_agent") 
        await agent_manager.create_agent("CESTAgent", "cest_agent")
        await agent_manager.create_agent("AggregationAgent", "aggregation_agent")
        
        # Iniciar agentes
        for agent_name in ["expansion_agent", "ncm_agent", "cest_agent", "aggregation_agent"]:
            await agent_manager.start_agent(agent_name)
        
        print("\n1. Criando workflow de classificação de produto...")
        
        # Criar workflow a partir de template
        workflow_id = await agent_coordinator.create_workflow_from_template(
            template_name="product_classification",
            workflow_id=f"product_class_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            context={
                "product_description": "Medicamento Paracetamol 500mg comprimidos",
                "additional_info": "Medicamento analgésico e antitérmico",
                "state": "SP"
            }
        )
        
        print(f"Workflow criado: {workflow_id}")
        
        # Executar workflow
        print("\n2. Executando workflow...")
        await agent_coordinator.execute_workflow(workflow_id)
        
        # Monitorar progresso
        print("\n3. Monitorando progresso...")
        while True:
            status = agent_coordinator.get_workflow_status(workflow_id)
            print(f"Status: {status['status']} - Progresso: {status['progress_percentage']:.1f}%")
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            await asyncio.sleep(2)
        
        # Mostrar resultado final
        final_status = agent_coordinator.get_workflow_status(workflow_id)
        print(f"\n4. Workflow concluído com status: {final_status['status']}")
        
        if final_status['status'] == 'completed':
            print("\nResultados dos steps:")
            for step in final_status['steps']:
                if step['status'] == 'completed':
                    print(f"  - {step['id']}: ✓ Concluído em {step['elapsed_time_seconds']:.1f}s")
                else:
                    print(f"  - {step['id']}: ✗ {step['status']}")
        
        # Mostrar métricas do sistema
        print("\n5. Métricas do sistema:")
        workflow_metrics = agent_coordinator.get_workflow_metrics()
        print(f"  - Total de workflows: {workflow_metrics['overview']['total_workflows']}")
        print(f"  - Taxa de sucesso: {workflow_metrics['performance']['success_rate']:.1f}%")
        print(f"  - Tempo médio de execução: {workflow_metrics['performance']['average_execution_time_seconds']:.1f}s")
    
    finally:
        # Limpar recursos
        await agent_manager.stop()
        await agent_coordinator.stop()


async def exemplo_reconciliacao_dados():
    """Demonstra uso do agente de reconciliação."""
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Reconciliação de Dados")
    print("=" * 60)
    
    # Criar sistema de agentes
    agent_manager, agent_coordinator = create_audit_agent_system()
    
    try:
        # Iniciar sistema
        await agent_manager.start()
        await agent_coordinator.start()
        
        # Criar agente de reconciliação
        await agent_manager.create_agent("ReconcilerAgent", "reconciler_agent")
        await agent_manager.start_agent("reconciler_agent")
        
        # Dados de exemplo com inconsistências propositais
        dataset_exemplo = [
            {
                "id": "1",
                "produto": "Pneu 185/65 R15",
                "ncm": "40111000",
                "cest": "0100100",
                "preco": 250.50,
                "email": "fornecedor1@empresa.com"
            },
            {
                "id": "2", 
                "produto": "PNEU 185/65 R15",  # Variação de formato
                "ncm": "40111000",
                "cest": "0100100",
                "preco": 250.50,
                "email": "fornecedor1empresa.com"  # Email inválido
            },
            {
                "id": "3",
                "produto": "Medicamento Paracetamol",
                "ncm": "30049099",
                "cest": "",  # Campo vazio
                "preco": None,  # Valor nulo
                "email": "farmacia@teste.com"
            }
        ]
        
        print("\n1. Analisando qualidade dos dados...")
        quality_task = AgentTask(
            type="analyze_data_quality",
            data={
                "dataset": dataset_exemplo,
                "dimensions": ["completeness", "accuracy", "consistency", "validity"]
            }
        )
        
        quality_result = await agent_manager.execute_task("reconciler_agent", quality_task)
        print(f"Score geral de qualidade: {quality_result['overall_quality_score']:.2%}")
        print(f"Nota de qualidade: {quality_result['quality_grade']}")
        
        # Mostrar análise por dimensão
        for dimension, analysis in quality_result['quality_analysis'].items():
            print(f"  - {dimension.capitalize()}: {analysis['percentage']:.1f}%")
        
        print("\n2. Detectando inconsistências...")
        inconsistency_task = AgentTask(
            type="detect_inconsistencies",
            data={
                "dataset": dataset_exemplo,
                "rules": {
                    "not_null": ["id", "produto", "ncm"],
                    "unique": ["id"],
                    "ranges": {"preco": {"min": 0, "max": 10000}}
                }
            }
        )
        
        inconsistency_result = await agent_manager.execute_task("reconciler_agent", inconsistency_task)
        total_issues = sum(len(inconsistency_result['inconsistencies'][key]) 
                          for key in inconsistency_result['inconsistencies'])
        print(f"Total de inconsistências encontradas: {total_issues}")
        
        # Mostrar alguns exemplos
        for issue_type, issues in inconsistency_result['inconsistencies'].items():
            if issues:
                print(f"  - {issue_type}: {len(issues)} problemas")
        
        print("\n3. Detectando e mesclando duplicatas...")
        merge_task = AgentTask(
            type="merge_duplicate_records",
            data={
                "dataset": dataset_exemplo,
                "similarity_threshold": 0.8,
                "strategy": "intelligent"
            }
        )
        
        merge_result = await agent_manager.execute_task("reconciler_agent", merge_task)
        print(f"Registros originais: {merge_result['merge_summary']['original_records']}")
        print(f"Grupos de duplicatas: {merge_result['merge_summary']['duplicate_groups_found']}")
        print(f"Registros finais: {merge_result['merge_summary']['final_record_count']}")
        print(f"Redução: {merge_result['merge_summary']['reduction_percentage']:.1f}%")
    
    finally:
        # Limpar recursos
        await agent_manager.stop()
        await agent_coordinator.stop()


async def exemplo_classificacao_rapida():
    """Demonstra função utilitária de classificação rápida."""
    print("\n" + "=" * 60)
    print("EXEMPLO 4: Classificação Rápida (Função Utilitária)")
    print("=" * 60)
    
    produtos_teste = [
        "Pneu radial 205/55 R16 para veículos de passeio",
        "Medicamento Ibuprofeno 600mg comprimidos revestidos",
        "Notebook Dell Inspiron 15 3000 Intel Core i5",
        "Óleo lubrificante SAE 15W40 para motores diesel"
    ]
    
    for i, produto in enumerate(produtos_teste, 1):
        print(f"\n{i}. Classificando: {produto}")
        
        # Usar função utilitária
        resultado = await quick_classify_product(produto, state="SP")
        
        if resultado["success"]:
            summary = resultado["summary"]
            print(f"   NCM: {summary['ncm_code']} (confiança: {summary['ncm_confidence']:.1%})")
            if summary.get('cest_code'):
                print(f"   CEST: {summary['cest_code']} (confiança: {summary['cest_confidence']:.1%})")
            else:
                print("   CEST: Não aplicável")
        else:
            print(f"   Erro: {resultado['error']}")


def mostrar_capacidades_sistema():
    """Mostra as capacidades do sistema de agentes."""
    print("\n" + "=" * 60)
    print("CAPACIDADES DO SISTEMA DE AGENTES")
    print("=" * 60)
    
    capacidades = get_agent_capabilities_summary()
    
    for agent_name, capabilities in capacidades.items():
        print(f"\n{agent_name}:")
        for capability in capabilities:
            print(f"  • {capability}")
    
    print(f"\nTotal de agentes especializados: {len(capacidades)}")
    print(f"Total de capacidades disponíveis: {sum(len(caps) for caps in capacidades.values())}")


async def main():
    """Função principal que executa todos os exemplos."""
    print("SISTEMA DE AGENTES PARA AUDITORIA FISCAL ICMS")
    print("=" * 60)
    print("Demonstração completa do sistema de agentes especializados")
    print("Desenvolvido para automatizar processos de auditoria fiscal\n")
    
    # Mostrar capacidades primeiro
    mostrar_capacidades_sistema()
    
    try:
        # Executar exemplos em sequência
        await exemplo_agentes_individuais()
        await exemplo_workflow_completo()
        await exemplo_reconciliacao_dados()
        await exemplo_classificacao_rapida()
        
        print("\n" + "=" * 60)
        print("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print("Todos os exemplos foram executados corretamente.")
        print("O sistema de agentes está pronto para uso em produção.")
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        print("Verifique os logs para mais detalhes.")
    
    print("\nPara usar o sistema em seus projetos:")
    print("  from src.agents import create_audit_agent_system")
    print("  agent_manager, agent_coordinator = create_audit_agent_system()")


if __name__ == "__main__":
    # Executar exemplos
    asyncio.run(main())
