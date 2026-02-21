"""HTML Renderer — uses Jinja2 to generate the dashboard."""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLRenderer:
    """Renders the backtest report as a self-contained HTML file."""

    def __init__(self):
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, report_data: dict) -> str:
        """Render the dashboard using the report.html template."""
        # Sanitize sensitive data (already handled in OptimizationResult, but good to double check)
        sanitized_data = self._sanitize(report_data)
        
        template = self.env.get_template("report.html")
        return template.render(data=sanitized_data)

    def _sanitize(self, data: any) -> any:
        """Recursively strip sensitive keys like API keys."""
        if isinstance(data, dict):
            return {
                k: self._sanitize(v)
                for k, v in data.items()
                if not any(s in k.lower() for s in ["api_key", "secret", "token", "password"])
            }
        elif isinstance(data, list):
            return [self._sanitize(i) for i in data]
        return data
