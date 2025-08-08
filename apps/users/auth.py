# your_app/auth.py

from rest_framework_simplejwt.authentication import JWTAuthentication

class BearerJWTAuthentication(JWTAuthentication):
    def get_header(self, request):
        """
        Extracts and returns the 'Authorization' header from the request.
        Supports 'Bearer <token>' format.
        """
        header = super().get_header(request)
        if header is None:
            return None

        parts = header.decode().split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        return parts[1].encode()  # Return token bytes
