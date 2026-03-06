"""Quick test: scrape a few NPTEL + SWAYAM courses and print their skill tags."""
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

print("=" * 60)
print("TESTING NPTEL SCRAPER")
print("=" * 60)

from scrapers.courses.nptel_scraper import scrape_nptel
courses = scrape_nptel(max_courses=5)
print(f"\nGot {len(courses)} NPTEL courses\n")
for c in courses:
    print(f"Name: {c['name']}")
    print(f"  Domain:      {c['domain']}")
    print(f"  Institution: {c['institution']}")
    print(f"  Skills:      {c['skill_tags']}")
    print()

print("=" * 60)
print("TESTING SWAYAM SCRAPER")
print("=" * 60)

from scrapers.courses.swayam_scraper import scrape_swayam
courses2 = scrape_swayam(max_courses=5)
print(f"\nGot {len(courses2)} SWAYAM courses\n")
for c in courses2:
    print(f"Name: {c['name']}")
    print(f"  Domain:      {c['domain']}")
    print(f"  Institution: {c['institution']}")
    print(f"  Skills:      {c['skill_tags']}")
    print()
