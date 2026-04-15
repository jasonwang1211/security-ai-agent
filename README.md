# Sentinel Project

A security-focused project with modular architecture for knowledge retrieval, attack detection, and response.

## Modules

### Module 1: Security Knowledge Retrieval and Q&A
- Local knowledge base
- RAG answering
- Follow-up parsing
- Refusal mechanism

### Module 2: Attack Detection and Analysis
- Analyze input / log
- Determine attack type
- Provide risk description

### Module 3: Defense Recommendations and Response
- Provide repair suggestions
- Plan subsequent processing steps
- Reserve automated defense interface

## Structure

- `knowledge/`: Security knowledge files
- `chroma_db/`: Vector database for knowledge
- `modules/`: Core modules
- `agent_main.py`: Main agent script
- `ingest_knowledge.py`: Knowledge ingestion script