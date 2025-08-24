# 🏢 Sistema de Auditoria Fiscal ICMS v4.0

## ⚡ INÍCIO RÁPIDO

### 🚀 Para usuários que já têm tudo instalado:
```powershell
# 1. Verificar se está tudo funcionando:
.\verificar_status.ps1

# 2. Se precisar iniciar os serviços:
.\iniciar_banco_dados.ps1
.\iniciar_backend.ps1
.\iniciar_frontend.ps1

# 3. Acessar o sistema:
# http://localhost:3001
# Login: admin@demo.com / admin123
```

### 📦 Para primeira instalação:
```powershell
# Execute o instalador automático:
.\scripts\instalar_sistema_usuario_final.ps1
```

## 📖 DOCUMENTAÇÃO COMPLETA

- **Manual do Usuário:** `MANUAL_USUARIO_FINAL.md`
- **Guia de Deploy:** `GUIA_DEPLOY_LOCAL_WINDOWS.md`

## 🛠️ SCRIPTS PRINCIPAIS

| Script | Função | Frequência |
|--------|--------|------------|
| `verificar_status.ps1` | Diagnóstico rápido | **Diário** ⭐ |
| `manutencao_sistema.ps1` | Limpeza e otimização | **Semanal** ⭐ |
| `iniciar_backend.ps1` | Inicia serviços backend | Conforme necessário |
| `iniciar_frontend.ps1` | Inicia interface web | Conforme necessário |
| `criar_backup_dados.ps1` | Backup dos dados | **Mensal** |
| `reiniciar_sistema_completo.ps1` | Restart completo | Quando houver problemas |

## 🌐 ACESSOS RÁPIDOS

- **🖥️ Sistema Principal:** http://localhost:3001
- **📊 API Docs:** http://localhost:8000/docs
- **💾 Status Backend:** http://localhost:8000/health
- **🤖 Ollama IA:** http://localhost:11434

## 👤 USUÁRIOS PADRÃO

| Tipo | Email | Senha | Permissões |
|------|-------|-------|------------|
| Administrador | admin@demo.com | admin123 | Todas |
| Auditor | auditor@demo.com | auditor123 | Auditoria |
| Operador | operador@demo.com | oper123 | Básicas |

## 🔧 PROBLEMAS?

### 1️⃣ SEMPRE execute primeiro:
```powershell
.\verificar_status.ps1
```

### 2️⃣ Se não resolver:
```powershell
.\reiniciar_sistema_completo.ps1
```

### 3️⃣ Para problemas persistentes:
- Consulte: `MANUAL_USUARIO_FINAL.md` (seção "Solução de Problemas")
- Execute: `.\manutencao_sistema.ps1`

## 📞 SUPORTE

- **📧 Email:** suporte@auditoriafiscal.com
- **📱 WhatsApp:** (11) 99999-9999
- **💬 Teams:** Equipe Auditoria Fiscal
- **🌐 Portal:** https://support.auditoriafiscal.com

---

## 📋 FUNCIONALIDADES

### ✅ Gestão Multi-Tenant
- Múltiplas empresas no mesmo sistema
- Isolamento completo de dados
- Configurações independentes

### ✅ Importação Inteligente
- Planilhas Excel/CSV
- NFe XML
- Sped Fiscal
- Validação automática

### ✅ Classificação com IA
- Reconhecimento automático de produtos
- Sugestões de NCM/CEST
- Aprendizado contínuo
- Validação humana

### ✅ Relatórios e Dashboards
- Dashboard executivo
- Relatórios fiscais
- Gráficos interativos
- Exportação para Excel/PDF

### ✅ Auditoria e Compliance
- Trilha de auditoria
- Controle de versões
- Logs detalhados
- Relatórios de conformidade

---

## 💻 REQUISITOS TÉCNICOS

- **SO:** Windows 10/11
- **RAM:** 8GB (recomendado 16GB)
- **HD:** 20GB livres
- **Internet:** Para modelos de IA

### 📦 Software Necessário:
- Docker Desktop
- Anaconda Python
- Node.js
- Ollama
- Git (opcional)

---

**Sistema de Auditoria Fiscal ICMS v4.0**
*Desenvolvido para Windows 11 - Ambiente 100% Local*

🔒 **Seguro** | 🚀 **Rápido** | 🤖 **Inteligente** | 📊 **Completo**
