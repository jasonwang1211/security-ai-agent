from modules.ingest import KnowledgeIngestor

def main():
    ingestor = KnowledgeIngestor()
    ingestor.ingest_knowledge(input_folder="knowledge/blue_team")

if __name__ == "__main__":
    main()
