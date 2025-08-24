# Servidor API Mock para Sistema de Agentes
# Execute com: python mock_agents_api.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time
from datetime import datetime
import sys
import os

# Adicionar o diretório atual ao path para importar mock_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mock_data import (
        get_mock_data,
        generate_agent,
        generate_task,
        generate_workflow,
        generate_system_metrics,
        generate_id,
        AGENT_TYPES,
    )
except ImportError:
    print("Erro: Não foi possível importar mock_data.py")
    print("Certifique-se de que o arquivo mock_data.py existe no mesmo diretório")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Permite CORS para desenvolvimento

# Dados simulados em memória
mock_data = get_mock_data()

# Simulação de delay de rede (opcional)
SIMULATE_DELAY = True
MAX_DELAY = 0.5  # segundos


def simulate_network_delay():
    if SIMULATE_DELAY:
        time.sleep(random.uniform(0.1, MAX_DELAY))


@app.route("/agents/status", methods=["GET"])
def get_system_status():
    simulate_network_delay()

    running_agents = len([a for a in mock_data["agents"] if a["status"] == "running"])
    total_agents = len(mock_data["agents"])

    if running_agents > total_agents * 0.8:
        status = "healthy"
        message = "Sistema funcionando normalmente"
    elif running_agents > total_agents * 0.5:
        status = "degraded"
        message = "Sistema com performance reduzida"
    else:
        status = "unhealthy"
        message = "Sistema com problemas críticos"

    return jsonify({"status": status, "message": message})


@app.route("/agents/metrics", methods=["GET"])
def get_system_metrics():
    simulate_network_delay()

    # Atualizar métricas com dados atuais
    metrics = generate_system_metrics()

    # Usar dados reais dos agentes mockados
    total_agents = len(mock_data["agents"])
    running_agents = len([a for a in mock_data["agents"] if a["status"] == "running"])
    idle_agents = len([a for a in mock_data["agents"] if a["status"] == "idle"])
    error_agents = len([a for a in mock_data["agents"] if a["status"] == "error"])

    metrics["agent_metrics"].update(
        {
            "total_agents": total_agents,
            "running_agents": running_agents,
            "idle_agents": idle_agents,
            "error_agents": error_agents,
        }
    )

    mock_data["system_metrics"] = metrics
    return jsonify(metrics)


@app.route("/agents", methods=["GET"])
def get_agents():
    simulate_network_delay()
    return jsonify(mock_data["agents"])


@app.route("/agents", methods=["POST"])
def create_agent():
    simulate_network_delay()

    data = request.get_json()
    agent_type = data.get("agent_type")
    config = data.get("config", {})

    if agent_type not in AGENT_TYPES:
        return jsonify({"error": "Tipo de agente inválido"}), 400

    # Criar novo agente
    new_agent = generate_agent()
    new_agent["type"] = agent_type
    new_agent["name"] = config.get("name", f"{agent_type.lower()}_{new_agent['id']}")
    new_agent["config"].update(config)
    new_agent["status"] = "idle"  # Agente criado mas não iniciado

    mock_data["agents"].append(new_agent)

    return jsonify(new_agent), 201


@app.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    return jsonify(agent)


