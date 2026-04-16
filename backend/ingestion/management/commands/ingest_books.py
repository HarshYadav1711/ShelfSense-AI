from django.core.management.base import BaseCommand

from ingestion.services import run_book_ingestion


class Command(BaseCommand):
    help = "Fetches a repeatable batch of books from books.toscrape.com and stores them locally."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10)

    def handle(self, *args, **options):
        run = run_book_ingestion(limit=options["limit"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Run {run.id} finished with status={run.status} "
                f"processed={run.processed_count} failed={run.failed_count}"
            )
        )
