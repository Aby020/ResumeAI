"""
Management command to clean up test data from production.

Preserves all staff and superuser accounts. Deletes only users where
is_staff=False AND is_superuser=False, along with their associated
Resume and ResumeAnalysis records and Cloudinary files.
"""

import sys

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from resume.models import Resume, ResumeAnalysis


class Command(BaseCommand):
    help = "Delete test users and their data (resumes, analyses, Cloudinary files). DRY-RUN by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-dry-run",
            action="store_true",
            help="Actually perform deletions. Without this flag, runs in DRY-RUN mode.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required confirmation for real deletion (with --no-dry-run).",
        )

    def handle(self, *args, **options):
        dry_run = not options["no_dry_run"]
        confirmed = options["confirm"]

        if not dry_run and not confirmed:
            raise CommandError(
                "Real deletion requires --no-dry-run AND --confirm flags. "
                "Run with --help for usage."
            )

        # Identify test users (non-staff, non-superuser)
        test_users = User.objects.filter(is_staff=False, is_superuser=False)
        test_user_count = test_users.count()

        if test_user_count == 0:
            self.stdout.write(self.style.SUCCESS("No test users found. Nothing to clean up."))
            return

        # Collect all resumes for these users
        test_resumes = Resume.objects.filter(user__in=test_users)
        test_resume_count = test_resumes.count()

        # Collect all analyses for these resumes
        test_analyses = ResumeAnalysis.objects.filter(resume__in=test_resumes)
        test_analysis_count = test_analyses.count()

        # Cloudinary file counts
        resume_files = list(test_resumes.exclude(file="").values_list("file", flat=True))
        job_image_files = list(
            test_analyses.exclude(job_image="").values_list("job_image", flat=True)
        )

        # Summary
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.NOTICE("CLEANUP TEST DATA - SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Mode: {'DRY-RUN' if dry_run else 'REAL DELETION'}")
        self.stdout.write(f"Test users to delete: {test_user_count}")
        self.stdout.write(f"Resume records to delete: {test_resume_count}")
        self.stdout.write(f"ResumeAnalysis records to delete: {test_analysis_count}")
        self.stdout.write(f"Cloudinary resume files: {len(resume_files)}")
        self.stdout.write(f"Cloudinary job image files: {len(job_image_files)}")
        self.stdout.write("-" * 60)

        if dry_run:
            self.stdout.write(self.style.NOTICE("DRY-RUN: No deletions performed."))
            if resume_files:
                self.stdout.write("Resume files that would be deleted:")
                for f in resume_files:
                    self.stdout.write(f"  - {f}")
            if job_image_files:
                self.stdout.write("Job image files that would be deleted:")
                for f in job_image_files:
                    self.stdout.write(f"  - {f}")
            self.stdout.write("=" * 60)
            self.stdout.write(
                "To execute real deletion, run:\n"
                "  python manage.py cleanup_test_data --no-dry-run --confirm"
            )
            return

        # REAL DELETION PATH
        self.stdout.write(self.style.WARNING("Executing REAL deletion..."))

        # Track deletions
        deleted_cloudinary_files = 0
        failed_cloudinary_files = []

        # 1. Delete Cloudinary resume files
        for resume in test_resumes.iterator():
            if resume.file:
                try:
                    storage = resume.file.storage
                    if storage.exists(resume.file.name):
                        storage.delete(resume.file.name)
                        deleted_cloudinary_files += 1
                        self.stdout.write(f"  Deleted resume file: {resume.file.name}")
                    else:
                        self.stdout.write(
                            f"  Resume file not found (skipped): {resume.file.name}"
                        )
                except Exception as e:
                    failed_cloudinary_files.append(f"resume:{resume.file.name}:{e}")
                    self.stdout.write(
                        self.style.ERROR(f"  Failed to delete resume file {resume.file.name}: {e}")
                    )

        # 2. Delete Cloudinary job image files
        for analysis in test_analyses.iterator():
            if analysis.job_image:
                try:
                    storage = analysis.job_image.storage
                    if storage.exists(analysis.job_image.name):
                        storage.delete(analysis.job_image.name)
                        deleted_cloudinary_files += 1
                        self.stdout.write(f"  Deleted job image: {analysis.job_image.name}")
                    else:
                        self.stdout.write(
                            f"  Job image not found (skipped): {analysis.job_image.name}"
                        )
                except Exception as e:
                    failed_cloudinary_files.append(f"job_image:{analysis.job_image.name}:{e}")
                    self.stdout.write(
                        self.style.ERROR(f"  Failed to delete job image {analysis.job_image.name}: {e}")
                    )

        # 3. Delete users (CASCADE handles Resume and ResumeAnalysis)
        deleted_user_count, deleted_objects = test_users.delete()

        # Extract counts from deleted_objects
        deleted_resume_count = deleted_objects.get("resume.Resume", 0)
        deleted_analysis_count = deleted_objects.get("resume.ResumeAnalysis", 0)

        # Final summary
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("CLEANUP COMPLETE"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Users deleted: {deleted_user_count}")
        self.stdout.write(f"Resume records deleted: {deleted_resume_count}")
        self.stdout.write(f"ResumeAnalysis records deleted: {deleted_analysis_count}")
        self.stdout.write(f"Cloudinary files deleted: {deleted_cloudinary_files}")
        if failed_cloudinary_files:
            self.stdout.write(self.style.ERROR(f"Cloudinary files failed: {len(failed_cloudinary_files)}"))
            for f in failed_cloudinary_files:
                self.stdout.write(f"  - {f}")
        else:
            self.stdout.write("Cloudinary files failed: 0")
        self.stdout.write("=" * 60)
        self.stdout.write("Admin/superuser accounts preserved.")