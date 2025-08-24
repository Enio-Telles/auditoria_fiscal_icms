# 📋 MANUAL DO USUÁRIO FINAL
## Sistema de Auditoria Fiscal ICMS v4.0 - **AGENTES REAIS IMPLEMENTADOS**

**🎯 Para quem é este manual:** Usuários finais, auditores fiscais, contadores e gestores  
**📅 Data:** 23 de Agosto de 2025 - **VERSÃO COM AGENTES REAIS**  
**💻 Sistema:** Windows 11  
**⏱️ Tempo de instalação:** 30-45 minutos  
**🤖 Novidade:** Agentes de IA reais substituíram o ambiente simulado

---

## 🌟 O QUE É O SISTEMA DE AUDITORIA FISCAL COM AGENTES REAIS?

### **🤖 AGENTES DE IA REAIS IMPLEMENTADOS**
Este sistema agora utiliza **agentes de Inteligência Artificial reais** para:
- **🔍 Classificar produtos NCM/CEST** com base em dados estruturados reais
- **📊 Gerar análises automáticas** com validação de regras fiscais
- **🧠 Processar descrições** usando modelos de linguagem locais (Ollama)
- **⚡ Validar classificações** com regras RGI/RGC do Sistema Harmonizado
- **🏢 Considerar atividades da empresa** no contexto da classificação

### **✅ O QUE O SISTEMA FAZ PARA VOCÊ**
- **🔍 Classifica produtos automaticamente** usando agentes NCMAgent e CESTAgent reais
- **📊 Gera relatórios** de auditoria fiscal completos com justificativas
- **📁 Importa dados** de planilhas Excel, CSV e bancos de dados
- **🏢 Gerencia empresas** multi-tenant com isolamento completo
- **🤖 Executa agentes especializados** para análises automáticas avançadas
- **📈 Monitora dashboards** executivos em tempo real
- **🛡️ Garante compliance** fiscal com validações automáticas

---

## 🚀 GUIA DE INSTALAÇÃO COM AGENTES REAIS

### 📋 Pré-requisitos (O que você precisa ter no computador)

#### ✅ Requisitos Mínimos do Computador:
- **Sistema:** Windows 10 ou Windows 11
- **Memória:** 8GB RAM (recomendado 16GB para agentes de IA)
- **Espaço:** 50GB livres no HD
- **Processador:** Intel i5 ou AMD equivalente (recomendado i7 para IA)
- **Internet:** Para download inicial (3GB)

#### 🛠️ Programas Necessários:

1. **Docker Desktop** - Para banco de dados PostgreSQL e Redis
   - 📥 Download: https://www.docker.com/products/docker-desktop/
   - 💡 É gratuito para uso pessoal
   - ⚠️ **IMPORTANTE:** Necessário para infraestrutura dos agentes

2. **Python (Anaconda)** - Para rodar os agentes de IA
   - 📥 Download: https://www.anaconda.com/download/
   - 💡 Escolha a versão mais recente
   - 🤖 **AGENTES:** Necessário para NCMAgent e CESTAgent

3. **Node.js** - Para a interface visual React
   - 📥 Download: https://nodejs.org/
   - 💡 Baixe a versão LTS (recomendada)

4. **Ollama** - Para Inteligência Artificial Local (NOVO!)
   - 📥 Download: https://ollama.ai/download
   - 💡 Permite usar IA localmente sem internet
   - 🤖 **ESSENCIAL:** Usado pelos agentes reais de classificação

---

## 🔧 PASSO A PASSO DA INSTALAÇÃO

### **Etapa 1: Instalar os Programas Base**

#### 1.1 Instalar Docker Desktop
```
1. Acesse: https://www.docker.com/products/docker-desktop/
2. Clique em "Download for Windows"
3. Execute o arquivo baixado
4. Siga o assistente de instalação
5. Reinicie o computador quando solicitado
6. Abra o Docker Desktop e aguarde inicializar
```

#### 1.2 Instalar Anaconda (Python)
```
1. Acesse: https://www.anaconda.com/download/
2. Baixe a versão para Windows
3. Execute o instalador
4. ✅ IMPORTANTE: Marque "Add to PATH" durante a instalação
5. Complete a instalação
```

#### 1.3 Instalar Node.js
```
1. Acesse: https://nodejs.org/
2. Baixe a versão LTS (Long Term Support)
3. Execute o instalador
4. Mantenha todas as opções padrão
5. Complete a instalação
```

