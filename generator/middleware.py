"""
Request logging middleware for tracking performance and errors.
"""
import time
import logging

logger = logging.getLogger('generator')


class RequestLoggingMiddleware:
    """Middleware to log request details and execution time."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Record start time
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR', 'unknown')}")
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing."""
        logger.error(
            f"Exception during {request.method} {request.path}: {exception}",
            exc_info=True
        )
        return None
