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


class ReportAgent(Runnable):
    """Agent that generates a structured report from summary and visual insights."""

    def __init__(self):
        self.llm = ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name=settings.AWS_REGION),
            model_id=settings.BEDROCK_MODEL_ID,
            model_kwargs={
                "temperature": settings.BEDROCK_TEMPERATURE,
                "max_tokens": settings.BEDROCK_MAX_TOKENS
            }
        )

    def invoke(self, state: dict, config=None) -> dict:
        summary = state.get("summary", "")
        visual_sections = state.get("visual_sections", [])
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info("Generating final report...")

        if job_id:
            try:
                state_manager.update_progress(job_id, 80, "Finalizing report generation...")
            except Exception as e:
                logger.warning(f"Failed to update progress (ignored): {e}")

        if not summary:
            logger.warning("Summary is missing.")
            return {**state, "report_result": self._create_error_report("Summary not available.")}

        try:
            logger.info("Structuring summary into report sections...")
            structured_sections = self._structure_summary(summary)

            logger.info(f"Merging {len(visual_sections)} visual insights into report...")
            final_sections = self._merge_visualizations(structured_sections, visual_sections)

            report_result = {
                "title": self._extract_title(summary),
                "summary_brief": self._create_brief_summary(summary),
                "sections": final_sections,
                "metadata": {
                    "total_sections": len(final_sections),
                    "text_sections": len([s for s in final_sections if s.get("type") == "text"]),
                    "visual_sections": len([s for s in final_sections if s.get("type") == "visualization"]),
                    "generated_at": "",
                    "user_id": user_id,
                    "job_id": job_id
                }
            }

            logger.info(f"Report generation completed with {len(final_sections)} sections.")
            return {**state, "report_result": report_result}

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return {**state, "report_result": self._create_error_report(str(e))}

    def _structure_summary(self, summary: str) -> List[Dict[str, Any]]:
        """Convert summary into structured report sections using LLM"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
Convert the summary into structured sections with titles, levels, and keywords. Output only JSON:

{
  "sections": [
    {
      "id": "section_1",
      "title": "Section Title",
      "type": "text",
      "content": "Section content here",
      "level": 1,
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
"""),
            ("human", "{summary}")
        ])

        try:
            response = self.llm.invoke(prompt.format_messages(summary=summary))
            content = response.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                result = json.loads(json_str)
                return result.get('sections', [])
            else:
                return self._fallback_sectioning(summary)

        except Exception as e:
            logger.error(f"Error in structuring summary: {e}")
            return self._fallback_sectioning(summary)

    def _fallback_sectioning(self, summary: str) -> List[Dict[str, Any]]:
        """Fallback sectioning logic using paragraphs"""
        paragraphs = summary.split('\n\n')
        sections = []

        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) > 50:
                sections.append({
                    "id": f"section_{i + 1}",
                    "title": f"Section {i + 1}",
                    "type": "text",
                    "content": paragraph.strip(),
                    "level": 2,
                    "keywords": []
                })

        return sections

    def _merge_visualizations(self, text_sections: List[Dict], visual_sections: List[Dict]) -> List[Dict]:
        """Merge text and visualization sections by paragraph position"""
        if not visual_sections:
            return text_sections

        sorted_visuals = sorted(visual_sections,
                                key=lambda x: x.get('position', {}).get('after_paragraph', 999))

        final_sections = []
        visual_index = 0

        for i, text_section in enumerate(text_sections):
            final_sections.append(text_section)

            while (visual_index < len(sorted_visuals) and
                   sorted_visuals[visual_index].get('position', {}).get('after_paragraph', 999) <= i):
                visual = sorted_visuals[visual_index]
                final_sections.append({
                    "id": f"visual_{visual_index + 1}",
                    "title": visual.get('title', 'Untitled Visualization'),
                    "type": "visualization",
                    "visualization_type": visual.get("visualization_type"),
                    "data": visual.get('data'),
                    "insight": visual.get('insight', ''),
                    "purpose": visual.get('purpose', ''),
                    "user_benefit": visual.get('user_benefit', '')
                })
                visual_index += 1

        while visual_index < len(sorted_visuals):
            visual = sorted_visuals[visual_index]
            final_sections.append({
                "id": f"visual_{visual_index + 1}",
                "title": visual.get('title', 'Untitled Visualization'),
                "type": "visualization",
                "visualization_type": visual.get('visualization_type'),
                "data": visual.get('data'),
                "insight": visual.get('insight', ''),
                "purpose": visual.get('purpose', ''),
                "user_benefit": visual.get('user_benefit', '')
            })
            visual_index += 1

        return final_sections

    def _extract_title(self, summary: str) -> str:
        """Extract a representative title from the summary"""
        first_line = summary.split('\n')[0]
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        return first_line.strip()

    def _create_brief_summary(self, summary: str) -> str:
        """Generate a 2~3 sentence brief summary"""
        sentences = summary.replace('\n', ' ').split('.')
        important_sentences = []
        importance_keywords = ['key', 'insight', 'result', 'summary', 'finding']

        for sentence in sentences[:10]:
            if any(keyword in sentence.lower() for keyword in importance_keywords):
                important_sentences.append(sentence.strip())

        if not important_sentences:
            important_sentences = [s.strip() for s in sentences[:2] if s.strip()]

        brief = '. '.join(important_sentences[:2])
        if not brief.endswith('.'):
            brief += '.'

        return brief

    def _create_error_report(self, error_message: str) -> Dict[str, Any]:
        """Return a default error report in case of failure"""
        return {
            "title": "Report Generation Failed",
            "summary_brief": f"An error occurred while generating the report: {error_message}",
            "sections": [
                {
                    "id": "error_section",
                    "title": "Error Details",
                    "type": "text",
                    "content": f"An error occurred during report generation:\n\n{error_message}\n\nPlease try again or contact support.",
                    "level": 1,
                    "keywords": ["error", "failure"]
                }
            ],
            "metadata": {
                "total_sections": 1,
                "text_sections": 1,
                "visual_sections": 0,
                "error": True
            }
        }
