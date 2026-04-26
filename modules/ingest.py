import os

from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHROMA_PATH, EMBED_MODEL


class KnowledgeIngestor:
    def __init__(self):
        self.embeddings = None
        self.init_error = None

        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        except Exception as exc:
            self.init_error = exc

    def _load_file(self, file_path):
        for encoding in ("utf-8", "utf-8-sig", "cp950"):
            try:
                loader = TextLoader(file_path, encoding=encoding)
                return loader.load()
            except Exception:
                continue
        return []

    def load_documents(self, folder_path):
        if not os.path.isdir(folder_path):
            return []

        all_docs = []
        for root, _dirs, files in os.walk(folder_path):
            for filename in sorted(files):
                if not filename.lower().endswith((".txt", ".md")):
                    continue

                file_path = os.path.join(root, filename)
                docs = self._load_file(file_path)
                if docs:
                    all_docs.extend(docs)
                else:
                    print(f"Failed to load file: {file_path}")

        return all_docs

    def ingest_knowledge(self, input_folder="knowledge", db_dir=CHROMA_PATH):
        if self.embeddings is None:
            print(f"Failed to initialize embeddings: {self.init_error}")
            return False

        if not os.path.isdir(input_folder):
            print(f"Knowledge folder not found: {input_folder}")
            return False

        docs = self.load_documents(input_folder)
        if not docs:
            print("No .txt or .md knowledge files were loaded.")
            return False

        print(f"Loaded {len(docs)} documents")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
        )
        split_docs = splitter.split_documents(docs)

        print(f"Split into {len(split_docs)} chunks")

        try:
            Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=db_dir,
            )
        except Exception as exc:
            print(f"Failed to build Chroma DB: {exc}")
            return False

        print("Chroma DB created successfully")
        return True
