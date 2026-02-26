# core/pagination.py
from rest_framework.pagination import PageNumberPagination, CursorPagination as DRFCursorPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    """
    Standard pagination for all list endpoints
    Usage: ?page=1&limit=20&sort=-created_at
    """
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'pagination': {
                'page': self.page.number,
                'limit': self.page.paginator.per_page,
                'total': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages
            }
        })


class CursorPagination(DRFCursorPagination):
    """For infinite scroll"""
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    ordering = '-created_at'