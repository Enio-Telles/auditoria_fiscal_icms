#!/bin/bash
echo "Iniciando Sistema de IA para Classificação NCM/CEST"
echo

# Ativar ambiente virtual se existir
if [ -f "venv/bin/activate" ]; then
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar Ollama
echo "Verificando Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "AVISO: Ollama não está rodando"
    echo "Execute: ollama serve"
    echo
fi

# Executar demonstração
echo "Iniciando demonstração..."
python demo_ai_classification.py
