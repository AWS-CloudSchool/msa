from chatbot.chains.qa_chain import build_qa_chain
from chatbot.retrievers.kb_retriever import get_kb_retriever, get_llm
import re

# Relevance score threshold (documents below this score will be ignored)
RELEVANCE_THRESHOLD = 0.5

def extract_best_time_and_text_with_ai(content: str, question: str, llm) -> str:
    """Extracts the most relevant timestamped sentence from the content using AI"""
    pattern = r'\[at (\d+\.?\d*) seconds?\]\s*([^\n\r]+)'
    matches = re.findall(pattern, content)
    
    if not matches:
        return "No timestamped sentences found."
    
    if len(matches) == 1:
        sec, txt = matches[0]
        seconds = float(sec)
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        time_str = f"{minutes}:{remaining_seconds:02d}" if minutes > 0 else f"{remaining_seconds}s"
        return f"{time_str}: {txt.strip()}"
    
    try:
        # Build prompt for LLM to select the best sentence
        evaluation_prompt = f"""
Select the most relevant sentence based on the following question.

Question: {question}

Sentences:
"""
        for i, (sec, txt) in enumerate(matches, 1):
            evaluation_prompt += f"{i}. {txt.strip()}\n"
        
        evaluation_prompt += "\nRespond with the number only."

        response = llm.invoke(evaluation_prompt)
        result = response.content.strip() if hasattr(response, 'content') else str(response).strip()

        number_match = re.search(r'\d+', result)
        if number_match:
            selected_idx = int(number_match.group()) - 1
            if 0 <= selected_idx < len(matches):
                sec, txt = matches[selected_idx]
                seconds = float(sec)
                minutes = int(seconds // 60)
                remaining_seconds = int(seconds % 60)
                time_str = f"{minutes}:{remaining_seconds:02d}" if minutes > 0 else f"{remaining_seconds}s"
                return f"{time_str}: {txt.strip()}"
    
    except Exception as e:
        print(f"[extract_best_time_and_text_with_ai] AI evaluation failed: {e}")
    
    # Fallback to first match if AI fails
    sec, txt = matches[0]
    seconds = float(sec)
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    time_str = f"{minutes}:{remaining_seconds:02d}" if minutes > 0 else f"{remaining_seconds}s"
    return f"{time_str}: {txt.strip()}"

def extract_video_id_from_content(content: str) -> str:
    """Extract video ID from content filename like 'OA7LIkxp3_o_xxx.txt'"""
    video_pattern = r'([A-Za-z0-9_-]{11})_[a-f0-9]+\.txt'
    matches = re.findall(video_pattern, content)
    
    if matches:
        return f"YouTube ID: {matches[0]}"
    
    return "No video ID found."

def answer_question(question: str):
    retriever = get_kb_retriever()
    llm = get_llm()

    docs = retriever(question)

    # Filter high quality documents using score threshold
    high_quality_docs = [
        doc for doc in docs
        if doc.metadata.get("score", 1.0) >= RELEVANCE_THRESHOLD
    ]
    
    relevance_scores = [doc.metadata.get("score", 0.0) for doc in docs]

    if high_quality_docs:
        print("[answer_question] Found relevant KB documents. Using Claude + KB.")

        # Deduplicate based on time and text
        unique_docs = []
        seen_content = set()
        
        for doc in high_quality_docs:
            time_and_text = extract_best_time_and_text_with_ai(doc.page_content, question, llm)
            if time_and_text not in seen_content:
                seen_content.add(time_and_text)
                unique_docs.append((doc, time_and_text))
        
        for i, (doc, time_and_text) in enumerate(unique_docs, 1):
            print(f"   - Selected document {i}: {time_and_text}")
        
        # Combine context and run QA chain
        context = "\n".join([doc.page_content for doc in high_quality_docs])
        qa_chain = build_qa_chain()
        response = qa_chain.invoke({"context": context, "question": question})
        
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return {
            'answer': answer,
            'source_type': 'KB',
            'documents_found': len(high_quality_docs),
            'relevance_scores': relevance_scores[:5]
        }

    else:
        print("[answer_question] No KB match found. Using Claude fallback.")
        response = llm.invoke(question)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return {
            'answer': answer,
            'source_type': 'FALLBACK',
            'documents_found': 0,
            'relevance_scores': relevance_scores[:5] if relevance_scores else []
        }
