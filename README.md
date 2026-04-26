# AI-driven Security Threat Detection and Response System

## 🚀 Key Idea
This project is a hybrid AI-driven security system that combines:

- deterministic rule-based detection (high reliability)
- retrieval-grounded knowledge reasoning (RAG)
- LLM-assisted contextual analysis (controlled, non-authoritative)

to simulate a real-world blue-team security analyst workflow.

---

## Overview
This project is an AI-assisted security analysis system designed for threat detection, knowledge-grounded explanation, and response recommendation.

It integrates:
- rule-based detection for high-confidence attack identification
- structured RAG for grounded security knowledge
- LLM-assisted analysis for contextual reasoning

The system is designed for **defensive security analysis**, not offensive automation.

---

## Motivation
Traditional signature-based detection is fast and reliable for known attacks, but lacks context and explanation.

Pure LLM-based systems are flexible, but:
- may hallucinate
- may weaken security decisions
- may generate unsafe or misleading outputs

This project balances both approaches:
- Rule-based detection = **authoritative**
- RAG = **knowledge grounding**
- LLM = **assistive reasoning only**

---

## Design Principles
- Rule-based detection is the source of truth
- LLM is assistive, not authoritative
- RAG ensures answers are grounded in structured knowledge
- Follow-up questions must remain context-aware
- Output must remain defensive and safe
- System must fail safely if LLM fails

---

## System Architecture
User → Detector → Risk → Decision → RAG → LLM → Response

---

## Features
- Rule-based attack detection
- RAG knowledge system
- LLM-assisted reasoning
- Contextual follow-up
- Traditional Chinese output (OpenCC)

---

## How to Run

```bash
pip install -r requirements.txt
python ingest_knowledge.py
python app.py
```

---

## 📌 Project Status
Stable milestone version