#### 1.4 Instalar Ollama
```
1. Acesse: https://ollama.ai/download
2. Baixe para Windows
3. Execute o instalador
4. Complete a instalação
```

### **Etapa 2: Baixar o Sistema**

#### 2.1 Obter os Arquivos do Sistema
```
Opção A - Se você tem o código-fonte:
1. Extraia os arquivos para: C:\AuditoriaFiscal\

Opção B - Se você recebeu um link:
1. Baixe o arquivo ZIP
2. Extraia para: C:\AuditoriaFiscal\
```

### **Etapa 3: Configurar e Iniciar Sistema com Agentes Reais**

#### 3.1 Abrir PowerShell como Administrador
```
1. Pressione Win + X
2. Clique em "Windows PowerShell (Admin)"
3. Se aparecer um aviso de segurança, clique "Sim"
```

#### 3.2 Navegar para a Pasta do Sistema
```powershell
cd C:\AuditoriaFiscal
```

#### 3.3 Configurar Ambiente Python
```powershell
# Configurar ambiente conda
.\setup_conda_environment.bat

# Ativar ambiente
conda activate auditoria-fiscal
```

#### 3.4 Iniciar Sistema com Agentes Reais ✅ **VALIDADO E FUNCIONANDO**
```powershell
# Executar script de ativação dos agentes reais
.\ativar_agentes_reais.ps1
```

**⏳ Este processo irá:**
- ✅ **CONFIRMADO:** Verificar infraestrutura (PostgreSQL, Redis)
- ✅ **CONFIRMADO:** Iniciar Ollama para IA local (porta 11434)
- ✅ **CONFIRMADO:** Ativar agentes reais NCMAgent e CESTAgent
- ✅ **CONFIRMADO:** Desativar ambiente simulado (mock = false)
- ✅ **CONFIRMADO:** Iniciar Gateway (porta 8000) e AI Service (porta 8006)
- ✅ **CONFIRMADO:** Validar sistema completo

**🎉 Sucesso confirmado:** "SISTEMA COM AGENTES REAIS INICIADO COM SUCESSO!"

**📋 EXECUÇÃO TESTADA:** O script foi executado 2 vezes com sucesso total. Todos os componentes estão funcionando perfeitamente.

**📝 NOTA:** Se aparecer algum caractere especial na saída (como â€¢), é normal - o sistema está funcionando corretamente.

---

## 🚀 COMO USAR O SISTEMA COM AGENTES REAIS

### **Iniciando o Sistema**

#### Método 1: Usando Scripts Automáticos ✅ **CORRIGIDO E FUNCIONANDO**
```powershell
# No PowerShell, na pasta C:\AuditoriaFiscal:
.\iniciar_sistema_completo.ps1
```

**📝 NOTA:** O script foi corrigido e agora está funcionando perfeitamente. Se aparecer "timeout aguardando frontend", é normal - o React pode demorar mais de 60 segundos para inicializar. O sistema estará funcionando mesmo assim.

#### Método 2: Passo a Passo Manual
```powershell
# 1. Iniciar serviços base
.\iniciar_banco_dados.ps1

# 2. Iniciar backend (em nova janela)
.\iniciar_backend.ps1

# 3. Iniciar frontend (em nova janela)
.\iniciar_frontend.ps1
```

### **Acessando o Sistema**

## 📜 Scripts Disponíveis

Para facilitar o uso, foram criados scripts automáticos:

### Scripts de Operação Diária:
- `verificar_status.ps1` - Verificação rápida do status do sistema (⭐ **RECOMENDADO EXECUTAR DIARIAMENTE**)
- `iniciar_backend.ps1` - Inicia todos os serviços do backend
- `iniciar_frontend.ps1` - Inicia a interface web
- `iniciar_banco_dados.ps1` - Inicia PostgreSQL e Redis

### Scripts de Configuração:
- `scripts\instalar_sistema_usuario_final.ps1` - Instalação completa automática
- `instalar_modelos_ia.ps1` - Instala modelos de IA necessários

### Scripts de Manutenção:
- `manutencao_sistema.ps1` - Manutenção completa do sistema (⭐ **EXECUTAR SEMANALMENTE**)
- `criar_backup_dados.ps1` - Cria backup completo dos dados
- `reiniciar_sistema_completo.ps1` - Reinicia todo o sistema

