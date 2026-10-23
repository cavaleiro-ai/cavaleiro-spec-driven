[English](README.md) · **Português (Brasil)**

<a id="top"></a>

<p align="center">
  <img src="docs/assets/cavaleiro-banner.svg" alt="Cavaleiro Spec Driven — desenvolvimento guiado por especificação para agentes de código com IA" width="100%"/>
</p>

<h1 align="center">Cavaleiro Spec Driven</h1>

<p align="center">
  <em>Construa a partir de uma especificação, corrija um bug ou avalie uma ideia — com o seu agente de código.</em>
</p>

<p align="center">
  <a href="https://github.com/cavaleiro-ai/cavaleiro-spec-driven/actions/workflows/test.yml"><img src="https://github.com/cavaleiro-ai/cavaleiro-spec-driven/actions/workflows/test.yml/badge.svg" alt="Testes"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue" alt="Licença MIT"/></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/vers%C3%A3o-1.0.0-informational" alt="Versão 1.0.0"/></a>
</p>

O Cavaleiro Spec Driven é um kit de ferramentas que dá aos agentes de código com IA processos estruturados, templates reutilizáveis e resultados documentados. Você instala a CLI `specify`, prepara um projeto para o seu agente e executa processos como o Desenvolvimento Guiado por Especificação (*Spec-Driven Development*, SDD) por meio de *skills* do agente, como `/speckit-specify` e `/speckit-plan`.

