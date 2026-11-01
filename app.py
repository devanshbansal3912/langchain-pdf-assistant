from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain


def main():
    load_dotenv()
    st.set_page_config(page_title="Ask your PDF")
    st.header("Ask your PDF")

    if "chain" not in st.session_state:
        st.session_state.chain = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    pdf = st.file_uploader("Upload your PDF", type="pdf")

    if pdf is not None and st.session_state.chain is None:
        pdf_reader = PdfReader(pdf)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)

        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        knowledge_base = FAISS.from_texts(chunks, embeddings)

        if st.session_state.chain is None:
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            st.session_state.chain = ConversationalRetrievalChain.from_llm(
                llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash"),
                retriever=knowledge_base.as_retriever(search_kwargs={"k": 2}),
                memory=memory
            )

        user_question = st.text_input("Ask a question about your PDF:")
        if user_question:
            response = st.session_state.chain({"question": user_question})
            st.session_state.chat_history.append(("You", user_question))
            st.session_state.chat_history.append(("Bot", response["answer"]))

        for role, message in st.session_state.chat_history:
            st.write(f"**{role}:** {message}")


if __name__ == "__main__":
    main()