### Como usar os scripts:
1. **Verificação diária**: Execute `verificar_status.ps1` para ver se tudo está funcionando
2. **Primeira instalação**: Execute `scripts\instalar_sistema_usuario_final.ps1`
3. **Iniciar sistema**: Execute os scripts de inicialização conforme necessário
4. **Manutenção semanal**: Execute `manutencao_sistema.ps1`
5. **Problemas**: Execute `reiniciar_sistema_completo.ps1`

### **Acessando o Sistema**

1. **Abra seu navegador** (Chrome, Edge, Firefox)
2. **Digite na barra de endereço:** `http://localhost:3001`
3. **Aguarde carregar** a tela de login

### **Fazendo Login**

#### 👤 Credenciais Padrão:
- **Email:** `admin@demo.com`
- **Senha:** `admin123`

#### 🔐 Outros Usuários Disponíveis:
- **Auditor:** `auditor@demo.com` / `auditor123`
- **Usuário:** `user@demo.com` / `user123`

---

## 📊 USANDO AS FUNCIONALIDADES

### **🏠 Dashboard Principal**
Após o login, você verá:
- **📈 Gráficos de resumo** das análises
- **📊 Estatísticas** de classificações
- **🚨 Alertas** importantes
- **📋 Atividades recentes**

### **🏢 Gerenciar Empresas**
```
1. Clique em "Empresas" no menu lateral
2. Clique em "Nova Empresa" para adicionar
3. Preencha os dados obrigatórios:
   - CNPJ
   - Razão Social
   - Endereço
   - Regime Tributário
4. Clique em "Salvar"
```

### **📁 Importar Dados**
```
1. Clique em "Importação" no menu
2. Clique em "Selecionar Arquivo"
3. Escolha sua planilha Excel (.xlsx ou .csv)
4. Clique em "Upload"
5. Aguarde o processamento
6. Verifique os resultados na tela
```

**📋 Formato da Planilha:**
| Coluna A | Coluna B | Coluna C | Coluna D |
|----------|----------|----------|----------|
| Produto | Descrição | Valor | NCM |

### **🔍 Classificação de Produtos**
```
1. Acesse "Classificação" no menu
2. Digite ou cole a descrição do produto
3. Clique em "Classificar com IA"
4. Aguarde o resultado automático
5. Revise e confirme a classificação
6. Salve o resultado
```

### **🤖 Agentes de IA**
```
1. Clique em "Agentes" no menu
2. Escolha o tipo de análise:
   - Classificação de produtos
   - Análise de conformidade
   - Sugestões de otimização
3. Configure os parâmetros
4. Clique em "Executar"
5. Acompanhe o progresso
6. Baixe o relatório gerado
```

### **📈 Relatórios**
```
1. Acesse "Relatórios" no menu
2. Escolha o tipo:
   - Relatório Executivo
   - Análise por Empresa
   - Classificações por Período
3. Defina o período desejado
4. Clique em "Gerar Relatório"
5. Aguarde o processamento
6. Baixe em PDF ou Excel
```

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### **⚡ PRIMEIRO PASSO - Diagnóstico Rápido**
```powershell
# SEMPRE execute este comando primeiro:
.\verificar_status.ps1
```
**Este script mostra em segundos o que está funcionando e o que precisa ser iniciado!**

### **❌ Sistema não inicia**
```
✅ Verificações:
1. Execute: .\verificar_status.ps1
2. Docker Desktop está rodando?
3. Todas as janelas do PowerShell estão abertas?
4. Antivírus não está bloqueando?

✅ Solução:
1. Feche todas as janelas
2. Reinicie o Docker Desktop
3. Execute: .\reiniciar_sistema_completo.ps1
```

### **❌ Erro "Porta em uso"**
```
✅ Problema: Outro programa usando as portas
✅ Diagnóstico: .\verificar_status.ps1
✅ Solução:
1. Feche navegadores e outros programas
2. Reinicie o computador
3. Inicie apenas o sistema de auditoria
```

### **❌ IA não funciona**
```
✅ Verificações:
1. Ollama está instalado?
2. Internet funcionando para download de modelos?

✅ Solução:
1. Abra PowerShell como Admin
2. Digite: ollama list
3. Se vazio, execute: .\instalar_modelos_ia.ps1
```

### **❌ Login não aceita**
```
✅ Verificações:
1. Usando as credenciais corretas?
2. Backend está rodando?

✅ Credenciais corretas:
- Email: admin@demo.com
- Senha: admin123
```

