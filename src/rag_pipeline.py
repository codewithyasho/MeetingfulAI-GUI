from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_classic.chains import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from dotenv import load_dotenv
import torch
import os
load_dotenv()


def rag_engine(transcript: str):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cuda"} if torch.cuda.is_available() else {
            "device": "cpu"}
    )

    # loader = TextLoader(transcript)
    # documents = loader.load()

    documents = [Document(page_content=transcript)]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=100)
    splitted_docs = text_splitter.split_documents(documents)

    vectorstore = InMemoryVectorStore.from_documents(splitted_docs, embeddings)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,

            "fetch_k": 10,

            "lambda_mult": 0.5
        }
    )

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.2)

    # The chain expects {context} and {input}
    prompt = ChatPromptTemplate.from_template("""
            You are an expert meeting assistant. Answer the user's question 
            based ONLY on the meeting transcript context provided below.

            If the answer is not found in the context, say: 
            "I could not find this information in the transcript."

            Always be concise and precise. If quoting someone, mention it clearly.  

            <context>
            {context}
            </context>

            Question: {input}
        """)

    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, document_chain)

    return rag_chain
