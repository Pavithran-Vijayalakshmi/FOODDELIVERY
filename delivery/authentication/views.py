from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import authenticate
from user.models import User
from user.serializer import UserSerializer
from .serializer import CustomTokenObtainPairSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "User registered successfully. Please log in to access your account."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message":str("Login Successful"),
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Changed from AllowAny to ensure only authenticated users can logout

    def post(self, request):
        try:
            
            # Get both tokens from the request
            refresh_token = request.data.get("refresh")
            
            # Blacklist the refresh token
            if refresh_token:
                refresh = RefreshToken(refresh_token)
                refresh.blacklist()
            
            return Response(
                {"message": "Successfully logged out. All tokens invalidated."},
                status=status.HTTP_205_RESET_CONTENT
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            
from django.shortcuts import render

def payment_view(request):
    # Add any context data you need to pass to the template
    context = {
        'amount': 100.00*100,  # example value
        'currency': 'INR',  # example value
    }
    return render(request, 'registration/payment.html', context)