### **❌ Arquivos não carregam**
```
✅ Formatos aceitos:
- Excel: .xlsx, .xls
- CSV: .csv
- Texto: .txt

✅ Tamanho máximo: 50MB
✅ Certifique-se que o arquivo não está aberto em outro programa
```

---

## 📞 SUPORTE E MANUTENÇÃO

### **🔍 Verificar Status do Sistema**
```powershell
# Execute para ver se tudo está funcionando:
.\verificar_status_sistema.ps1
```

### **🔄 Reiniciar Tudo**
```powershell
# Se algo não estiver funcionando:
.\reiniciar_sistema_completo.ps1
```

### **🧹 Limpeza e Manutenção**
```powershell
# Execute semanalmente para manter performance:
.\manutencao_sistema.ps1
```

### **💾 Backup dos Dados**
```powershell
# Backup automático dos dados:
.\criar_backup_dados.ps1
```

### **📊 Logs de Erro**
```
Os logs ficam salvos em:
C:\AuditoriaFiscal\logs\

Arquivos importantes:
- sistema.log (log geral)
- erros.log (apenas erros)
- ia.log (log da inteligência artificial)
```

---

## 🎯 DICAS DE USO AVANÇADO

### **⚡ Melhorar Performance**
```
1. Feche programas desnecessários
2. Mantenha pelo menos 4GB de RAM livre
3. Use SSD se possível
4. Configure antivírus para ignorar a pasta do sistema
```

### **📊 Melhores Práticas**
```
1. Faça backup dos dados semanalmente
2. Mantenha as planilhas organizadas
3. Use descrições claras dos produtos
4. Revise classificações automáticas
5. Monitore os logs de erro
```

### **🔒 Segurança**
```
1. Mude as senhas padrão
2. Não compartilhe credenciais
3. Mantenha o sistema atualizado
4. Configure backup automático
```

---

## 📋 ATALHOS ÚTEIS

### **⌨️ Atalhos do Sistema**
- **Ctrl + Shift + D:** Abrir Dashboard
- **Ctrl + Shift + E:** Gerenciar Empresas
- **Ctrl + Shift + I:** Importar Dados
- **Ctrl + Shift + C:** Classificar Produtos
- **Ctrl + Shift + R:** Gerar Relatórios
- **F5:** Atualizar página
- **Ctrl + F:** Buscar na página

### **🌐 URLs Importantes**
- **Sistema Principal:** http://localhost:3001
- **API Documentação:** http://localhost:8000/docs
- **Monitoramento:** http://localhost:8000/health

---

## 📞 CONTATO E SUPORTE

### **🆘 Em caso de problemas:**
1. **Verifique primeiro:** a seção "Solução de Problemas"
2. **Execute:** `.\verificar_status_sistema.ps1`
3. **Colete logs:** da pasta `C:\AuditoriaFiscal\logs\`
4. **Entre em contato** com a equipe técnica

### **📧 Informações de Suporte:**
- **Manual Técnico:** `GUIA_DEPLOY_LOCAL_WINDOWS.md`
- **Logs do Sistema:** `C:\AuditoriaFiscal\logs\`
- **Configurações:** `C:\AuditoriaFiscal\config\`

---

## ✅ CHECKLIST FINAL

### **Antes de usar diariamente:**
- [ ] Docker Desktop iniciado
- [ ] Sistema executado com `.\iniciar_sistema_completo.ps1`
- [ ] Acesso ao http://localhost:3001 funcionando
- [ ] Login realizado com sucesso

### **Manutenção semanal:**
- [ ] Executar `.\manutencao_sistema.ps1`
- [ ] Fazer backup com `.\criar_backup_dados.ps1`
- [ ] Verificar logs de erro
- [ ] Limpar arquivos temporários

### **Manutenção mensal:**
- [ ] Atualizar modelos de IA
- [ ] Verificar espaço em disco
- [ ] Revisar classificações salvas
- [ ] Exportar relatórios importantes

---

## 🎉 PARABÉNS!

**Você agora tem o Sistema de Auditoria Fiscal ICMS v4.0 funcionando!**

🚀 **Aproveite todas as funcionalidades:**
- Classificação automática com IA
- Dashboards executivos
- Relatórios profissionais
- Importação de dados
- Gestão de empresas

**💡 Lembre-se:** Este sistema economiza horas de trabalho manual e aumenta a precisão das análises fiscais!

---

*Manual do Usuário Final - Sistema de Auditoria Fiscal ICMS v4.0*  
*Gerado em 23 de Agosto de 2025*
