# listings/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard pour les listes de résultats
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class MatchPagination(PageNumberPagination):
    """
    Pagination spécifique pour les matchs
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class BetPagination(PageNumberPagination):
    """
    Pagination pour les paris
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
