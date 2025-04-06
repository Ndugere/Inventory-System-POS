from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from .serializers import LoginSerializer  # Assuming you have a serializer for login

class Login(APIView):
    
    def post(self, request):  # Added self as the first argument
        serializer = LoginSerializer(data=request.data)  # Validate input data
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=username, password=password)  # Authenticate user
            
            if user:
                login(request, user)  # Log in user
                return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
