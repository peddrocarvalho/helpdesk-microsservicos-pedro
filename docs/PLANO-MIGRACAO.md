# Plano de Migração — HelpDesk TI

## 1. Objetivo

Transformar a aplicação HelpDesk TI, originalmente desenvolvida como um monólito em Python com FastAPI, em uma arquitetura de microsserviços.

A migração deverá preservar as funcionalidades existentes, a autenticação, as permissões e as regras de negócio.

## 2. Situação inicial

A aplicação original possui:
- Uma única aplicação FastAPI.
- Um banco de dados compartilhado.
- Módulos de usuários, inventário, chamados e notificações.
- Interface web integrada à aplicação.
- Autenticação baseada em JWT.

### Testes da versão original

Antes de iniciar a migração, foram executados os testes automatizados do projeto.

**Resultado:** 36 testes aprovados, nenhum teste falhou.

Tempo de execução: 32,63 segundos.

Foi identificado um aviso de depreciação relacionado à integração entre `httpx` e `starlette.testclient`, sem impacto na aprovação dos testes.

## 3. Arquitetura planejada

A solução será dividida nos seguintes componentes:

- **API Gateway:** ponto único de entrada para as requisições externas.
- **Serviço de Usuários:** gerenciamento de usuários, perfis e dados de autenticação.
- **Serviço de Inventário:** gerenciamento dos ativos e equipamentos.
- **Serviço de Chamados:** abertura, atribuição, acompanhamento e atualização dos chamados.
- **Serviço de Notificações:** tratamento das notificações, integrado conforme a necessidade da arquitetura.

Cada microsserviço terá seu próprio banco de dados e será executado em um contêiner independente.

## 4. Comunicação entre serviços

A comunicação entre os serviços será realizada por HTTP quando houver necessidade de consultar dados ou executar operações em outro serviço.

O serviço de Chamados deverá consultar os serviços de Usuários e Inventário sem acessar diretamente seus bancos de dados.

As chamadas entre serviços deverão possuir timeout e tratamento de falhas, retornando erros claros quando uma dependência estiver indisponível.

## 5. Segurança

A migração deverá preservar:
- Autenticação com JWT.
- Validação dos tokens nos serviços.
- Controle de acesso por perfil.
- Proteção das rotas.
- Encaminhamento do token nas chamadas entre serviços.
- Utilização da variável `JWT_SEGREDO` por meio do arquivo `.env`.

Somente o API Gateway deverá expor uma porta de acesso externo.

## 6. Etapas de implementação

1. Registrar o planejamento e a arquitetura pretendida.
2. Preparar a estrutura do serviço de Usuários.
3. Implementar o microsserviço de Usuários.
4. Adaptar a autenticação para a arquitetura distribuída.
5. Implementar o microsserviço de Inventário.
6. Implementar o microsserviço de Chamados.
7. Implementar o API Gateway.
8. Configurar bancos independentes e Docker Compose.
9. Executar testes de integração e segurança.
10. Atualizar a documentação e preparar a demonstração.

## 7. Critérios de validação

A migração será considerada funcional quando:
- Os serviços puderem ser executados em contêineres independentes.
- Cada serviço utilizar seu próprio banco de dados.
- A comunicação entre serviços ocorrer por APIs, sem acesso direto aos bancos de outros serviços.
- O Gateway funcionar como ponto único de entrada.
- A autenticação e as permissões forem preservadas.
- As funcionalidades originais de chamados, inventário, usuários e notificações continuarem disponíveis.
- Os testes automatizados e os cenários de falha forem validados.

## 8. Registro de evolução

Este documento representa o planejamento inicial da migração.

As decisões de arquitetura, alterações realizadas, testes executados e resultados serão registrados durante o desenvolvimento.
