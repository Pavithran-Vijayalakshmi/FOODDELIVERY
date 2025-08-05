from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import authenticate
from user.models import User
from user.serializer import UserSerializer
from .serializer import CustomTokenObtainPairSerializer, RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from common.response import api_response
from django.contrib.auth import login



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save()
            return api_response(
                message= "User registered successfully. Please log in to access your account."
            , status_code=status.HTTP_201_CREATED)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
class RestaurantRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'user_type': 'restaurant_owner'})
        if serializer.is_valid():
            
            serializer.save()
            return api_response(
                message= "User registered successfully. Please log in to access your account.",
                data = serializer.data
            , status_code=status.HTTP_201_CREATED)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
class DeliveryPartnerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'user_type': 'delivery_partner'})
        if serializer.is_valid():
            
            serializer.save()
            return api_response(
                message= "User registered successfully. Please log in to access your account.",
                data = serializer.data
            , status_code=status.HTTP_201_CREATED)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
class DeliveryPersonRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'user_type': 'delivery_person'})
        if serializer.is_valid():
            
            serializer.save()
            return api_response(
                message= "User registered successfully. Please log in to access your account.",
                data = serializer.data
            , status_code=status.HTTP_201_CREATED)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         email = request.data.get("email")
#         password = request.data.get("password")
#         user = authenticate(request, email=email, password=password) 
#         if user is not None:
#             refresh = RefreshToken.for_user(user)
#             return api_response(
#                 message = str("Login Successful"),
#                 data = 
#                 {
#                     "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#                 }
#                 )
#         return api_response(message = "Invalid credentials", status_code=status.HTTP_401_UNAUTHORIZED)
    


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        # Check if user exists and is admin/staff
        if user is not None and (user.is_staff or user.is_superuser):
            refresh = RefreshToken.for_user(user)
            
            # Add admin-specific claims to the token if needed
            refresh['is_admin'] = user.is_staff
            refresh['is_superadmin'] = user.is_superuser
            
            return api_response(
                message="Admin Login Successful",
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "email": user.email,
                        "name": user.name,
                        "is_superuser": user.is_superuser,
                    }
                },
                status_code=status.HTTP_200_OK
            )
        
        # Return different messages for invalid credentials vs non-admin users
        if user is not None:
            return api_response(
                message="Access Denied: Not an admin account",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        return api_response(
            message="Invalid credentials",
            status_code=status.HTTP_401_UNAUTHORIZED
        )



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
            
            return api_response(
                message =  "Successfully logged out. All tokens invalidated.",
                status_code=status.HTTP_205_RESET_CONTENT
            )
            
        except Exception as e:
            return api_response(
                data =  str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
            


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []
    queryset = User.objects.all()
    def post(self, request):

        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response(
            {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Login successful",
                "data": {
                    "user_id": user.id,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }
            },
            status=status.HTTP_200_OK
        )