import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()


def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript)


def build_chain(system_prompt: str):
    llm = ChatMistralAI(model_name="mistral-small-latest", temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}"),
    ])

    return prompt | llm | StrOutputParser()


def extract_action_items(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. Extract all action items from the transcript. "
        "For each provide:\n- Task description\n- Owner (who is responsible)\n- Deadline (if mentioned)\n"
        "Format as a numbered list. If none found, say 'No action items found.'"
    )

    result = chain.invoke({"text": transcript})

    # with open("action_items.txt", "w", encoding="utf-8") as f:
    #     f.write(result)

    return result


def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. Extract all key decisions made. "
        "Format as a numbered list. If none found, say 'No key decisions found.'"
    )
    result = chain.invoke({"text": transcript})

    # with open("key_decisions.txt", "w", encoding="utf-8") as f:
    #     f.write(result)

    return result


def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "Extract all unresolved questions or topics needing follow-up from the transcript. "
        "Format as a numbered list. If none found, say 'No open questions found.'"
        "Dont make up questions."
    )
    result = chain.invoke({"text": transcript})

    # with open("open_questions.txt", "w", encoding="utf-8") as f:
    #     f.write(result)

    return result


# main summarization function that uses the above helper functions
def summarize_transcript(transcript: str) -> dict:
    llm = ChatMistralAI(model_name="mistral-small-latest", temperature=0.2)

    # 1. Summarize individual chunks
    map_prompt = ChatPromptTemplate.from_template(
        "Summarize this part of a video transcript concisely:\n\n{text}"
    )
    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)
    print(f"[INFO] Summarizing {len(chunks)} chunks...")

    chunk_summaries = [map_chain.invoke({"text": chunk}) for chunk in chunks]

    # 2. Combine partial summaries into one text
    combined_partial_summaries = "\n\n".join(chunk_summaries)

    # with open("combined_partial_summaries.txt", "w", encoding="utf-8") as f:
    #     f.write(combined_partial_summaries)

    # 3. Combine into final bullet points
    final_prompt = ChatPromptTemplate.from_template(
        """
        You are a professional video summarizer. 
        Combine these partial summaries into one final professional video summary using bullet points and give suitable title.
        
        Summaries:
        {text}
        """
    )

    final_chain = final_prompt | llm | StrOutputParser()

    # 4. Full summary
    full_summary = final_chain.invoke(
        {"text": combined_partial_summaries})

    with open("full_summary.txt", "w", encoding="utf-8") as f:
        f.write(full_summary)

    # 5. Extract actionable items, key decisions, and open questions from the combined partial summaries
    actionable_items = extract_action_items(combined_partial_summaries)
    key_decisions = extract_key_decisions(combined_partial_summaries)
    open_questions = extract_questions(combined_partial_summaries)

    return {
        "summary": full_summary,
        "action_items": actionable_items,
        "key_decisions": key_decisions,
        "open_questions": open_questions
    }