@app.route("/agents/<agent_id>/start", methods=["POST"])
def start_agent(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    agent["status"] = "running"
    agent["last_heartbeat"] = datetime.now().isoformat()

    return jsonify({"success": True, "message": "Agente iniciado com sucesso"})


@app.route("/agents/<agent_id>/stop", methods=["POST"])
def stop_agent(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    agent["status"] = "stopped"
    agent["last_heartbeat"] = datetime.now().isoformat()

    return jsonify({"success": True, "message": "Agente parado com sucesso"})


@app.route("/agents/<agent_id>/restart", methods=["POST"])
def restart_agent(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    # Simular restart
    agent["status"] = "running"
    agent["last_heartbeat"] = datetime.now().isoformat()
    agent["metrics"]["uptime_seconds"] = 0  # Reset uptime

    return jsonify({"success": True, "message": "Agente reiniciado com sucesso"})


@app.route("/agents/<agent_id>", methods=["DELETE"])
def remove_agent(agent_id):
    simulate_network_delay()

    agent_index = next(
        (i for i, a in enumerate(mock_data["agents"]) if a["id"] == agent_id), None
    )
    if agent_index is None:
        return jsonify({"error": "Agente não encontrado"}), 404

    # Remover agente
    mock_data["agents"].pop(agent_index)

    # Remover tarefas do agente
    mock_data["tasks"] = [t for t in mock_data["tasks"] if t["agent_id"] != agent_id]

    return jsonify({"success": True, "message": "Agente removido com sucesso"})


@app.route("/agents/<agent_id>/config", methods=["PUT"])
def update_agent_config(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    new_config = request.get_json()
    agent["config"].update(new_config)

    return jsonify(agent)


@app.route("/agents/<agent_id>/execute", methods=["POST"])
def execute_task(agent_id):
    simulate_network_delay()

    agent = next((a for a in mock_data["agents"] if a["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agente não encontrado"}), 404

    data = request.get_json()
    task_type = data.get("task_type")
    task_data = data.get("data", {})

    # Criar nova tarefa
    new_task = generate_task(agent_id)
    new_task["type"] = task_type
    new_task["data"] = task_data
    new_task["status"] = "pending"

    mock_data["tasks"].append(new_task)

    return jsonify(new_task), 201


@app.route("/agents/tasks", methods=["GET"])
def get_all_tasks():
    simulate_network_delay()

    # Ordenar por data de criação (mais recentes primeiro)
    sorted_tasks = sorted(
        mock_data["tasks"], key=lambda x: x["created_at"], reverse=True
    )

    return jsonify(sorted_tasks)


@app.route("/agents/<agent_id>/tasks", methods=["GET"])
def get_agent_tasks(agent_id):
    simulate_network_delay()

    agent_tasks = [t for t in mock_data["tasks"] if t["agent_id"] == agent_id]
    sorted_tasks = sorted(agent_tasks, key=lambda x: x["created_at"], reverse=True)

    return jsonify(sorted_tasks)


@app.route("/agents/tasks/<task_id>", methods=["GET"])
def get_task_result(task_id):
    simulate_network_delay()

    task = next((t for t in mock_data["tasks"] if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404

    return jsonify(task)


@app.route("/agents/workflows", methods=["GET"])
def get_workflows():
    simulate_network_delay()
    return jsonify(mock_data["workflows"])


@app.route("/agents/workflows", methods=["POST"])
def create_workflow():
    simulate_network_delay()

    data = request.get_json()
    name = data.get("name")
    steps = data.get("steps", [])

    new_workflow = generate_workflow()
    new_workflow["name"] = name
    new_workflow["total_steps"] = len(steps)
    new_workflow["steps"] = steps
    new_workflow["status"] = "idle"

    mock_data["workflows"].append(new_workflow)

    return jsonify(new_workflow), 201


@app.route("/agents/workflows/<workflow_id>", methods=["GET"])
def get_workflow(workflow_id):
    simulate_network_delay()

    workflow = next((w for w in mock_data["workflows"] if w["id"] == workflow_id), None)
    if not workflow:
        return jsonify({"error": "Workflow não encontrado"}), 404

    return jsonify(workflow)


@app.route("/agents/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    simulate_network_delay()

    workflow = next((w for w in mock_data["workflows"] if w["id"] == workflow_id), None)
    if not workflow:
        return jsonify({"error": "Workflow não encontrado"}), 404

    context = request.get_json()

    # Simular execução
    workflow["status"] = "running"
    workflow["started_at"] = datetime.now().isoformat()
    workflow["context"] = context
    execution_id = generate_id()

    return jsonify({"workflow_id": workflow_id, "execution_id": execution_id})


@app.route("/agents/workflows/<workflow_id>/pause", methods=["POST"])
def pause_workflow(workflow_id):
    simulate_network_delay()

    workflow = next((w for w in mock_data["workflows"] if w["id"] == workflow_id), None)
    if not workflow:
        return jsonify({"error": "Workflow não encontrado"}), 404

    workflow["status"] = "paused"

    return jsonify({"success": True, "message": "Workflow pausado"})


@app.route("/agents/workflows/<workflow_id>/resume", methods=["POST"])
def resume_workflow(workflow_id):
    simulate_network_delay()

    workflow = next((w for w in mock_data["workflows"] if w["id"] == workflow_id), None)
    if not workflow:
        return jsonify({"error": "Workflow não encontrado"}), 404

    workflow["status"] = "running"

    return jsonify({"success": True, "message": "Workflow retomado"})


@app.route("/agents/workflows/<workflow_id>/cancel", methods=["POST"])
def cancel_workflow(workflow_id):
    simulate_network_delay()

    workflow = next((w for w in mock_data["workflows"] if w["id"] == workflow_id), None)
    if not workflow:
        return jsonify({"error": "Workflow não encontrado"}), 404

    workflow["status"] = "failed"
    workflow["error_message"] = "Workflow cancelado pelo usuário"

    return jsonify({"success": True, "message": "Workflow cancelado"})


@app.route("/agents/quick-classify", methods=["POST"])
def quick_classify():
    simulate_network_delay()

    data = request.get_json()
    description = data.get("description", "")
    # state não utilizado (mantido no payload para futura lógica)

    # Simular classificação
    time.sleep(1)  # Simular processamento

    # Gerar resultado simulado baseado na descrição
    if "pneu" in description.lower():
        ncm_code = "40111000"
        ncm_description = "Pneus novos de borracha"
        cest_code = "0100300"
        cest_description = "Pneus e câmaras de ar"
        confidence = 0.92
    elif "notebook" in description.lower() or "computador" in description.lower():
        ncm_code = "84713012"
        ncm_description = "Máquinas automáticas para processamento de dados portáteis"
        cest_code = "1600100"
        cest_description = "Equipamentos de informática"
        confidence = 0.89
    else:
        ncm_code = "99999999"
        ncm_description = "Classificação simulada"
        cest_code = "9999999"
        cest_description = "CEST simulado"
        confidence = 0.75

    result = {
        "success": True,
        "summary": {
            "ncm_code": ncm_code,
            "ncm_description": ncm_description,
            "cest_code": cest_code,
            "cest_description": cest_description,
            "confidence": confidence,
            "st_required": random.choice([True, False]),
        },
        "details": {
            "expansion_result": {
                "expanded_description": f"Descrição expandida: {description}",
                "technical_features": ["característica 1", "característica 2"],
            },
            "ncm_result": {
                "classification_method": "direct",
                "alternatives": [ncm_code],
            },
            "cest_result": {
                "classification_method": "mapping",
                "st_analysis": {"required": random.choice([True, False])},
            },
            "processing_time": round(random.uniform(0.8, 2.5), 2),
            "agent_info": {
                "agents_used": ["ExpansionAgent", "NCMAgent", "CESTAgent"],
                "workflow_id": generate_id(),
            },
        },
        "errors": (
            []
            if random.random() > 0.1
            else ["Aviso: Classificação com baixa confiança"]
        ),
        "workflow_id": generate_id(),
    }

    return jsonify(result)


@app.route("/agents/health", methods=["GET"])
def health_check():
    simulate_network_delay()

    agents_status = {}
    for agent in mock_data["agents"]:
        agents_status[agent["name"]] = agent["status"]

    overall_status = "healthy"
    if any(status == "error" for status in agents_status.values()):
        overall_status = "degraded"

    return jsonify({"status": overall_status, "agents": agents_status})


@app.route("/agents/initialize", methods=["POST"])
def initialize_system():
    simulate_network_delay()

    # Simular inicialização do sistema
    for agent in mock_data["agents"]:
        if agent["status"] == "stopped":
            agent["status"] = "idle"

    return jsonify(
        {"success": True, "message": "Sistema de agentes inicializado com sucesso"}
    )


@app.route("/agents/shutdown", methods=["POST"])
def shutdown_system():
    simulate_network_delay()

    # Simular shutdown do sistema
    for agent in mock_data["agents"]:
        if agent["status"] != "stopped":
            agent["status"] = "stopped"

    return jsonify(
        {"success": True, "message": "Sistema de agentes desligado com sucesso"}
    )


# Endpoint para reinicializar dados mock (útil para desenvolvimento)
@app.route("/agents/mock/reset", methods=["POST"])
def reset_mock_data():
    global mock_data
    mock_data = get_mock_data()
    return jsonify({"success": True, "message": "Dados mock reinicializados"})


if __name__ == "__main__":
    print("🤖 Iniciando API Mock do Sistema de Agentes...")
    print("📡 Servidor disponível em: http://localhost:8007")
    print("📋 Endpoints disponíveis:")
    print("   GET  /agents/status")
    print("   GET  /agents/metrics")
    print("   GET  /agents")
    print("   POST /agents")
    print("   POST /agents/quick-classify")
    print("   GET  /agents/workflows")
    print("   POST /agents/mock/reset")
    print("\n🔄 Para resetar os dados mock, use: POST /agents/mock/reset")
    print("⏱️  Delay de rede simulado:", "Ativado" if SIMULATE_DELAY else "Desativado")

    app.run(host="0.0.0.0", port=8007, debug=True)
