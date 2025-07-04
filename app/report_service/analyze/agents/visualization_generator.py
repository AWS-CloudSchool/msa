import os
import json
import boto3
from typing import Dict, List, Any
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from core.config import settings
from analyze.services.state_manager import state_manager
import logging

logger = logging.getLogger(__name__)


class SmartVisualAgent(Runnable):
    """Agent that generates visual sections from summary text using LLM."""

    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
            model_id=settings.BEDROCK_MODEL_ID,
            model_kwargs={"temperature": 0.7, "max_tokens": settings.BEDROCK_MAX_TOKENS}
        )

    def invoke(self, state: dict, config=None) -> dict:
        summary = state.get("summary", "")
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info("Generating smart visualizations...")

        if job_id:
            try:
                state_manager.update_progress(job_id, 60, "Generating visual sections...")
            except Exception as e:
                logger.warning(f"Failed to update job progress (ignored): {e}")

        if not summary or len(summary) < 100:
            logger.warning("Invalid or too short summary. Skipping visualization.")
            return {**state, "visual_sections": []}

        try:
            logger.info("Step 1: Analyzing context for visualization opportunities...")
            context = self._analyze_context(summary)

            if not context or "error" in context:
                logger.error(f"Failed to extract visualization context: {context}")
                return {**state, "visual_sections": []}

            logger.info(f"Step 2: Generating {len(context.get('visualization_opportunities', []))} visual sections")
            visual_sections = []

            for i, opportunity in enumerate(context.get('visualization_opportunities', [])):
                logger.info(f"Generating visualization {i + 1}...")
                visualization = self._generate_smart_visualization(context, opportunity)

                if visualization and "error" not in visualization:
                    position = self._find_best_position(summary, opportunity)
                    visual_section = {
                        "position": position,
                        "type": "visualization",
                        "title": visualization.get('title', opportunity.get('content', 'Untitled'))[:50],
                        "visualization_type": visualization.get('type'),
                        "data": self._standardize_visualization_data(visualization),
                        "insight": visualization.get('insight', ''),
                        "purpose": opportunity.get('purpose', ''),
                        "user_benefit": opportunity.get('user_benefit', '')
                    }
                    visual_sections.append(visual_section)
                    logger.info(f"Visualization {i + 1} generated: {visualization.get('type')}")
                else:
                    logger.warning(f"Visualization {i + 1} generation failed.")

            logger.info(f"Completed generation of {len(visual_sections)} visual sections.")
            return {**state, "visual_sections": visual_sections}

        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            return {**state, "visual_sections": []}

    def _analyze_context(self, summary: str) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are an assistant that analyzes summaries to identify visualization opportunities.
Return JSON with fields such as visualization_opportunities, key_concepts, and content_structure.
Ensure the response is a single valid JSON object.
"""),
            ("human", "{summary}")
        ])

        try:
            response = self.llm.invoke(prompt.format_messages(summary=summary))
            content = response.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                return json.loads(content[start_idx:end_idx + 1])
            else:
                return {"error": "Could not parse JSON."}
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {"error": str(e)}

    def _generate_smart_visualization(self, context: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        # This function would follow the same format as the _analyze_context using another prompt
        # Due to size constraints, it can be implemented similarly
        return {}

    def _find_best_position(self, summary: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        paragraphs = summary.split('\n\n')
        total_paragraphs = len(paragraphs)
        content = opportunity.get('content', '').lower()
        location_hint = opportunity.get('location_hint', 'middle')
        keywords = content.split()[:5]

        best_position = 0
        max_score = 0

        for i, paragraph in enumerate(paragraphs):
            score = sum(1 for kw in keywords if kw in paragraph.lower())
            if location_hint == 'beginning' and i < total_paragraphs // 3:
                score += 2
            elif location_hint == 'middle' and total_paragraphs // 3 <= i < 2 * total_paragraphs // 3:
                score += 2
            elif location_hint == 'end' and i >= 2 * total_paragraphs // 3:
                score += 2
            if score > max_score:
                max_score = score
                best_position = i

        return {
            "after_paragraph": best_position,
            "relevance_score": max_score
        }

    def _standardize_visualization_data(self, visualization: Dict[str, Any]) -> Dict[str, Any]:
        # Stub: Assume the visualization data is already usable.
        return visualization.get("data", {})
