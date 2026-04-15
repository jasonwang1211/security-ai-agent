import os
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_documents(folder_path):
    all_docs = []
    for f in os.listdir(folder_path):
        if f.endswith(".txt"):
            loader = TextLoader(os.path.join(folder_path, f), encoding="utf-8")
            all_docs.extend(loader.load())
    return all_docs

def main():
    INPUT_FOLDER = "knowledge"
    DB_DIR = "chroma_db"

    docs = load_documents(INPUT_FOLDER)

    print(f"📂 載入 {len(docs)} 份文件")

    # 🔥 改這裡（更細）
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=40
    )
    split_docs = splitter.split_documents(docs)

    print(f"✂️ 切成 {len(split_docs)} chunks")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=DB_DIR
    )

    print("✅ Chroma DB 建立完成！")

if __name__ == "__main__":
    main()