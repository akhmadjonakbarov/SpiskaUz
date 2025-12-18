from apps.document.models import Document


class CalculateService:
    def calculate_salary(self, request):
        documents = (
            Document.objects.filter(
                deleted_at__isnull=True,
                created_by=request.user,
            ).prefetch_related(
                ""
            )
        )