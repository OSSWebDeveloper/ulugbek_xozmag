"""Har kassirning ochiq savati alohida; ombor va sotuv tarixi umumiy."""
from django.db.models import Q
from django.shortcuts import get_object_or_404


def hujjat(request, model, pk):
    document = get_object_or_404(model.objects.filter(
        Q(kassir=request.user) | Q(kassir__isnull=True)), pk=pk)
    if document.kassir_id is None:
        model.objects.filter(pk=pk, kassir__isnull=True).update(kassir=request.user)
        document.refresh_from_db()
        if document.kassir_id != request.user.pk:
            from django.http import Http404
            raise Http404
    return document
