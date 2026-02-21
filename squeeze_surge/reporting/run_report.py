"""Main entry point for generating the strategy dashboard report."""

import logging
from pathlib import Path

from squeeze_surge.config import config
from squeeze_surge.reporting.report_data import ReportData
from squeeze_surge.reporting.html_renderer import HTMLRenderer

logger = logging.getLogger(__name__)


def generate_report(output_path: str = "data/report.html", timeframe: str = "1Hour"):
    """Collect data and render the dashboard.
    
    Args:
        output_path: Where to save the generated HTML file.
        timeframe: The data timeframe to use for backtesting.
    """
    logger.info("Starting report generation for %s timeframe...", timeframe)
    
    # 1. Collect Data
    collector = ReportData(timeframe=timeframe)
    report_data = collector.collect()
    
    # 2. Render to HTML
    renderer = HTMLRenderer()
    html_content = renderer.render(report_data)
    
    # 3. Save Output
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    logger.info("Report successfully generated at: %s", out_file.absolute())
    return out_file


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    generate_report()