O Cavaleiro Spec Driven é mantido pela [Cavaleiro AI](https://github.com/cavaleiro-ai). Ele mantém todos os recursos do projeto original (veja [Licença](#licenca)), acrescenta correções verificadas de segurança, robustez e Windows, e mantém todos os nomes de comandos, a estrutura de arquivos e o nome do pacote compatíveis com o projeto original.

- [O que o Cavaleiro Spec Driven acrescenta](#o-que-o-cavaleiro-spec-driven-acrescenta)
- [Instalação](#instalacao)
- [Escolha o seu processo](#escolha-o-seu-processo)
- [Compatibilidade](#compatibilidade)
- [Documentação](#documentacao)
- [Licença](#licenca)

## O que o Cavaleiro Spec Driven acrescenta

Tudo o que o projeto original tem no commit `c6a4c18`, mais o que está abaixo. Detalhes e evidências estão no [changelog](CHANGELOG.md#cavaleiro-spec-driven-100--2026-10-17) e no [relatório de engenharia](docs/cavaleiro/ENGINEERING.md), em inglês.

- **Arquivos compactados mais seguros.**
  - Um tar.gz minúsculo não consegue mais alocar gigabytes de memória.
  - Uma cadeia de cabeçalhos estendidos não derruba mais a CLI com `RecursionError`.
  - Downloads menores que o `Content-Length` declarado são rejeitados, em vez de instalados pela metade.
- **Erros de rede claros.** Conexões reiniciadas, tempo esgotado e leituras incompletas agora mostram uma mensagem de erro em vez de um *traceback*. Isso vale para `extension add --from`, `preset add --from` e a leitura de catálogos.
- **Um `specify init` mais amigável.**
  - Uma inicialização que falha não deixa mais uma pasta pela metade, que bloqueava a nova tentativa.
  - `init --here --force` preserva o seu `feature_numbering`.
  - Mensagens com `[colchetes]` aparecem como foram escritas.
- **Correções para Windows.**
  - Os scripts PowerShell funcionam em caminhos com `[` e `]`.
  - `specify self upgrade` reconhece instalações feitas com `uv tool` (em `%APPDATA%\uv\tools`).
- **Correção de um bug do projeto original.** Um `GIT_BRANCH_NAME` que aponta para a branch atual não quebra mais toda execução de `/speckit-specify` (issue #5003 do projeto original). A correção vale para Bash, PowerShell e Python.
- **Atualizações que respeitam o fork.** A variável opcional `SPECIFY_UPGRADE_REPOSITORY=dono/repo` faz o `specify self check` e o `self upgrade` seguirem um fork, em vez de substituí-lo em silêncio pela versão do projeto original.
- **Documentação em português:** este README e um [guia completo](docs/cavaleiro/GUIA-PT-BR.md).
- **Segurança do fork.** Os workflows de publicação, deploy e bots do projeto original foram movidos para [`.github/workflows-disabled/`](.github/workflows-disabled/README.md), onde não rodam.

<a id="instalacao"></a>
<a id="install"></a>

## Instalação

Você precisa do **Python 3.11+**, do **[uv](https://docs.astral.sh/uv/)** (ou pipx) e de um agente de código com IA compatível, no Linux, macOS ou Windows. O Git é opcional e só é necessário para a extensão git.

Instale o Cavaleiro Spec Driven a partir deste repositório e crie um projeto:

```bash
uv tool install specify-cli --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git
specify init meu-projeto --integration copilot
cd meu-projeto
```

Os mesmos comandos funcionam no Windows PowerShell. No modo interativo, o `specify init` pergunta qual variante de script instalar. Sem interação, ele usa PowerShell no Windows e Bash nos demais sistemas. Use `--script sh`, `--script ps` ou `--script py` para escolher.

Outras formas de executar:

```bash
# Execução avulsa, sem instalar
uvx --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git specify init meu-projeto --integration claude

# pipx
pipx install git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git

# Conferir a instalação e os agentes disponíveis
specify version
specify check
```

> [!IMPORTANT]
> O nome do pacote continua sendo `specify-cli`. Por isso, `uv tool install specify-cli` **sem** `--from` (ou `pip install specify-cli`) instala o **projeto original** do PyPI, e não o Cavaleiro Spec Driven. Veja [Compatibilidade](#compatibilidade).

Troque `copilot` pela [chave da sua integração](docs/reference/integrations.md), como `claude`, `codex`, `gemini`, `cursor-agent` ou `opencode`. Para um agente sem integração própria, use `generic` com `--integration-options="--commands-dir .meuagente/commands"`. Já tem código? Siga o [guia para projetos existentes](docs/guides/existing-projects.md), em inglês.

Agora **abra o seu agente de código na pasta do projeto** e escolha um processo abaixo. Chame cada *skill* `/speckit-*` **no chat do agente**, uma de cada vez, e revise o resultado antes de continuar. Elas são *skills* do agente, não comandos de terminal. Alguns agentes usam [outra sintaxe de chamada](docs/reference/integrations.md).

<a id="escolha-o-seu-processo"></a>

## Escolha o seu processo

| Do que você precisa | Processo | Resultado |
| --- | --- | --- |
| Construir uma funcionalidade ou aplicação | [Desenvolvimento Guiado por Especificação](#sdd) | Uma especificação levada até o planejamento, a implementação e a convergência |
| Diagnosticar e corrigir um comportamento quebrado | [Correção de bugs](#bugs) | Uma causa avaliada, uma correção delimitada e uma verificação registrada |
| Decidir se vale investir em uma ideia | [Avaliação de ideias](#ideias) | Uma decisão de seguir, esclarecer ou parar, baseada em evidências |
| Adotar ou criar outro processo | [Personalização](#personalizar) | Um processo adaptado ou montado a partir de peças reutilizáveis |

<a id="sdd"></a>

### Desenvolvimento Guiado por Especificação (SDD)

Defina **o quê e o porquê** antes de decidir **o como**. O SDD transforma requisitos em especificação, plano técnico e tarefas, e conduz a implementação a partir desses artefatos. A constituição é feita uma vez por projeto. Depois, cada funcionalidade passa por especificar → planejar → tarefas → implementar → convergir.

```text
/speckit-constitution Crie princípios focados em qualidade de código, testes e manutenção.
/speckit-specify Crie um organizador de fotos com álbuns agrupados por data e prévia em mosaico de cada álbum.
/speckit-plan Use Vite com JavaScript puro. Mantenha as imagens locais e guarde os metadados em SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

Repita **implementar → convergir** até a convergência informar **Converged**. Use `/speckit-clarify`, `/speckit-checklist` e `/speckit-analyze` quando precisar de verificações extras. Veja o [passo a passo do SDD](docs/quickstart.md) e a [referência de comandos](docs/reference/agentic-sdd.md), em inglês.

<a id="bugs"></a>

### Correção de bugs

Mantenha separados o diagnóstico, a correção e a verificação. No terminal, dentro da pasta do projeto:

```bash
specify extension add bug
```

Depois, no chat do agente:

```text
/speckit-bug-assess "Enviar uma senha vazia derruba o formulário de login." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

Os relatórios ficam em `.specify/bugs/login-crash/`. Veja o [passo a passo](docs/guides/bugfix.md) e a [referência](docs/reference/agentic-bugfix.md), em inglês.

<a id="ideias"></a>

### Avaliação de ideias

Reúna evidências antes de se comprometer com uma ideia. Funciona até em projetos sem código:

```bash
specify extension add assess
```

```text
/speckit-assess-intake "Permitir que os usuários trabalhem offline e sincronizem ao reconectar." slug=modo-offline
/speckit-assess-research slug=modo-offline
/speckit-assess-define slug=modo-offline
/speckit-assess-shape slug=modo-offline
/speckit-assess-decide slug=modo-offline
```

Os artefatos ficam em `.specify/assessments/modo-offline/` e terminam em uma decisão **go / needs-clarification / kill**, ou seja, seguir, esclarecer ou descartar. Veja o [passo a passo](docs/guides/assessment.md) e a [referência](docs/reference/agentic-assessment.md), em inglês.

<a id="personalizar"></a>

### Personalize ou traga o seu próprio processo

| Recurso | Mecanismo |
| --- | --- |
| Conectar ou trocar de agente de código | [Integrações](docs/reference/integrations.md) |
| Adicionar um comando, uma verificação ou um processo completo | [Extensões](docs/reference/extensions.md) |
| Adaptar templates, comandos, terminologia ou metodologia | [Presets](docs/reference/presets.md) |
| Sobrescrever um template em um único projeto | [Sobrescritas locais](docs/guides/customization.md) |
| Automatizar prompts, comandos, verificações e tarefas de shell | [Workflows](docs/reference/workflows.md) |
| Instalar uma configuração pronta para um papel ou equipe | [Bundles](docs/reference/bundles.md) |
| Descobrir ou hospedar catálogos de componentes | [Catálogos](docs/reference/catalogs.md) |
| Acessar catálogos e downloads privados | [Autenticação](docs/reference/authentication.md) |
| Trabalhar offline ou atrás de um firewall | [Instalação sem internet](docs/install/air-gapped.md) |
| Ver qual camada fornece um comando, template ou script | [Inventário de artefatos](docs/reference/artifacts.md) |

Estar listado em um catálogo não é auditoria nem endosso. Revise o código-fonte de componentes da comunidade antes de instalar ou executar.

<a id="compatibilidade"></a>

## Compatibilidade

O Cavaleiro Spec Driven renomeia o **projeto**, não os **identificadores**. Projetos, scripts e documentação existentes continuam funcionando:

- **O comando continua sendo `specify`**, e o pacote Python continua sendo **`specify-cli`**, na versão `1.2.2.dev0` herdada do projeto original. O `specify version` mostra essa versão do pacote. A versão do Cavaleiro é a **1.0.0**.
- **Os comandos do agente mantêm os nomes.** Continuam iguais as *skills* `/speckit.*` e `/speckit-*`, os comandos de extensões como `speckit.git.feature` e os marcadores dos templates.
- **A estrutura do projeto e a configuração não mudam.** Isso inclui `.specify/`, `init-options.json`, `integration.json`, os manifestos de extensões, presets e workflows, e todas as variáveis de ambiente (`SPECIFY_INIT_DIR`, `SPECIFY_FEATURE`, `SPECKIT_CATALOG_URL`, `SPECKIT_PRESET_CATALOG_URL`, `GH_TOKEN` e outras). Um projeto criado pelo projeto original funciona aqui, e vice-versa.
- **Os endereços usados em tempo de execução continuam apontando para o projeto original.** Nada foi redirecionado em silêncio:
  - Os **catálogos** de extensões, presets, integrações, workflows, *steps* e bundles são lidos de `raw.githubusercontent.com/github/spec-kit/main/…`. Você pode trocá-los com `SPECKIT_CATALOG_URL`, `SPECKIT_PRESET_CATALOG_URL`, `SPECKIT_INTEGRATION_CATALOG_URL`, `SPECKIT_WORKFLOW_CATALOG_URL` e `SPECKIT_STEP_CATALOG_URL`, ou com arquivos de catálogo por projeto dentro de `.specify/`. Veja [Catálogos](docs/reference/catalogs.md).
  - **`specify self check` e `specify self upgrade`** consultam `api.github.com/repos/github/spec-kit/releases/latest` e reinstalam a partir de `git+https://github.com/github/spec-kit.git`. Ou seja, `self upgrade` troca o Cavaleiro Spec Driven pela versão do **projeto original**. Para seguir um fork que publica as próprias tags de versão, defina `SPECIFY_UPGRADE_REPOSITORY=dono/repo`. Outra opção é reinstalar com o comando da seção [Instalação](#instalacao).
  - A CLI **não tem telemetria**. Ela só acessa a rede para consultar catálogos, para downloads que você pede e para `self check` e `self upgrade`.
- **As extensões incluídas mantêm os IDs.** A `git` (1.0.2) e a `agent-context` (1.0.3) receberam uma nova versão no Cavaleiro porque os scripts delas mudaram.
- **Documentação herdada.** As páginas em [`docs/`](docs/index.md) vêm do projeto original, e os comandos de instalação que citam `github/spec-kit` instalam o projeto original. Os READMEs traduzidos do projeto original estão em [`docs/original-i18n/`](docs/original-i18n/README.md), e os boletins dele em [`newsletters/`](newsletters/).

<a id="documentacao"></a>

## Documentação

- **Em português:** [guia completo do Cavaleiro Spec Driven](docs/cavaleiro/GUIA-PT-BR.md), com arquitetura, instalação por sistema, exemplos, configuração, solução de problemas e como contribuir.
- **Em inglês:**
  - [Instalação](docs/installation.md), [atualização](docs/upgrade.md) e [desenvolvimento local](docs/local-development.md).
  - [Referência da CLI](docs/reference/overview.md), [comandos principais](docs/reference/core.md) e [servidor MCP](docs/reference/mcp.md).
  - [Filosofia do SDD](docs/concepts/sdd.md), [metodologia completa](spec-driven.md) e [evolução de especificações existentes](docs/guides/evolving-specs.md).
  - [Relatório de engenharia](docs/cavaleiro/ENGINEERING.md), com arquitetura, linha de base, achados e verificação.

## Suporte e contribuição

[Relatar um bug ou pedir uma funcionalidade](https://github.com/cavaleiro-ai/cavaleiro-spec-driven/issues/new/choose) · [Guia de contribuição](CONTRIBUTING.md) · [Política de segurança](SECURITY.md) · [Código de conduta](CODE_OF_CONDUCT.md) · [Suporte](SUPPORT.md) · [Changelog](CHANGELOG.md)

<a id="licenca"></a>

## Licença

Baseado no Spec Kit · licença MIT · veja [LICENSE](LICENSE). Sem afiliação com o projeto original.

<p align="center"><a href="#top">Voltar ao topo ↑</a></p>
