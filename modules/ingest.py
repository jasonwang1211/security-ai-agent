import os
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHROMA_PATH, EMBED_MODEL

class KnowledgeIngestor:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    def load_documents(self, folder_path):
        all_docs = []
        for f in os.listdir(folder_path):
            if f.endswith(".txt"):
                loader = TextLoader(os.path.join(folder_path, f), encoding="utf-8")
                all_docs.extend(loader.load())
        return all_docs

    def ingest_knowledge(self, input_folder="knowledge", db_dir=CHROMA_PATH):
        docs = self.load_documents(input_folder)

        print(f"📂 載入 {len(docs)} 份文件")

        # 切分文檔
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=40
        )
        split_docs = splitter.split_documents(docs)

        print(f"✂️ 切成 {len(split_docs)} chunks")

        # 建立向量資料庫
        Chroma.from_documents(
            documents=split_docs,
            embedding=self.embeddings,
            persist_directory=db_dir
        )

        print("✅ Chroma DB 建立完成！")
