# utils/api_response.py
from django.http import JsonResponse

def api_response(status_code=200, message="", data=None):
    """
    Standard API response format
    Args:
        status_code: HTTP status code
        message: Human-readable message
        data: Response payload (dict/list/None)
    Returns:
        JsonResponse with standardized format
    """
    response_data = {
        'status': 'success' if 200 <= status_code < 300 else 'error',
        'code': status_code,
        'message': message,
        'data': data if data is not None else {}
    }
    
    return JsonResponse(response_data, status=status_code)