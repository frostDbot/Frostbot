# 📋 Lista Completa de Comandos do Bot Discord

## 🎯 Comandos de Eventos (Enquete)
**Permissão necessária:** Cargo "Puxadores"

| Comando              | Descrição                                      | Funcionalidade                                                                 | Como usar                                                                 |
|----------------------|-----------------------------------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `/criar_evento_boss` | Criar enquete para eventos de boss            | Modal com limite de jogadores por categoria (TANKER, HEALER, DPS, RESERVA)    | Execute o comando e preencha o formulário                                |
| `/resultado_evento`  | Ver resultados dos últimos eventos            | Lista os 5 eventos mais recentes com participantes                            | Execute e selecione um evento para ver detalhes                          |
| `/deletar_eventos`   | Deletar eventos salvos                        | Lista todos os eventos e permite deletar múltiplos                            | Execute, selecione os eventos e confirme                                 |
| `/limpar_evento`     | Limpar enquetes da memória                    | Remove dados temporários de enquetes ativas                                   | Execute quando houver problemas com botões                               |

---

## 🔧 Comandos de Gerenciamento (Cargos)
**Permissão necessária:** "Gerenciar Cargos"

| Comando                    | Descrição                                 | Funcionalidade                                              | Como usar                                                        |
|----------------------------|-------------------------------------------|--------------------------------------------------------------|------------------------------------------------------------------|
| `/gerenciar_cargos [cargo]` | Gerenciar cargos em múltiplos membros     | Interface para adição/remoção em massa                      | Execute com ou sem o parâmetro para escolher o cargo             |

---

## 🔐 Comandos de Verificação (Novos Membros)
**Permissão necessária:** Administrador

| Comando                          | Descrição                                 | Funcionalidade                                                             | Como usar                                                        |
|----------------------------------|-------------------------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------|
| `/criar_painel_verificacao`     | Criar painel de verificação               | Sistema com nickname e vocação                                             | Execute no canal desejado ou informe um canal                    |
| `/verificar_cargos`             | Verificar existência dos cargos           | Checa se Convidado, EK, MS, RP, ED, MK estão configurados                 | Execute para diagnóstico                                         |
| `/resultado_verificacao`        | Ver lista de membros verificados          | Mostra estatísticas e histórico                                            | Execute para ver o relatório completo                            |

---

## ⚙️ Comandos Administrativos
**Permissão necessária:** Administrador

| Comando           | Descrição                              | Funcionalidade                                      | Como usar                                               |
|-------------------|------------------------------------------|-----------------------------------------------------|---------------------------------------------------------|
| `/sync_comandos`  | Sincronizar comandos slash              | Atualiza comandos quando não aparecem ou falham     | Execute quando comandos não estiverem funcionando       |

---

## 🎮 Sistemas Interativos

### Sistema de Eventos
- Enquetes com botões interativos
- Categorias: 🛡️ TANKER, 🚑 HEALER, ⚔️ DPS, 🔄 RESERVA
- Limite configurável por categoria
- Lista automática de participantes
- Salvamento persistente em JSON

### Sistema de Verificação
- Painel persistente para novos membros
- Processo em 3 etapas:
  1. Definir nickname
  2. Receber cargo "Convidado"
  3. Escolher vocação (EK, MS, RP, ED, MK)

### Sistema de Gerenciamento de Cargos
- Dropdowns para múltipla seleção
- Visualização de membros com/sem cargo
- Ações em massa com confirmação

---

## 📊 Recursos Especiais

- Logging com horário de Brasília  
- Armazenamento persistente em JSON  
- Interface responsiva com feedback visual  
- Verificação de permissões por cargo  
- Views que funcionam após restart do bot  
- Relatórios completos e detalhados  

---

> Todos os comandos usam **slash commands** ( `/` ) e têm verificação de permissões apropriadas.
