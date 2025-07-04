import os
import boto3
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from core.config import settings
from analyze.services.state_manager import state_manager
import logging

logger = logging.getLogger(__name__)


class SummaryAgent(Runnable):
    """Agent that summarizes a YouTube caption into key insights."""

    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
            model_id=settings.BEDROCK_MODEL_ID,
            model_kwargs={"temperature": settings.BEDROCK_TEMPERATURE, "max_tokens": settings.BEDROCK_MAX_TOKENS}
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an assistant that summarizes YouTube video captions into structured insights.

**Summarization Criteria:**
1. **Overall Summary**: Describe the general theme and message of the video in a concise way.
2. **Key Points**: Extract core arguments, conclusions, or findings.
3. **Contextual Details**: Mention context, conditions, related insights.
4. **Actionable Takeaways**: Summarize direct implications, suggestions, or results.
5. **Additional Information**: Add references, metrics, time markers, or other important mentions.

**Expected Output:**
- 1 paragraph summary
- 3~5 bullet points with key findings
- Short and clear
- 800 words max"""),
            ("human", "Here is the YouTube caption to summarize:\n\n{caption}")
        ])

    def invoke(self, state: dict, config=None):
        caption = state.get("caption", "")
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info("Starting summary generation...")

        if job_id:
            try:
                state_manager.update_progress(job_id, 40, "Summarizing the YouTube caption...")
            except Exception as e:
                logger.warning(f"Failed to update state (ignored): {e}")

        if not caption or "No caption detected" in caption or "Caption extraction failed" in caption:
            logger.warning("Invalid or missing caption.")
            return {**state, "summary": "No valid caption found. Caption may be missing or failed to extract."}

        try:
            processed_caption = self._preprocess_caption(caption)

            response = self.llm.invoke(
                self.prompt.format_messages(caption=processed_caption)
            )
            summary = response.content.strip()

            if len(summary) < 500:
                logger.warning("Summary appears too short. Attempting enhancement...")
                followup_prompt = ChatPromptTemplate.from_messages([
                    ("system", "The initial summary was too short. Please provide a more detailed response."),
                    ("human", f"Original caption:\n{processed_caption}\n\nInitial summary:\n{summary}\n\nPlease elaborate further.")
                ])
                response = self.llm.invoke(followup_prompt.format_messages())
                summary = response.content.strip()

            logger.info(f"Summary generation completed. Length: {len(summary)}")
            return {**state, "summary": summary}

        except Exception as e:
            error_msg = f"Error during summary generation: {str(e)}"
            logger.error(error_msg)
            return {**state, "summary": error_msg}

    def _preprocess_caption(self, caption: str) -> str:
        """Trims and extracts the most important parts of the caption for summarization."""
        if len(caption) <= 6000:
            return caption

        logger.info(f"Caption too long ({len(caption)} chars). Extracting highlights...")

        sentences = caption.replace('\n', ' ').split('.')

        importance_keywords = [
            'summary', 'key point', 'insight', 'finding', 'result', 'conclusion',
            'first', 'second', 'third', 'main',
            'score', 'criteria', 'impact', 'outcome', 'recommendation', 'evidence',
            'context', 'reference', 'trend'
        ]

        important_sentences = []
        regular_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            score = sum(1 for keyword in importance_keywords if keyword.lower() in sentence.lower())
            if score > 0:
                important_sentences.append((score, sentence))
            else:
                regular_sentences.append(sentence)

        important_sentences.sort(key=lambda x: x[0], reverse=True)

        result_sentences = []
        result_sentences.extend(sentences[:10])
        result_sentences.extend([s[1] for s in important_sentences[:30]])

        step = max(1, len(regular_sentences) // 20)
        result_sentences.extend(regular_sentences[::step][:20])
        result_sentences.extend(sentences[-10:])

        seen = set()
        final_sentences = []
        for sentence in result_sentences:
            if sentence not in seen and sentence.strip():
                seen.add(sentence)
                final_sentences.append(sentence)

        processed = '. '.join(final_sentences)

        if len(processed) > 6000:
            processed = processed[:6000] + "..."

        logger.info(f"Caption preprocessing complete: {len(caption)} -> {len(processed)} chars")
        return processed
