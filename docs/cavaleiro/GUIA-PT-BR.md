# Guia do Cavaleiro Spec Driven (português)

Este guia explica, em português, o que é o Cavaleiro Spec Driven, como ele funciona por dentro, como instalar em cada sistema operacional e como usar no dia a dia. Para um resumo rápido, veja o [README em português](../../README.pt-BR.md). O relatório técnico das melhorias está em [ENGINEERING.md](ENGINEERING.md), em inglês.

## Sumário

1. [O que é e para quem](#o-que-e-e-para-quem)
2. [Arquitetura](#arquitetura)
3. [Instalação passo a passo](#instalacao-passo-a-passo)
4. [Primeiros passos](#primeiros-passos)
5. [Exemplos práticos](#exemplos-praticos)
6. [Configuração](#configuracao)
7. [Solução de problemas](#solucao-de-problemas)
8. [Como contribuir](#como-contribuir)

<a id="o-que-e-e-para-quem"></a>

## 1. O que é e para quem

O **Cavaleiro Spec Driven** é um kit para o **Desenvolvimento Guiado por Especificação** (*Spec-Driven Development*, SDD) com agentes de código com IA, como Claude Code, GitHub Copilot, Codex, Gemini CLI, Cursor e outros 37 agentes. A ideia central é simples: antes de pedir código ao agente, você escreve **o quê** e **o porquê**. Isso vira uma especificação. Depois, o agente transforma a especificação em plano técnico, em lista de tarefas e, por fim, em implementação, sempre conferindo o resultado contra esses documentos.

Ele é mantido pela [Cavaleiro AI](https://github.com/cavaleiro-ai) e mantém a mesma CLI (`specify`), os mesmos comandos de agente (`/speckit-*`) e a mesma estrutura de projeto (`.specify/`) do projeto original. Além disso, corrige bugs de segurança, robustez e Windows, todos verificados com testes.

**Para quem é:**

- **Desenvolvedores** que usam agentes de IA e querem resultados previsíveis, e não apenas "código que parece pronto".
- **Equipes** que querem um processo comum, como constituição do projeto, especificação, plano, tarefas, implementação e convergência, com os mesmos artefatos para todos.
- **Quem trabalha no Windows.** As correções desta versão fazem os scripts PowerShell funcionarem em caminhos com colchetes e reconhecem instalações `uv tool`.
- **Quem precisa avaliar ideias ou corrigir bugs com método.** As extensões `assess` e `bug` trazem processos prontos para isso.

<a id="arquitetura"></a>

## 2. Arquitetura

O projeto tem três camadas: a **CLI** em Python (`specify`), os **ativos** que ela instala no seu projeto (templates, scripts e comandos de agente) e os **componentes opcionais** (extensões, presets, workflows e bundles), que vêm do próprio pacote ou de catálogos.

```text
                         você (terminal)                         você (chat do agente)
                               |                                          |
                               v                                          v
+-------------------------------------------------------+     +------------------------------+
| CLI `specify`  (src/specify_cli)                      |     | Agente de código (Claude,    |
|  init / check / version / self check|upgrade          |     | Copilot, Codex, Gemini...)   |
|  integration  extension  preset  workflow  bundle     |     |  /speckit-specify, -plan,    |
|  artifact  event  mcp                                 |     |  -tasks, -implement ...      |
+---------------------------+---------------------------+     +---------------+--------------+
                            | instala / atualiza                              | lê e executa
                            v                                                 v
+---------------------------------------------------------------------------------------------+
| Seu projeto                                                                                 |
|  .specify/                       pasta do agente (.claude/, .github/, .agents/ ...)        |
|   templates/  scripts/{bash,powershell,python}   comandos/skills gerados para o agente     |
|   memory/constitution.md   extensions/  presets/  workflows/   init-options.json           |
|  specs/NNN-funcionalidade/  spec.md  plan.md  tasks.md ...                                  |
+---------------------------------------------------------------------------------------------+
                            ^
                            | baixa (HTTPS, limites de tamanho, extração segura)
+---------------------------+-----------------------------------------------------------------+
| Catálogos e pacotes: núcleo embutido no wheel (core_pack) + catálogos remotos opcionais     |
+---------------------------------------------------------------------------------------------+
```

**Componentes principais (`src/specify_cli/`):**

| Componente | Responsabilidade |
| --- | --- |
| `__init__.py`, `command_init.py` | Ponto de entrada (`specify = specify_cli:main`). O `init` cria o projeto, instala a integração do agente, os scripts e templates compartilhados, extensões, presets e o workflow `speckit`. |
| `shared_infra.py`, `_assets.py` | Copiam `.specify/scripts` e `.specify/templates` a partir do `core_pack` embutido no pacote (funciona offline) e registram tudo em um manifesto. |
| `integrations/` | Uma pasta para cada um dos 42 agentes (chaves como `claude`, `copilot`, `codex`, `generic`). Cada integração sabe onde e em que formato gravar os comandos e *skills* do agente. |
| `extensions/`, `presets/`, `workflows/`, `bundles/` | Instalação, atualização, remoção e catálogos de cada tipo de componente. Os workflows têm um motor de execução com etapas (`workflows/engine.py`, `workflows/step/`). |
| `_download_security.py` | Downloads com limite de tamanho, política HTTPS e de redirecionamento, e extração segura de ZIP e tar.gz (bloqueia caminhos fora da pasta, links simbólicos, nomes reservados do Windows e "bombas" de compressão). |
| `authentication/` | Tokens para catálogos privados (GitHub, Azure DevOps, Bitbucket), aplicados só aos hosts configurados. |
| `_version.py`, `selfs/` | `specify version`, `self check` e `self upgrade`, que detectam se a instalação foi feita via `uv tool`, `pipx` ou código-fonte. |
| `mcp_server/` | Servidor MCP experimental (`specify mcp`) que expõe operações da CLI para agentes. |

**Scripts (`scripts/` e `extensions/*/scripts/`):** cada script existe em três versões gêmeas, **Bash**, **PowerShell** (compatível com o Windows PowerShell 5.1) e **Python**, e as três devem se comportar da mesma forma. Os comandos de agente chamam esses scripts para criar a pasta da funcionalidade, achar os pré-requisitos e preparar o plano e as tarefas.

**Fluxo do SDD:** `/speckit-constitution` grava os princípios em `.specify/memory/constitution.md`. Em seguida, `/speckit-specify` executa a extensão `git` (cria a branch) e o script `create-new-feature` (cria `specs/001-.../spec.md`). Depois vêm `/speckit-plan` (que usa `setup-plan`), `/speckit-tasks` (que usa `setup-tasks`) e `/speckit-implement`, e por fim `/speckit-converge`.

**Testes:** são cerca de 12.700 testes `pytest` em `tests/`. Eles cobrem a CLI, as integrações, a paridade entre os scripts Bash, PowerShell e Python, a segurança de download e os workflows do GitHub Actions.

<a id="instalacao-passo-a-passo"></a>

## 3. Instalação passo a passo

Você vai precisar de **Python 3.11 ou mais novo**, do **uv** (recomendado) ou do pipx e de um **agente de código**. O **Git** é opcional e só é necessário para a extensão `git`, que cria branches.

> [!IMPORTANT]
> Instale **a partir deste repositório** (`--from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git`). O nome do pacote continua `specify-cli`, então `uv tool install specify-cli` sem `--from` instala o **projeto original** do PyPI.

### Windows (10 ou 11)

1. **Python:** instale pelo site [python.org](https://www.python.org/downloads/) e marque *Add python.exe to PATH*. Ou use `winget install Python.Python.3.12`. Confira com `python --version`.
2. **uv:** no PowerShell, execute:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Feche e reabra o terminal, depois confira com `uv --version`.
3. **Git (opcional):** `winget install Git.Git`.
4. **Cavaleiro Spec Driven:**

   ```powershell
   uv tool install specify-cli --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git
   specify version
   ```

   Se aparecer "specify não é reconhecido", execute `uv tool update-shell` e reabra o terminal. O uv coloca o `specify.exe` em `%USERPROFILE%\.local\bin`.
5. **Política de execução do PowerShell:** os comandos do agente rodam scripts `.ps1`. Se o Windows bloquear, libere os scripts locais para o seu usuário:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

### macOS

1. **Python e uv:** `brew install python uv`. Sem Homebrew, use `curl -LsSf https://astral.sh/uv/install.sh | sh`, e o uv baixa um Python quando precisar.
2. **Git:** já vem com as *Command Line Tools* (`xcode-select --install`) ou pode ser instalado com `brew install git`.
3. **Cavaleiro Spec Driven:**

   ```bash
   uv tool install specify-cli --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git
   specify version
   ```

### Linux

1. **uv:** `curl -LsSf https://astral.sh/uv/install.sh | sh`. Depois, reabra o terminal ou execute `source $HOME/.local/bin/env`.
2. **Python 3.11+:** use o da distribuição (`sudo apt install python3`, `sudo dnf install python3`) ou deixe o uv baixar um (`uv python install 3.12`).
3. **Git:** `sudo apt install git` ou `sudo dnf install git`.
4. **Cavaleiro Spec Driven:**

   ```bash
   uv tool install specify-cli --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git
   specify version
   ```

### Alternativas

- **Sem instalar (uma execução só):** `uvx --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git specify init meu-projeto --integration claude`.
- **Com pipx:** `pipx install git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git`.
- **Sem internet:** gere um *wheel* em uma máquina com acesso e instale offline. Siga o [guia de instalação sem internet](../install/air-gapped.md), em inglês.

<a id="primeiros-passos"></a>

## 4. Primeiros passos

1. **Crie o projeto** para o seu agente:

   ```bash
   specify init meu-app --integration claude
   cd meu-app
   ```

   - Para usar a pasta atual, rode `specify init --here --integration claude`. Se a pasta não estiver vazia, o comando pede confirmação; use `--force` para mesclar sem perguntar.
   - Para escolher os scripts, use `--script ps` (PowerShell), `--script sh` (Bash) ou `--script py` (Python).
   - Para incluir a extensão de branches Git, use `--extension git`.
2. **Confira as ferramentas** com `specify check`. Ele lista quais agentes e ferramentas foram encontrados.
3. **Abra o agente na pasta do projeto** e, **no chat do agente**, crie a constituição:

   ```text
   /speckit-constitution Priorize código simples, testes automatizados e acessibilidade.
   ```

4. **Especifique, planeje, quebre em tarefas e implemente**, revisando cada resultado antes de seguir:

   ```text
   /speckit-specify Um app de lista de tarefas com prazos e lembretes por e-mail.
   /speckit-plan Use FastAPI, SQLite e templates Jinja. Sem frameworks de front-end.
   /speckit-tasks
   /speckit-implement
   /speckit-converge
   ```

   Os documentos ficam em `specs/001-lista-de-tarefas/` (`spec.md`, `plan.md`, `tasks.md`).

> [!TIP]
> Alguns agentes usam outra sintaxe. Em modo de comandos, é `/speckit.specify`. No Codex, é `$speckit-specify`. Veja a [referência de integrações](../reference/integrations.md), em inglês.

<a id="exemplos-praticos"></a>

## 5. Exemplos práticos

### Projeto novo com GitHub Copilot no VS Code, sem prompts

```bash
specify init loja --integration copilot --script ps --non-interactive --extension git
```

### Projeto existente

```bash
cd meu-sistema-legado
specify init --here --integration codex --force
```

Depois, no chat: `/speckit-constitution Documente as convenções que este código já segue.`. Veja o [guia para projetos existentes](../guides/existing-projects.md), em inglês.

### Corrigir um bug com método

```bash
specify extension add bug
```

```text
/speckit-bug-assess "O relatório mensal mostra valores duplicados quando há estornos." slug=relatorio-duplicado
/speckit-bug-fix slug=relatorio-duplicado
/speckit-bug-test slug=relatorio-duplicado
```

O veredito final é `verified`, `partial` ou `failed`. Sem verificação, a correção não conta como concluída.

### Avaliar uma ideia antes de construir

```bash
specify extension add assess
```

```text
/speckit-assess-intake "Cobrança recorrente por PIX para assinantes." slug=pix-recorrente
/speckit-assess-research slug=pix-recorrente
/speckit-assess-define slug=pix-recorrente
/speckit-assess-shape slug=pix-recorrente
/speckit-assess-decide slug=pix-recorrente
```

### Usar um nome de branch definido pela sua equipe

Quando o padrão da equipe é `feature/PROJ-42-login`, crie a branch e exporte a variável antes de chamar o agente:

```bash
git checkout -b feature/PROJ-42-login
export GIT_BRANCH_NAME=feature/PROJ-42-login        # PowerShell: $env:GIT_BRANCH_NAME = 'feature/PROJ-42-login'
```

No Cavaleiro Spec Driven, o `/speckit-specify` reaproveita a branch atual quando `GIT_BRANCH_NAME` aponta para ela. No projeto original, isso falhava (issue #5003 do projeto original). Se a variável apontar para **outra** branch que já existe, o comando continua falhando de propósito, para não trocar de branch sem você perceber.

### Monorepo: rodar comandos em um subprojeto sem `cd`

```bash
SPECIFY_INIT_DIR=servicos/pagamentos specify extension list
```

### Instalar uma extensão de um endereço

```bash
specify extension add minha-ext --from https://exemplo.com/minha-ext-1.0.0.zip
```

A CLI pede confirmação, só aceita HTTPS (HTTP só para `localhost`), limita o tamanho a 50 MiB e extrai o arquivo com segurança. Se a conexão cair no meio do download, você vê `Error: Failed to download from ...` em vez de um *traceback*.

<a id="configuracao"></a>

## 6. Configuração

### Arquivos do projeto

| Arquivo | Para que serve |
| --- | --- |
| `.specify/init-options.json` | As opções do `init`: agente, scripts, `feature_numbering` (`sequential` ou `timestamp`) e outras. Não há flag para `feature_numbering`, então edite o arquivo. O `init --here --force` preserva esse valor no Cavaleiro. |
| `.specify/integration.json` | As integrações instaladas e a integração padrão. |
| `.specify/memory/constitution.md` | Os princípios do projeto, usados por todos os comandos. |
| `.specify/templates/overrides/` | Templates que substituem os padrões só neste projeto. |
| `.specify/extensions/git/git-config.yml` | Configuração da extensão git: modelo de nome de branch, commits automáticos e outras opções. |

### Variáveis de ambiente úteis

| Variável | Efeito |
| --- | --- |
| `SPECIFY_INIT_DIR` | Aponta a CLI e os scripts para outro projeto (útil em monorepos e CI). |
| `SPECIFY_FEATURE` / `SPECIFY_FEATURE_DIRECTORY` | Escolhem a funcionalidade atual sem depender da branch ou do `feature.json`. |
| `GIT_BRANCH_NAME` | Usa exatamente esse nome de branch na extensão git. |
| `SPECKIT_CATALOG_URL`, `SPECKIT_PRESET_CATALOG_URL`, `SPECKIT_INTEGRATION_CATALOG_URL`, `SPECKIT_WORKFLOW_CATALOG_URL`, `SPECKIT_STEP_CATALOG_URL` | Trocam os catálogos remotos. Por padrão, eles vêm do repositório do projeto original. |
| `GH_TOKEN` / `GITHUB_TOKEN` | Token para catálogos e downloads privados no GitHub. Veja [autenticação](../reference/authentication.md), em inglês. |
| `SPECKIT_PYTHON_EXECUTABLE` | Qual Python os scripts devem usar quando precisarem dele. |
| `SPECIFY_UPGRADE_REPOSITORY` | **Novo no Cavaleiro.** É um `dono/repo` que o `self check` e o `self upgrade` passam a seguir. Sem ela, os comandos seguem o projeto original. |
| `SPECIFY_UPGRADE_TIMEOUT_SECS` | Tempo limite do `self upgrade`. |

### Atualizar

- **A CLI:** reinstale a partir deste repositório com `uv tool install specify-cli --force --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git`.
  - `specify self upgrade` instala a versão do **projeto original**, a menos que você defina `SPECIFY_UPGRADE_REPOSITORY`.
- **Os arquivos de um projeto:** use `specify integration upgrade`. Se ele não servir, use `specify init --here --force --integration <agente>`.
- **As extensões incluídas:** `specify extension update`.

<a id="solucao-de-problemas"></a>

## 7. Solução de problemas

| Sintoma | Causa provável e solução |
| --- | --- |
| `specify` não é reconhecido | A pasta de executáveis do uv não está no PATH. Rode `uv tool update-shell` e reabra o terminal. |
| `uv tool install specify-cli` instalou o projeto original | Faltou o `--from`. Reinstale com `--force --from git+https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git`. |
| `specify self upgrade` voltou para a versão do projeto original | É o comportamento padrão. Defina `SPECIFY_UPGRADE_REPOSITORY` ou reinstale a partir do fork. |
| Scripts `.ps1` bloqueados no Windows | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| Erro "Directory already exists" depois de um `init` que falhou | No Cavaleiro, um `init` que falha remove a pasta que ele mesmo criou. Se a pasta veio de uma versão antiga, apague-a ou use `--force`. |
| `specify self upgrade` diz que não identificou o método de instalação no Windows | Corrigido no Cavaleiro: instalações `uv tool` em `%APPDATA%\uv\tools` agora são detectadas. Em versões antigas, reinstale manualmente. |
| Os scripts PowerShell não acham arquivos em uma pasta como `projeto [v2]` | Corrigido no Cavaleiro: os scripts usam `-LiteralPath`. Atualize a extensão `git` com `specify extension update` e reinstale os scripts com `specify integration upgrade`. |
| "Branch '...' already exists" ao usar `GIT_BRANCH_NAME` | Se a variável aponta para a branch atual, isso foi corrigido no Cavaleiro (extensão `git` 1.0.2). Se aponta para outra branch que já existe, faça `git checkout` dessa branch antes e chame o comando de novo. |
| Download interrompido ou "truncated: received X of Y bytes" | A conexão caiu no meio do download. Tente de novo. O arquivo incompleto nunca é instalado. |
| "Unsafe tar.gz archive: extended header ..." | O pacote tem cabeçalhos tar anormais e foi recusado por segurança. Peça ao autor um pacote gerado normalmente. |
| Mensagens com caracteres estranhos no console do Windows | Use o Windows Terminal ou execute `chcp 65001`. A CLI já força UTF-8 na saída. |

Para ver informações de diagnóstico, rode `specify version` e `specify init ... --debug`. Para relatar um problema, use o [formulário de bug](https://github.com/cavaleiro-ai/cavaleiro-spec-driven/issues/new/choose). Vulnerabilidades devem ser relatadas **em privado**, conforme a [política de segurança](../../SECURITY.md).

<a id="como-contribuir"></a>

## 8. Como contribuir

1. Faça um fork, clone e crie uma branch (`fix/<numero>-descricao` ou `feat/...`):

   ```bash
   git clone https://github.com/cavaleiro-ai/cavaleiro-spec-driven.git
   cd cavaleiro-spec-driven
   uv sync --extra test
   ```

2. Rode os testes com o Python do ambiente do projeto:

   ```bash
   .venv/bin/python -m pytest -q          # Windows: .venv\Scripts\python -m pytest -q
   ```

   No Windows, há duas limitações. Testes que criam links simbólicos falham com `WinError 1314`, a menos que o Modo de Desenvolvedor esteja ativo. Testes Bash são pulados quando o `bash` do sistema é o lançador do WSL.
3. Correções de bug precisam de um **teste que falha antes e passa depois**. Mudanças em PowerShell precisam ser testadas no **Windows PowerShell 5.1**. Mudanças em um script precisam ser replicadas nas versões gêmeas em Bash, PowerShell e Python.
4. Adicione uma linha no [CHANGELOG](../../CHANGELOG.md) e preencha o [modelo de pull request](../../.github/PULL_REQUEST_TEMPLATE.md), incluindo a declaração de uso de IA.
5. Leia o [guia de contribuição](../../CONTRIBUTING.md), em inglês, e o [código de conduta](../../CODE_OF_CONDUCT.md).

---

O Cavaleiro Spec Driven é distribuído sob a [licença MIT](../../LICENSE).
