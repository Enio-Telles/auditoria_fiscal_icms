# 📋 Manual do Usuário Final - Sistema de Auditoria Fiscal ICMS v4.1

**Status:** 🟢 **Produção Estável** | **Data:** 24 de Agosto de 2025

Bem-vindo! Este manual foi criado para ajudar você a instalar, usar e resolver problemas do Sistema de Auditoria Fiscal de forma rápida e eficiente.

---

## 🚀 Instalação Rápida (Windows)

Siga estes passos para ter o sistema funcionando em minutos.

### 1. Pré-requisitos

Garanta que os seguintes programas estão instalados:

1.  **Docker Desktop:** Essencial para o banco de dados.
    *   [Download aqui](https://www.docker.com/products/docker-desktop/)
2.  **Anaconda Python:** Gerencia o ambiente de IA.
    *   [Download aqui](https://www.anaconda.com/download)
3.  **Node.js:** Necessário para a interface do usuário.
    *   [Download aqui](https://nodejs.org/)
4.  **Ollama:** Executa os modelos de IA localmente.
    *   [Download aqui](https://ollama.ai/download)

### 2. Instalação Automatizada

Com os pré-requisitos instalados, abra o **PowerShell como Administrador** e execute um único comando:

```powershell
# Instala e inicia o sistema completo. Recomendado para o primeiro uso.
.\iniciar_sistema_completo_limpo.ps1
```

**O que este script faz por você:**
*   Verifica se o Docker está ativo.
*   Baixa e configura o banco de dados PostgreSQL.
*   Cria e configura o ambiente Python (`conda`).
*   Instala todas as dependências do backend e frontend.
*   Carrega 20.223 produtos de exemplo no banco de dados.
*   Inicia o backend, o frontend e os agentes de IA.

### 3. Acessando o Sistema

Após a conclusão do script, o sistema estará pronto para uso:

*   **URL de Acesso:** [http://localhost:3000](http://localhost:3000) (ou `http://localhost:3001`)
*   **Usuário:** `admin`
*   **Senha:** `admin123`

---

## 🖥️ Como Usar o Sistema

### Funcionalidades Principais

*   **Dashboard:** Visão geral com estatísticas e atividades recentes.
*   **Empresas:** Cadastre e gerencie as empresas que serão auditadas.
*   **Importação:** Faça o upload de planilhas de produtos (`.xlsx`, `.csv`) para análise.
*   **Classificação:** Use a IA para classificar a NCM/CEST de novos produtos.
*   **Relatórios:** Gere análises de conformidade fiscal.

---

## 🔧 Solução de Problemas (Troubleshooting)

### Diagnóstico Rápido

Se encontrar qualquer problema, o primeiro passo é sempre executar o script de verificação:

```powershell
# Fornece um diagnóstico rápido do estado de cada componente.
.\verificar_status.ps1
```

### Problemas Comuns e Soluções

| Problema | Solução Rápida |
| :--- | :--- |
| 🐌 **Sistema lento ou não responde** | 1. Verifique se o **Docker Desktop** está aberto. <br> 2. Feche todas as janelas e execute `.\reiniciar_sistema_limpo.ps1`. |
| ❗ **Erro de "Porta em uso"** | Reinicie o computador. Outro programa pode estar usando as portas `3000`, `8000` ou `5432`. |
| 🤖 **IA não classifica os produtos** | Verifique se o aplicativo **Ollama** está rodando no seu sistema. |
| 🔑 **Login inválido** | Confirme que o backend está ativo com `.\verificar_status.ps1` e use as credenciais `admin` / `admin123`. |

### ✅ Correções Implementadas na v4.1

Os seguintes problemas foram **resolvidos** e não devem mais ocorrer:
*   **Dashboard com dados simulados:** Agora exibe dados reais do banco.
*   **"Erro ao testar conexão" na importação:** A comunicação com o backend foi corrigida.
*   **Scripts com erros de sintaxe:** As versões `*_limpo.ps1` garantem execução sem falhas.
*   **Endpoints não encontrados (404):** Todas as rotas da API foram alinhadas.

---

## 📞 Suporte

*   **Logs de Erro:** Para análises detalhadas, os logs estão na pasta `\logs`.
*   **Documentação Técnica:** A pasta `\docs` contém diagramas e detalhes da arquitetura.
*   **Contato:** Se o problema persistir, contate a equipe de suporte técnico.
