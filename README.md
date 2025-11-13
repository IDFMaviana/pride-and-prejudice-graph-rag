# Pride and Prejudice Graph RAG

Este repositório reúne um pipeline completo de GraphRAG para o romance **Pride and Prejudice**. A ideia é extrair cenas e relacionamentos com o Llama Cloud, estruturar os resultados em um grafo Neo4j, criar embeddings ricos para busca semântica em Pinecone e, por fim, orquestrar tudo com agentes CrewAI capazes de responder perguntas sobre a obra.

## Visão geral

1. **Preparação do texto**: o livro bruto é dividido capítulo a capítulo.
2. **Extração semântica**: um agente do Llama Cloud identifica personagens, cenários, temas e relações.
3. **Bases de conhecimento**:
   - **Neo4j** guarda os personagens e interações (grafo heterogêneo).
   - **Pinecone** indexa resumos das cenas como vetores para busca semântica.
4. **Camada de agentes**: três agentes CrewAI (grafo, semântico e literário) combinam consultas estruturadas e contextuais para responder ao usuário.

## Principais recursos

- **Pipeline de dados reproduzível** (`src/data`, `src/Llama`, `src/vector_db_loader.py`, `src/graph_db_loader.py`).
- **Integração com Google Gemini** para embeddings e geração.
- **Suporte a Docker Compose** para subir aplicação e Neo4j rapidamente.
- **Notebooks exploratórios** em `notebooks/` para análises ad hoc.

## Pré-requisitos

- Python 3.12+
- Conta no [Llama Cloud](https://www.llamaindex.ai/) com acesso ao Extract.
- Chaves para Google Generative AI, Pinecone e Neo4j (self-hosted ou AuraDB).
- Docker e Docker Compose (opcional, mas recomendado).
- Arquivo `jane-austen-pride-prejudice.txt` em `src/data/raw/`.

## Configuração rápida

1. Clone o projeto e crie um ambiente virtual.
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copie o texto original para `src/data/raw/jane-austen-pride-prejudice.txt`.
3. Crie um arquivo `.env` na raiz com as credenciais abaixo.

### Variáveis de ambiente esperadas

| Nome                     | Descrição                                              |
|-------------------------|--------------------------------------------------------|
| `GEMINI_API_KEY`        | Chave do Google Generative AI (usada por LLM/embeddings) |
| `LLAMA_EXTRACT_KEY`     | Chave do Llama Cloud Extract                           |
| `NEO4J_URI`             | URI do banco (ex.: `bolt://neo4j:7687`)                |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Credenciais do Neo4j                           |
| `PINECONE_API_KEY`      | Chave do Pinecone                                      |
| `PINECONE_INDEX_NAME`   | Nome do índice que será criado/use                    |

## Preparando os dados

1. **Dividir o livro em capítulos**
   ```bash
   python src/data/preprocess_chapters.py
   ```
   Saída: arquivos `Chapter_X.txt` em `src/data/pre_processed/`.

2. **Rodar o agente de extração**
   ```bash
   python src/Llama/agent_extraction.py
   ```
   O script envia lotes para o Llama Cloud e consolida os resultados em `src/data/processed/processed_book.json`.

## Carregar as bases

1. **Pinecone (vetores)**
   ```bash
   python src/vector_db_loader.py
   ```
   - Cria o índice (caso não exista) com embeddings Gemini `models/gemini-embedding-001`.
   - Faz upsert em lotes de 50 cenas.

2. **Neo4j (grafo de personagens)**
   ```bash
   python src/graph_db_loader.py
   ```
   - Garante a constraint única de personagens.
   - Cria nós de personagens e relacionamentos `INTERACTS_IN` com atributos de cena.

## Subindo o ambiente com Docker

```bash
docker compose up --build
```

- Serviço `neo4j` expõe 7474 (Browser) e 7687 (Bolt), persistindo dados em `neo4j_data/`.
- Serviço `app` carrega o código em `/app/src` com as variáveis definidas no `.env`.

## Operando os agentes

Com as bases populadas e as variáveis configuradas, execute:

```bash
python src/main_agent.py
```

O script instancia:
- **Graph Database Specialist** para Cypher no Neo4j.
- **Semantic Search Specialist** para busca Pinecone.
- **Literary Analyst** que coordena as respostas ao usuário.

(Os hooks para ferramentas estão prontos, bastando conectar os objetos de consulta dentro do código.)

## Estrutura do repositório

```
.
├── docker-compose.yml / dockerfile
├── requirements.txt
├── neo4j_data/                 # volume do banco
├── notebooks/                  # análises exploratórias
└── src/
    ├── data/
    │   ├── raw/                # texto original
    │   ├── pre_processed/      # capítulos individuais
    │   ├── processed/          # JSON final do Llama
    │   └── preprocess_chapters.py
    ├── Llama/
    │   ├── prompts/            # prompt e schema do extractor
    │   └── agent_extraction.py
    ├── tools/, utils/
    ├── graph_db_loader.py
    ├── vector_db_loader.py
    └── main_agent.py
```

## Próximos passos sugeridos

- Conectar de fato os agentes às ferramentas de consulta (Neo4j/Pinecone) e liberar uma interface de chat.
- Enriquecer o schema do grafo (por exemplo, nós de lugares ou temas).
- Adicionar testes automatizados para as funções de parsing e loaders.

## Licença

Distribuído sob a licença [MIT](LICENSE).
