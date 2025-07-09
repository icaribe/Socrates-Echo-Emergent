import os
import uuid
import asyncio
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
import json

# Environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "socrates_echo")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")
DEFAULT_OPENAI_KEY = "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"

# Initialize FastAPI
app = FastAPI(title="Socrates' Echo API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Database
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
trails_collection = db.trails
sessions_collection = db.sessions
classes_collection = db.classes
messages_collection = db.messages
api_configs_collection = db.api_configs

# Models
class UserRole(str):
    STUDENT = "student"
    TEACHER = "teacher"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
    class_ids: List[str] = []

class APIConfig(BaseModel):
    user_id: str
    provider: str
    api_key: str
    model: str
    is_validated: bool = False
    created_at: datetime

class TrailCreate(BaseModel):
    title: str
    description: str
    subject: str
    syllabus: Dict[str, Any]
    created_by: str

class Trail(BaseModel):
    id: str
    title: str
    description: str
    subject: str
    syllabus: Dict[str, Any]
    created_by: str
    created_at: datetime

class ChatMessage(BaseModel):
    message: str
    trail_id: Optional[str] = None
    session_id: Optional[str] = None

class SessionCreate(BaseModel):
    trail_id: str
    user_id: str

class Session(BaseModel):
    id: str
    trail_id: str
    user_id: str
    messages: List[Dict[str, Any]] = []
    progress: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class ClassCreate(BaseModel):
    name: str
    description: str

class Class(BaseModel):
    id: str
    name: str
    description: str
    teacher_id: str
    join_code: str
    student_ids: List[str] = []
    trail_ids: List[str] = []
    created_at: datetime

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await users_collection.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_user_api_config(user_id: str):
    """Get user's API configuration or return default"""
    config = await api_configs_collection.find_one({"user_id": user_id, "is_validated": True})
    if config:
        return config
    return {
        "provider": "openai",
        "api_key": DEFAULT_OPENAI_KEY,
        "model": "gpt-4o-mini"
    }

async def create_ai_chat(user_id: str, session_id: str):
    """Create AI chat instance with user's configuration"""
    config = await get_user_api_config(user_id)
    
    system_message = """Você é Sócrates, um tutor de filosofia especializado em educação filosófica. 
    Sua missão é guiar os estudantes através de uma jornada socrática de descoberta e aprendizado.
    
    Instruções importantes:
    1. Use perguntas socráticas para estimular o pensamento crítico
    2. Adapte-se ao nível de conhecimento do estudante
    3. Forneça explicações claras e exemplos práticos
    4. Conecte conceitos filosóficos com situações cotidianas
    5. Responda sempre em português brasileiro
    6. Mantenha um tom encorajador e inspirador
    7. Retorne suas respostas em JSON no seguinte formato:
    {
        "response": "sua resposta aqui",
        "image_prompt": "descrição para geração de imagem relacionada ao tema",
        "suggested_questions": ["pergunta 1", "pergunta 2", "pergunta 3"],
        "competency_assessment": "avaliação das competências BNCC demonstradas"
    }
    """
    
    chat = LlmChat(
        api_key=config["api_key"],
        session_id=session_id,
        system_message=system_message
    ).with_model(config["provider"], config["model"])
    
    return chat

async def generate_image(prompt: str, user_id: str):
    """Generate image using user's API configuration"""
    config = await get_user_api_config(user_id)
    
    try:
        if config["provider"] == "openai":
            image_gen = OpenAIImageGeneration(api_key=config["api_key"])
            images = await image_gen.generate_images(
                prompt=prompt,
                model="dall-e-3",
                number_of_images=1
            )
            if images and len(images) > 0 and images[0] is not None:
                return base64.b64encode(images[0]).decode('utf-8')
    except Exception as e:
        print(f"Error generating image: {str(e)}")
    
    return None

# Routes
@app.post("/api/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_id = str(uuid.uuid4())
    
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "role": user_data.role,
        "created_at": datetime.utcnow(),
        "class_ids": []
    }
    
    await users_collection.insert_one(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@app.post("/api/login")
async def login(user_data: UserLogin):
    # Find user
    user = await users_collection.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@app.get("/api/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/api-config")
async def save_api_config(config: dict, current_user: User = Depends(get_current_user)):
    """Save user's API configuration"""
    api_config = {
        "user_id": current_user.id,
        "provider": config["provider"],
        "api_key": config["api_key"],
        "model": config["model"],
        "is_validated": False,
        "created_at": datetime.utcnow()
    }
    
    # Remove existing config for this user
    await api_configs_collection.delete_many({"user_id": current_user.id})
    
    # Insert new config
    await api_configs_collection.insert_one(api_config)
    
    return {"message": "API configuration saved"}

@app.post("/api/validate-api")
async def validate_api(config: dict, current_user: User = Depends(get_current_user)):
    """Validate API key and get available models"""
    try:
        # Test the API key
        test_chat = LlmChat(
            api_key=config["api_key"],
            session_id="test",
            system_message="Test"
        ).with_model(config["provider"], config["model"])
        
        # Send test message
        test_message = UserMessage(text="Hello")
        await test_chat.send_message(test_message)
        
        # Update config as validated
        await api_configs_collection.update_one(
            {"user_id": current_user.id},
            {"$set": {"is_validated": True}}
        )
        
        # Return available models for the provider
        available_models = {
            "openai": ['gpt-4o-mini', 'gpt-4o', 'gpt-4.1', 'gpt-4.1-mini'],
            "anthropic": ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
            "gemini": ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
        }
        
        return {
            "valid": True,
            "models": available_models.get(config["provider"], [])
        }
        
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.get("/api/trails")
async def get_trails(current_user: User = Depends(get_current_user)):
    """Get available trails"""
    try:
        # Convert MongoDB documents to dictionaries
        trails = []
        async for trail in trails_collection.find({}):
            # Convert ObjectId to string for JSON serialization
            if "_id" in trail:
                trail["_id"] = str(trail["_id"])
            trails.append(trail)
        return trails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trails: {str(e)}")

@app.post("/api/trails")
async def create_trail(trail_data: TrailCreate, current_user: User = Depends(get_current_user)):
    """Create a new trail"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can create trails")
    
    trail_id = str(uuid.uuid4())
    trail = {
        "id": trail_id,
        "title": trail_data.title,
        "description": trail_data.description,
        "subject": trail_data.subject,
        "syllabus": trail_data.syllabus,
        "created_by": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    await trails_collection.insert_one(trail)
    return Trail(**trail)

@app.post("/api/trails/generate")
async def generate_trail(prompt: dict, current_user: User = Depends(get_current_user)):
    """Generate trail using AI"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can generate trails")
    
    try:
        # Create AI chat for trail generation
        chat = await create_ai_chat(current_user.id, str(uuid.uuid4()))
        
        system_prompt = f"""Você é um especialista em criação de trilhas educacionais de filosofia.
        
        Baseado no seguinte prompt: "{prompt['prompt']}"
        
        Crie uma trilha de aprendizado completa com:
        1. Título atrativo
        2. Descrição detalhada
        3. Objetivos de aprendizagem
        4. Competências da BNCC
        5. Metodologia
        6. Bibliografia
        7. Pontos-chave para avaliação
        
        Retorne em formato JSON estruturado.
        """
        
        message = UserMessage(text=system_prompt)
        response = await chat.send_message(message)
        
        # Parse response and create trail
        trail_data = json.loads(response)
        trail_id = str(uuid.uuid4())
        
        trail = {
            "id": trail_id,
            "title": trail_data.get("title", "Nova Trilha"),
            "description": trail_data.get("description", ""),
            "subject": trail_data.get("subject", "Filosofia"),
            "syllabus": trail_data,
            "created_by": current_user.id,
            "created_at": datetime.utcnow()
        }
        
        await trails_collection.insert_one(trail)
        return Trail(**trail)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trail: {str(e)}")

@app.post("/api/sessions")
async def create_session(session_data: SessionCreate, current_user: User = Depends(get_current_user)):
    """Create a new learning session"""
    session_id = str(uuid.uuid4())
    
    session = {
        "id": session_id,
        "trail_id": session_data.trail_id,
        "user_id": current_user.id,
        "messages": [],
        "progress": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await sessions_collection.insert_one(session)
    return Session(**session)

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Get session details"""
    session = await sessions_collection.find_one({"id": session_id, "user_id": current_user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return Session(**session)

@app.post("/api/chat")
async def chat_with_ai(message_data: ChatMessage, current_user: User = Depends(get_current_user)):
    """Chat with AI tutor"""
    try:
        session_id = message_data.session_id or str(uuid.uuid4())
        
        # Create AI chat
        chat = await create_ai_chat(current_user.id, session_id)
        
        # Send message
        user_message = UserMessage(text=message_data.message)
        response = await chat.send_message(user_message)
        
        # Parse AI response
        try:
            ai_response = json.loads(response)
        except:
            ai_response = {
                "response": response,
                "image_prompt": "Conceito filosófico abstrato",
                "suggested_questions": ["Pode explicar mais sobre isso?", "Como isso se aplica hoje?", "Qual é um exemplo prático?"],
                "competency_assessment": "Demonstrou interesse em aprender"
            }
        
        # Generate image if prompt provided
        image_base64 = None
        if ai_response.get("image_prompt"):
            try:
                image_base64 = await generate_image(ai_response["image_prompt"], current_user.id)
            except Exception as e:
                print(f"Error generating image: {str(e)}")
                # Continue without image if generation fails
        
        # Save message to session
        if message_data.session_id:
            await sessions_collection.update_one(
                {"id": message_data.session_id},
                {
                    "$push": {
                        "messages": {
                            "user_message": message_data.message,
                            "ai_response": ai_response["response"],
                            "image": image_base64,
                            "suggested_questions": ai_response.get("suggested_questions", []),
                            "timestamp": datetime.utcnow()
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        return {
            "response": ai_response["response"],
            "image": image_base64,
            "suggested_questions": ai_response.get("suggested_questions", []),
            "competency_assessment": ai_response.get("competency_assessment", ""),
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.post("/api/quiz/generate")
async def generate_quiz(session_data: dict, current_user: User = Depends(get_current_user)):
    """Generate quiz based on session"""
    try:
        session_id = session_data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get session
        session = await sessions_collection.find_one({"id": session_id, "user_id": current_user.id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create AI chat for quiz generation
        chat = await create_ai_chat(current_user.id, str(uuid.uuid4()))
        
        # Generate quiz based on session messages
        quiz_prompt = f"""Baseado na conversa anterior, crie um quiz de 5 perguntas sobre os temas discutidos.
        
        Retorne em formato JSON:
        {{
            "questions": [
                {{
                    "question": "pergunta aqui",
                    "options": ["opção 1", "opção 2", "opção 3", "opção 4"],
                    "correct_answer": 0,
                    "explanation": "explicação da resposta correta"
                }}
            ]
        }}
        
        Mensagens da sessão: {json.dumps(session.get('messages', []))}
        """
        
        message = UserMessage(text=quiz_prompt)
        response = await chat.send_message(message)
        
        # Parse and return quiz
        quiz_data = json.loads(response)
        return quiz_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

@app.post("/api/classes")
async def create_class(class_data: ClassCreate, current_user: User = Depends(get_current_user)):
    """Create a new class"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can create classes")
    
    class_id = str(uuid.uuid4())
    join_code = str(uuid.uuid4())[:6].upper()
    
    class_obj = {
        "id": class_id,
        "name": class_data.name,
        "description": class_data.description,
        "teacher_id": current_user.id,
        "join_code": join_code,
        "student_ids": [],
        "trail_ids": [],
        "created_at": datetime.utcnow()
    }
    
    await classes_collection.insert_one(class_obj)
    return Class(**class_obj)

@app.get("/api/classes")
async def get_classes(current_user: User = Depends(get_current_user)):
    """Get user's classes"""
    if current_user.role == UserRole.TEACHER:
        classes = await classes_collection.find({"teacher_id": current_user.id}).to_list(length=None)
    else:
        classes = await classes_collection.find({"student_ids": current_user.id}).to_list(length=None)
    
    return [Class(**cls) for cls in classes]

@app.post("/api/classes/join")
async def join_class(join_data: dict, current_user: User = Depends(get_current_user)):
    """Join a class using join code"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can join classes")
    
    join_code = join_data.get("join_code")
    if not join_code:
        raise HTTPException(status_code=400, detail="Join code required")
    
    # Find class
    class_obj = await classes_collection.find_one({"join_code": join_code})
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Add student to class
    if current_user.id not in class_obj["student_ids"]:
        await classes_collection.update_one(
            {"id": class_obj["id"]},
            {"$push": {"student_ids": current_user.id}}
        )
        
        # Add class to user
        await users_collection.update_one(
            {"id": current_user.id},
            {"$push": {"class_ids": class_obj["id"]}}
        )
    
    return {"message": "Successfully joined class"}

@app.get("/api/classes/{class_id}/students")
async def get_class_students(class_id: str, current_user: User = Depends(get_current_user)):
    """Get students in a class"""
    class_obj = await classes_collection.find_one({"id": class_id})
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    if current_user.id != class_obj["teacher_id"]:
        raise HTTPException(status_code=403, detail="Only the teacher can view students")
    
    # Get student details
    students = await users_collection.find({"id": {"$in": class_obj["student_ids"]}}).to_list(length=None)
    return [User(**student) for student in students]

@app.get("/api/students/{student_id}/progress")
async def get_student_progress(student_id: str, current_user: User = Depends(get_current_user)):
    """Get student progress for teacher"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can view student progress")
    
    # Get student's sessions
    sessions = await sessions_collection.find({"user_id": student_id}).to_list(length=None)
    
    # Calculate progress metrics
    total_sessions = len(sessions)
    total_messages = sum(len(session.get("messages", [])) for session in sessions)
    
    progress_report = {
        "student_id": student_id,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "sessions": [Session(**session) for session in sessions],
        "competency_analysis": "Análise detalhada das competências BNCC será implementada"
    }
    
    return progress_report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)