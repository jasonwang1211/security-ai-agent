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

    def load_documents(self, folder_path):
        if not os.path.isdir(folder_path):
            return []

        all_docs = []
        for filename in os.listdir(folder_path):
            if not filename.endswith(".txt"):
                continue

            file_path = os.path.join(folder_path, filename)
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                all_docs.extend(loader.load())
            except Exception as exc:
                print(f"略過無法讀取的檔案 {file_path}: {exc}")

        return all_docs

    def ingest_knowledge(self, input_folder="knowledge", db_dir=CHROMA_PATH):
        if self.embeddings is None:
            print(f"無法初始化 embedding 模型：{self.init_error}")
            return False

        if not os.path.isdir(input_folder):
            print(f"找不到知識資料夾：{input_folder}")
            return False

        docs = self.load_documents(input_folder)
        if not docs:
            print("找不到可匯入的 txt 文件。")
            return False

        print(f"載入 {len(docs)} 份文件")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=40,
        )
        split_docs = splitter.split_documents(docs)

        print(f"切成 {len(split_docs)} 個 chunks")

        try:
            Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=db_dir,
            )
        except Exception as exc:
            print(f"建立 Chroma DB 失敗：{exc}")
            return False

        print("Chroma DB 建立完成。")
        return True
