# RadarComp

Radar estratégico de oportunidades profissionais em Computação.

A V1 monitora fontes oficiais do **IFPB**, classifica oportunidades, calcula score estratégico, mantém histórico em JSON, gera um dashboard estático para **GitHub Pages** e envia alertas **P0/P1** pelo Telegram.

## Estratégia de carreira

- **Plano A — IFPB:** professor efetivo/substituto em Computação é prioridade máxima. Cargos de TI do IFPB também são monitorados com prioridade menor.
- **Plano B — Docência estratégica:** arquitetura preparada para vagas docentes que fortaleçam experiência e currículo. Fontes privadas entram na V2.
- **Plano C — QA:** arquitetura e classificação preparadas para QA/Testes. Fontes de vagas entram na V3.

> O RadarComp não afirma que uma experiência dará pontos em futuros concursos. A pontuação de títulos depende do edital vigente.

## O que a V1 faz

- monitora páginas vigentes de Professor Substituto, Professor EBTT e Técnico-Administrativo do IFPB;
- segue paginação do portal Plone;
- acompanha a página de detalhe de cada edital e seus documentos;
- detecta mudanças por hash;
- lê PDF com camada de texto quando a página HTML não revela a área/cargo;
- evita OCR na V1;
- usa regras Python antes de chamar LLM;
- usa Gemini para extração estruturada quando configurado;
- protege o prompt do Gemini contra instruções vindas do conteúdo externo;
- deduplica oportunidades;
- calcula `strategic_score`, `compatibility_score`, `urgency_score` e `total_score`;
- persiste dados em JSON versionado;
- notifica P0/P1 pelo Telegram sem repetir a mesma revisão;
- gera dashboard estático sem publicar perfil, tokens ou metadados internos;
- roda por CLI, GitHub Actions e GitHub Pages.

## Fontes oficiais validadas em 24/08/2026

- Professor Substituto: `https://www.ifpb.edu.br/concursopublico/professor-substituto/vigentes`
- Professor EBTT: `https://www.ifpb.edu.br/concursopublico/professor/vigentes`
- Técnico-Administrativo: `https://www.ifpb.edu.br/concursopublico/tecnico-administrativo/vigentes`

As URLs ficam em `config/sources.yaml` para permitir alteração sem espalhar endereços no código.

## Arquitetura

```text
GitHub Actions / CLI
        |
        v
    IFPBSource
        |
        v
HTML/PDF parsers -----> hash / detecção de mudança
        |                         |
        v                         v
classifier Python ----------> Gemini (se necessário)
        |                         |
        +------------+------------+
                     v
               ScoringEngine
                     |
                     v
              JsonRepository
                /          \
               v            v
          Telegram       SiteBuilder
                            |
                            v
                       GitHub Pages
```

## Estrutura

```text
radarcomp/
├── app/
│   ├── config/
│   ├── domain/
│   ├── llm/
│   ├── notifications/
│   ├── parsers/
│   ├── repositories/
│   ├── scoring/
│   ├── services/
│   ├── sources/
│   └── utils/
├── config/
│   ├── profile.yaml
│   ├── scoring.yaml
│   └── sources.yaml
├── data/
├── site/
├── tests/
├── .github/workflows/
├── main.py
└── pyproject.toml
```

## Instalação local

Requer Python 3.11+ (recomendado 3.12).

```bash
git clone SEU_REPOSITORIO
cd radarcomp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuração

Copie o exemplo:

```bash
cp .env.example .env
```

A aplicação lê `.env` automaticamente. `.env` está no `.gitignore`.

### Gemini

Configure:

```env
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-2.5-flash-lite
```

O modelo é configurável para evitar acoplamento. O código usa a REST API por meio de `GeminiProvider` e valida a resposta com Pydantic.

Sem `GEMINI_API_KEY`, o RadarComp continua funcionando apenas com regras determinísticas e parsing local.

### Telegram

Crie um bot com o BotFather e configure:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Para descobrir seu `TELEGRAM_CHAT_ID`:

1. envie uma mensagem para seu bot;
2. abra no navegador `https://api.telegram.org/botSEU_TOKEN/getUpdates`;
3. localize `message.chat.id`;
4. coloque o valor em `.env` ou no GitHub Secret.

Teste:

```bash
python main.py test-telegram
```

Sem as duas variáveis do Telegram, as notificações ficam desativadas sem bloquear o scan.

## Perfil

Edite `config/profile.yaml`.

Os campos `degrees`, `skills` e `qa_skills` ficam vazios por padrão para o sistema não inventar dados pessoais.

Exemplo:

```yaml
degrees:
  - Ciência da Computação

skills:
  - Python
  - Redes

qa_skills:
  - Playwright
  - Pytest
```

Esses dados são usados no cálculo de compatibilidade, mas **não são exportados para o GitHub Pages**.

## Scoring

Todos os pesos ficam em `config/scoring.yaml`.

O score é separado em:

- `strategic_score`: alinhamento com Plano A/B/C;
- `compatibility_score`: formação e skills;
- `urgency_score`: proximidade de prazo;
- `total_score`: estratégico + compatibilidade + bônus de urgência limitado.

O bônus de urgência possui teto para uma vaga pouco estratégica não ultrapassar um objetivo do Plano A apenas porque o prazo está acabando.

## CLI

### Escanear

```bash
python main.py scan
```

