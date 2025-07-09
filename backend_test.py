#!/usr/bin/env python3
import requests
import json
import time
import uuid
import random
import os
from typing import Dict, Any, Optional, Tuple

# Get the backend URL from frontend/.env
BACKEND_URL = "https://ea5aca98-e130-4303-947c-614414d23e17.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test data
STUDENT_DATA = {
    "name": "Maria Silva",
    "email": f"maria.silva{uuid.uuid4().hex[:8]}@example.com",
    "password": "SecurePassword123!",
    "role": "student"
}

TEACHER_DATA = {
    "name": "João Oliveira",
    "email": f"joao.oliveira{uuid.uuid4().hex[:8]}@example.com",
    "password": "TeacherPass456!",
    "role": "teacher"
}

# Test OpenAI API key (using the default key from server.py)
TEST_API_KEY = "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"

class BackendTester:
    def __init__(self):
        self.student_token = None
        self.teacher_token = None
        self.student_user = None
        self.teacher_user = None
        self.session_id = None
        self.trail_id = None
        self.class_id = None
        self.join_code = None
        
    def run_tests(self):
        """Run all backend tests"""
        print("\n===== STARTING BACKEND TESTS =====\n")
        
        # Test user authentication
        print("\n----- Testing User Authentication System -----\n")
        self.test_user_registration()
        self.test_user_login()
        self.test_get_me()
        
        # Test API configuration
        print("\n----- Testing API Configuration System -----\n")
        self.test_save_api_config()
        self.test_validate_api()
        
        # Test trail creation
        print("\n----- Testing Learning Trails System -----\n")
        self.test_create_trail()
        self.test_generate_trail()
        self.test_get_trails()
        
        # Test session management
        print("\n----- Testing Session Management -----\n")
        self.test_create_session()
        self.test_get_session()
        
        # Test chat system
        print("\n----- Testing Chat System with AI Tutor -----\n")
        self.test_chat_with_ai()
        
        # Test quiz generation
        print("\n----- Testing Quiz Generation System -----\n")
        self.test_generate_quiz()
        
        # Test class management
        print("\n----- Testing Class Management System -----\n")
        self.test_create_class()
        self.test_get_classes()
        self.test_join_class()
        self.test_get_class_students()
        
        print("\n===== ALL BACKEND TESTS COMPLETED =====\n")
        
    def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                    token: Optional[str] = None, expected_status: int = 200) -> Tuple[Dict[str, Any], int]:
        """Make an HTTP request to the backend API"""
        url = f"{API_URL}{endpoint}"
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        elif method.lower() == "post":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        status_code = response.status_code
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"text": response.text}
            
        # Print request and response details
        print(f"Request: {method} {url}")
        if data:
            print(f"Request data: {json.dumps(data, indent=2)}")
        print(f"Response status: {status_code}")
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        # Check if status code matches expected
        if status_code != expected_status:
            print(f"WARNING: Expected status {expected_status}, got {status_code}")
            
        return response_data, status_code
        
    def test_user_registration(self):
        """Test user registration for both student and teacher"""
        print("\nTesting student registration...")
        response, status = self.make_request("post", "/register", STUDENT_DATA)
        
        if status == 200:
            self.student_token = response.get("access_token")
            self.student_user = response.get("user")
            print(f"Student registered successfully: {self.student_user['name']}")
        else:
            print("Student registration failed")
            
        print("\nTesting teacher registration...")
        response, status = self.make_request("post", "/register", TEACHER_DATA)
        
        if status == 200:
            self.teacher_token = response.get("access_token")
            self.teacher_user = response.get("user")
            print(f"Teacher registered successfully: {self.teacher_user['name']}")
        else:
            print("Teacher registration failed")
            
    def test_user_login(self):
        """Test user login for both student and teacher"""
        print("\nTesting student login...")
        login_data = {
            "email": STUDENT_DATA["email"],
            "password": STUDENT_DATA["password"]
        }
        response, status = self.make_request("post", "/login", login_data)
        
        if status == 200:
            self.student_token = response.get("access_token")
            print("Student login successful")
        else:
            print("Student login failed")
            
        print("\nTesting teacher login...")
        login_data = {
            "email": TEACHER_DATA["email"],
            "password": TEACHER_DATA["password"]
        }
        response, status = self.make_request("post", "/login", login_data)
        
        if status == 200:
            self.teacher_token = response.get("access_token")
            print("Teacher login successful")
        else:
            print("Teacher login failed")
            
    def test_get_me(self):
        """Test getting current user information"""
        print("\nTesting get current user (student)...")
        response, status = self.make_request("get", "/me", token=self.student_token)
        
        if status == 200:
            print(f"Got student profile: {response['name']}")
        else:
            print("Failed to get student profile")
            
        print("\nTesting get current user (teacher)...")
        response, status = self.make_request("get", "/me", token=self.teacher_token)
        
        if status == 200:
            print(f"Got teacher profile: {response['name']}")
        else:
            print("Failed to get teacher profile")
            
    def test_save_api_config(self):
        """Test saving API configuration"""
        print("\nTesting save API configuration...")
        config_data = {
            "provider": "openai",
            "api_key": TEST_API_KEY,
            "model": "gpt-4o-mini"
        }
        response, status = self.make_request("post", "/api-config", config_data, token=self.teacher_token)
        
        if status == 200:
            print("API configuration saved successfully")
        else:
            print("Failed to save API configuration")
            
    def test_validate_api(self):
        """Test API key validation"""
        print("\nTesting API key validation...")
        config_data = {
            "provider": "openai",
            "api_key": TEST_API_KEY,
            "model": "gpt-4o-mini"
        }
        response, status = self.make_request("post", "/validate-api", config_data, token=self.teacher_token)
        
        if status == 200 and response.get("valid"):
            print("API key validated successfully")
            print(f"Available models: {response.get('models')}")
        else:
            print("API key validation failed")
            
    def test_create_trail(self):
        """Test creating a learning trail"""
        print("\nTesting trail creation...")
        trail_data = {
            "title": "Introdução à Filosofia Socrática",
            "description": "Uma jornada pelos fundamentos do método socrático e sua aplicação contemporânea",
            "subject": "Filosofia",
            "syllabus": {
                "modules": [
                    {
                        "title": "O Método Socrático",
                        "topics": ["Maiêutica", "Ironia Socrática", "Diálogo"]
                    },
                    {
                        "title": "Aplicações Contemporâneas",
                        "topics": ["Educação", "Debate", "Pensamento Crítico"]
                    }
                ],
                "objectives": ["Compreender o método socrático", "Aplicar o diálogo socrático"]
            },
            "created_by": self.teacher_user["id"]
        }
        response, status = self.make_request("post", "/trails", trail_data, token=self.teacher_token)
        
        if status == 200:
            self.trail_id = response.get("id")
            print(f"Trail created successfully: {response.get('title')}")
        else:
            print("Failed to create trail")
            
    def test_generate_trail(self):
        """Test generating a trail using AI"""
        print("\nTesting AI trail generation...")
        prompt_data = {
            "prompt": "Crie uma trilha sobre ética e moral na filosofia contemporânea"
        }
        response, status = self.make_request("post", "/trails/generate", prompt_data, token=self.teacher_token)
        
        if status == 200:
            print(f"Trail generated successfully: {response.get('title')}")
            # Use this trail for further tests if the manual creation failed
            if not self.trail_id:
                self.trail_id = response.get("id")
        else:
            print("Failed to generate trail")
            
    def test_get_trails(self):
        """Test getting available trails"""
        print("\nTesting get trails...")
        response, status = self.make_request("get", "/trails", token=self.student_token)
        
        if status == 200:
            trails = response
            print(f"Got {len(trails)} trails")
            # If we don't have a trail_id yet, use the first one from the list
            if not self.trail_id and trails:
                self.trail_id = trails[0].get("id")
                print(f"Using trail: {trails[0].get('title')}")
        else:
            print("Failed to get trails")
            
    def test_create_session(self):
        """Test creating a learning session"""
        print("\nTesting session creation...")
        if not self.trail_id:
            print("Cannot create session: No trail ID available")
            return
            
        session_data = {
            "trail_id": self.trail_id,
            "user_id": self.student_user["id"]
        }
        response, status = self.make_request("post", "/sessions", session_data, token=self.student_token)
        
        if status == 200:
            self.session_id = response.get("id")
            print(f"Session created successfully: {self.session_id}")
        else:
            print("Failed to create session")
            
    def test_get_session(self):
        """Test getting session details"""
        print("\nTesting get session...")
        if not self.session_id:
            print("Cannot get session: No session ID available")
            return
            
        response, status = self.make_request("get", f"/sessions/{self.session_id}", token=self.student_token)
        
        if status == 200:
            print(f"Got session details: {response.get('id')}")
        else:
            print("Failed to get session details")
            
    def test_chat_with_ai(self):
        """Test chatting with AI tutor"""
        print("\nTesting chat with AI tutor...")
        if not self.session_id:
            print("Cannot chat: No session ID available")
            return
            
        chat_data = {
            "message": "O que é o método socrático?",
            "session_id": self.session_id
        }
        response, status = self.make_request("post", "/chat", chat_data, token=self.student_token)
        
        if status == 200:
            print("Chat response received successfully")
            print(f"Response includes image: {'Yes' if response.get('image') else 'No'}")
            print(f"Suggested questions: {len(response.get('suggested_questions', []))}")
        else:
            print("Failed to get chat response")
            
    def test_generate_quiz(self):
        """Test generating a quiz based on session"""
        print("\nTesting quiz generation...")
        if not self.session_id:
            print("Cannot generate quiz: No session ID available")
            return
            
        quiz_data = {
            "session_id": self.session_id
        }
        response, status = self.make_request("post", "/quiz/generate", quiz_data, token=self.student_token)
        
        if status == 200:
            print(f"Quiz generated successfully with {len(response.get('questions', []))} questions")
        else:
            print("Failed to generate quiz")
            
    def test_create_class(self):
        """Test creating a class"""
        print("\nTesting class creation...")
        class_data = {
            "name": "Filosofia Contemporânea",
            "description": "Estudo dos principais filósofos e correntes do século XX e XXI"
        }
        response, status = self.make_request("post", "/classes", class_data, token=self.teacher_token)
        
        if status == 200:
            self.class_id = response.get("id")
            self.join_code = response.get("join_code")
            print(f"Class created successfully: {response.get('name')}")
            print(f"Join code: {self.join_code}")
        else:
            print("Failed to create class")
            
    def test_get_classes(self):
        """Test getting user's classes"""
        print("\nTesting get teacher classes...")
        response, status = self.make_request("get", "/classes", token=self.teacher_token)
        
        if status == 200:
            classes = response
            print(f"Teacher has {len(classes)} classes")
        else:
            print("Failed to get teacher classes")
            
        print("\nTesting get student classes...")
        response, status = self.make_request("get", "/classes", token=self.student_token)
        
        if status == 200:
            classes = response
            print(f"Student has {len(classes)} classes")
        else:
            print("Failed to get student classes")
            
    def test_join_class(self):
        """Test joining a class"""
        print("\nTesting join class...")
        if not self.join_code:
            print("Cannot join class: No join code available")
            return
            
        join_data = {
            "join_code": self.join_code
        }
        response, status = self.make_request("post", "/classes/join", join_data, token=self.student_token)
        
        if status == 200:
            print("Student joined class successfully")
        else:
            print("Failed to join class")
            
    def test_get_class_students(self):
        """Test getting students in a class"""
        print("\nTesting get class students...")
        if not self.class_id:
            print("Cannot get students: No class ID available")
            return
            
        response, status = self.make_request("get", f"/classes/{self.class_id}/students", token=self.teacher_token)
        
        if status == 200:
            students = response
            print(f"Class has {len(students)} students")
        else:
            print("Failed to get class students")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_tests()