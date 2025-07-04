from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph
from analyze.agents.caption_extractor import CaptionAgent
from analyze.agents.content_summarizer import SummaryAgent
from analyze.agents.visualization_generator import SmartVisualAgent
from analyze.agents.report_builder import ReportAgent
from analyze.services.state_manager import state_manager
import logging

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """Workflow state schema for YouTube Reporter"""
    job_id: str
    user_id: str
    youtube_url: str
    caption: str
    summary: str
    visual_sections: List[Dict[str, Any]]
    report_result: Dict[str, Any]
    final_output: Dict[str, Any]


class YouTubeReporterWorkflow:
    """Workflow for YouTube content analysis and report generation"""

    def __init__(self):
        logger.info("Initializing YouTube Reporter workflow...")
        self.caption_agent = CaptionAgent()
        self.summary_agent = SummaryAgent()
        self.visual_agent = SmartVisualAgent()
        self.report_agent = ReportAgent()
        self.graph = self._build_graph()
        logger.info("YouTube Reporter workflow initialized successfully")

    def _build_graph(self):
        """Build the LangGraph workflow"""
        builder = StateGraph(state_schema=GraphState)

        # Add nodes
        builder.add_node("caption_node", self.caption_agent)
        builder.add_node("summary_node", self.summary_agent)
        builder.add_node("visual_node", self.visual_agent)
        builder.add_node("report_node", self.report_agent)
        builder.add_node("finalize_node", self._finalize_result)

        # Define flow
        builder.set_entry_point("caption_node")
        builder.add_edge("caption_node", "summary_node")
        builder.add_edge("summary_node", "visual_node")
        builder.add_edge("visual_node", "report_node")
        builder.add_edge("report_node", "finalize_node")
        builder.add_edge("finalize_node", "__end__")

        return builder.compile()

    def _finalize_result(self, state: dict, config=None) -> dict:
        """Finalize the output result and insert fallback sections if needed"""
        report_result = state.get("report_result", {})
        job_id = state.get("job_id")
        user_id = state.get("user_id")

        logger.info("Finalizing result...")

        if job_id:
            try:
                state_manager.update_progress(job_id, 100, "Analysis complete!")
            except Exception as e:
                logger.warning(f"Failed to update progress: {e}")

        final_output = {
            "success": not report_result.get("metadata", {}).get("error", False),
            "title": report_result.get("title", "YouTube Analysis Report"),
            "summary": report_result.get("summary_brief", ""),
            "sections": report_result.get("sections", []),
            "statistics": {
                "total_sections": report_result.get("metadata", {}).get("total_sections", 0),
                "text_sections": report_result.get("metadata", {}).get("text_sections", 0),
                "visualizations": report_result.get("metadata", {}).get("visual_sections", 0)
            },
            "process_info": {
                "youtube_url": state.get("youtube_url", ""),
                "caption_length": len(state.get("caption", "")),
                "summary_length": len(state.get("summary", "")),
                "user_id": user_id,
                "job_id": job_id,
                "generated_at": report_result.get("metadata", {}).get("generated_at", "")
            }
        }

        for i, section in enumerate(final_output["sections"]):
            if not isinstance(section, dict):
                logger.warning("Unexpected section format: %s", section)
                final_output["sections"][i] = {
                    "id": f"section_{i + 1}",
                    "title": f"Section {i + 1}",
                    "type": "text",
                    "content": str(section),
                }
                section = final_output["sections"][i]

            if section.get("type") == "visualization":
                if not section.get("data"):
                    logger.warning("Visualization section '%s' is missing data", section.get("title"))
                    section["error"] = "Missing visualization data"
                else:
                    viz_info = section.get("visualization_type")
                    if isinstance(viz_info, dict):
                        viz_type = viz_info.get("type")
                    else:
                        if viz_info and not isinstance(viz_info, str):
                            logger.warning("Unexpected visualization_type format: %s", viz_info)
                        viz_type = viz_info

                    if viz_type == "chart" and not section["data"].get("config"):
                        section["error"] = "Missing chart configuration"
                    elif viz_type == "network" and not section["data"].get("data"):
                        section["error"] = "Missing network data"
                    elif viz_type == "flow" and not section["data"].get("data"):
                        section["error"] = "Missing flowchart data"

        logger.info("Final output generated:")
        logger.info(f"   - Title: {final_output['title']}")
        logger.info(f"   - Total Sections: {final_output['statistics']['total_sections']}")
        logger.info(f"   - Text Sections: {final_output['statistics']['text_sections']}")
        logger.info(f"   - Visualizations: {final_output['statistics']['visualizations']}")

        return {**state, "final_output": final_output}

    def process(self, youtube_url: str, job_id: str = None, user_id: str = None) -> dict:
        """Start processing from YouTube URL and build final report"""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Start YouTube Reporter: {youtube_url}")
        logger.info(f"Job ID: {job_id}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"{'=' * 60}\n")

        initial_state = {
            "job_id": job_id,
            "user_id": user_id,
            "youtube_url": youtube_url,
            "caption": "",
            "summary": "",
            "visual_sections": [],
            "report_result": {},
            "final_output": {}
        }

        try:
            if job_id:
                try:
                    state_manager.update_progress(job_id, 0, "Starting analysis...")
                except Exception as e:
                    logger.warning(f"Failed to update initial progress: {e}")

            logger.info("Step 1: Extracting transcript...")
            result = self.graph.invoke(initial_state)

            final_output = result.get("final_output", {})

            if final_output.get("success"):
                logger.info("\nReport successfully generated!")
            else:
                logger.warning("\nReport generation failed or returned error")

            return final_output

        except Exception as e:
            logger.error(f"\nWorkflow execution failed: {str(e)}")

            if job_id:
                try:
                    state_manager.update_progress(job_id, -1, f"Analysis failed: {str(e)}")
                except Exception as progress_error:
                    logger.warning(f"Failed to update failure status: {progress_error}")

            return {
                "success": False,
                "title": "Report Generation Failed",
                "summary": f"Workflow execution error: {str(e)}",
                "sections": [],
                "statistics": {
                    "total_sections": 0,
                    "text_sections": 0,
                    "visualizations": 0
                },
                "process_info": {
                    "youtube_url": youtube_url,
                    "user_id": user_id,
                    "job_id": job_id,
                    "error": str(e)
                }
            }