O comando também atualiza `site/data/opportunities.json`.

### Listar

```bash
python main.py list
python main.py list --plan A
python main.py list --priority P0
```

### Ver uma oportunidade

```bash
python main.py show ID
```

### Gerar dados do site

```bash
python main.py build-site
```

### Estado das páginas monitoradas

```bash
python main.py source-status
```

## Persistência

A V1 não requer banco externo.

- `data/opportunities.json`: fonte da verdade das oportunidades;
- `data/sources_state.json`: hashes das páginas já processadas;
- `data/history.json`: eventos `NEW`, `UPDATED` e `NOTIFIED`.

Os arquivos só mudam quando há mudança relevante. O timestamp do dashboard é derivado da última alteração de oportunidade, evitando commits vazios a cada execução agendada.

## GitHub Actions

### `tests.yml`

Executa testes em `push`/`pull_request`.

### `scan.yml`

Executa:

- a cada hora, no minuto 17;
- manualmente por `workflow_dispatch`.

O minuto 17 foi escolhido para evitar o pico comum de workflows no minuto 00.

Fluxo:

```text
pytest
  -> scan
  -> build-site
  -> commit somente se data/site/data mudou
  -> deploy do GitHub Pages
```

O commit automático usa `GITHUB_TOKEN` e `[skip ci]`, e o deploy do Pages acontece no próprio workflow atual.

### `pages.yml`

Permite publicar manualmente e também publica mudanças feitas diretamente nos arquivos estáticos do site.

## GitHub Secrets

No repositório:

`Settings -> Secrets and variables -> Actions -> New repository secret`

Crie:

- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Opcionalmente configure a variável de repositório:

- `GEMINI_MODEL`

Nunca faça commit dos tokens.

## GitHub Pages

No repositório:

1. abra `Settings -> Pages`;
2. em **Build and deployment**, selecione **GitHub Actions**;
3. execute `RadarComp Scan` manualmente uma primeira vez.

O workflow enviará a pasta `site/` como artefato do Pages.

## Segurança

### Prompt injection

Conteúdo de sites e PDFs é tratado como não confiável.

O `GeminiProvider` envia a regra de segurança em `systemInstruction`, separada do texto externo. A instrução estabelece que comandos encontrados dentro do edital não podem alterar o comportamento do extrator.

### Dashboard

Strings externas são escapadas no navegador e links são restritos a `http`/`https` antes de serem renderizados.

O SiteBuilder usa allowlist de campos públicos e não exporta:

- `metadata`;
- `requirements` internos;
- dados do perfil;
- tokens;
- hashes de notificação.

## PDFs

`pypdf` extrai texto dos primeiros 30 pages (até 120 mil caracteres).

Se o PDF for somente imagem, a V1 registra a falha e não usa OCR. OCR deve ser uma estratégia explícita futura, pois aumenta custo e fragilidade.

## Deduplicação

A deduplicação prioriza:

1. mesma instituição + mesmo número de edital;
2. similaridade de título dentro da mesma instituição.

Documentos como retificações/resultados ficam associados ao edital em `metadata.documents` e não viram oportunidades separadas.

## Como adicionar uma nova Source

1. crie uma classe em `app/sources/` que herde `BaseSource`;
2. implemente `list_entries()` retornando `ListingEntry` normalizado;
3. mantenha acesso HTTP isolado e com timeout;
4. não use Gemini para scraping;
5. adicione fixtures e testes offline;
6. só então conecte a Source ao scanner.

Para sites com termos de uso restritivos, prefira API, RSS, página oficial ou outra forma permitida.

## Testes

```bash
pytest
```

Os testes unitários não acessam a internet. Fixtures simulam o padrão Plone confirmado no IFPB.

## CurriculumTracker

A V1 já possui um domínio estável em `app/domain/curriculum.py` para experiências docentes, cursos ministrados, artigos, projetos, eventos e titulações.

A persistência e interface do tracker ficam para a V2.

## Roadmap

### V2

- prefeituras e outros órgãos públicos;
- instituições privadas de ensino;
- CurriculumTracker completo;
- comparação de currículo com prova de títulos de edital vigente.

### V3

- fontes de QA;
- Gupy/LinkedIn/Indeed somente quando houver forma tecnicamente e juridicamente adequada;
- WhatsApp como outro `NotificationProvider`;
- histórico/estatísticas avançados;
- banco externo se o volume justificar.

## Limitações conhecidas da V1

- o conteúdo real da web não é usado nos testes; fixtures evitam testes frágeis e dependentes de rede;
- mudanças estruturais no Plone podem exigir atualização do parser;
- editais com muitas vagas podem ser representados inicialmente de forma agregada por edital, não necessariamente uma linha por código de vaga;
- PDF escaneado não é submetido a OCR;
- Plano B e Plano C têm modelo/classificação, mas ainda não possuem fontes externas ativas na V1;
- a qualidade da extração do Gemini depende do modelo/cota disponíveis no projeto da API.

## Princípio do projeto

O RadarComp não é um agregador genérico de vagas.

Ele ordena oportunidades pela estratégia:

1. **Plano A: Professor do IFPB**;
2. **Plano B: Docência que fortalece o caminho para o Plano A**;
3. **Plano C: QA como alternativa na indústria**.

A fonte oficial deve ser sempre consultada antes de tomar qualquer decisão de inscrição.
