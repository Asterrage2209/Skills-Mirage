import logging

from scrapers.naukri.naukri_scraper import run_scraper

logger = logging.getLogger(__name__)


def run_job_pipeline():
    stats = run_scraper()
    logger.info("Job pipeline completed with stats: %s", stats)
    return stats


if __name__ == "__main__":
    run_job_pipeline()
