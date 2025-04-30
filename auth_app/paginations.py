from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    def get_page_size(self, request):
        return request.query_params.get('page_size',10)
    

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['page_size'] = self.request.query_params.get('page_size',10)
        return response
   