# cli_qa.py

from dotenv import load_dotenv
load_dotenv()

from rag.qa_service import QAService


def main():

    # service = QAService(embedding_backend="huggingface")
    service = QAService()

    print("RAG CLI (Qdrant + LlamaIndex + Gemini)")
    print("Type your question, or 'exit' to quit.")

    while True:
        question = input("\nYou: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        try:
            answer = service.answer(question)
            print("\nAssistant:", answer)
        except Exception as e:
            print("\n[Error]", e)


if __name__ == "__main__":
    main()
