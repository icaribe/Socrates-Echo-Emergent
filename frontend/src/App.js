import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/login`, {
        email,
        password
      });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (name, email, password, role) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/register`, {
        name,
        email,
        password,
        role
      });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login/Register Component
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'student'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let result;
      if (isLogin) {
        result = await login(formData.email, formData.password);
      } else {
        result = await register(formData.name, formData.email, formData.password, formData.role);
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-700 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Socrates' Echo</h1>
          <p className="text-purple-200">Tutoria de IA para Educação Filosófica</p>
        </div>

        <div className="flex mb-6">
          <button
            className={`flex-1 py-2 px-4 rounded-l-lg transition-colors ${
              isLogin 
                ? 'bg-purple-600 text-white' 
                : 'bg-purple-800/50 text-purple-200 hover:bg-purple-700/50'
            }`}
            onClick={() => setIsLogin(true)}
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 px-4 rounded-r-lg transition-colors ${
              !isLogin 
                ? 'bg-purple-600 text-white' 
                : 'bg-purple-800/50 text-purple-200 hover:bg-purple-700/50'
            }`}
            onClick={() => setIsLogin(false)}
          >
            Registrar
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <input
              type="text"
              name="name"
              placeholder="Nome completo"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          )}

          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />

          <input
            type="password"
            name="password"
            placeholder="Senha"
            value={formData.password}
            onChange={handleChange}
            required
            className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />

          {!isLogin && (
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="student">Estudante</option>
              <option value="teacher">Professor</option>
            </select>
          )}

          {error && (
            <div className="text-red-300 text-sm text-center">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? 'Processando...' : (isLogin ? 'Entrar' : 'Criar Conta')}
          </button>
        </form>
      </div>
    </div>
  );
};

// API Configuration Component
const APIConfig = ({ onClose }) => {
  const [config, setConfig] = useState({
    provider: 'openai',
    api_key: '',
    model: 'gpt-4o-mini'
  });
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);

  const handleValidateAPI = async () => {
    setIsValidating(true);
    setValidationResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/validate-api`, config);
      setValidationResult(response.data);
      if (response.data.valid) {
        setAvailableModels(response.data.models);
        await axios.post(`${API_BASE_URL}/api/api-config`, config);
      }
    } catch (error) {
      setValidationResult({ valid: false, error: error.response?.data?.detail || 'Validation failed' });
    } finally {
      setIsValidating(false);
    }
  };

  const providerModels = {
    openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4.1', 'gpt-4.1-mini'],
    anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
    gemini: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-purple-900/90 backdrop-blur-md rounded-2xl p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Configurar API</h2>
          <button
            onClick={onClose}
            className="text-purple-300 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-purple-200 mb-2">Provedor</label>
            <select
              value={config.provider}
              onChange={(e) => setConfig({...config, provider: e.target.value, model: providerModels[e.target.value][0]})}
              className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>

          <div>
            <label className="block text-purple-200 mb-2">API Key</label>
            <input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({...config, api_key: e.target.value})}
              placeholder="Insira sua API key"
              className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-purple-200 mb-2">Modelo</label>
            <select
              value={config.model}
              onChange={(e) => setConfig({...config, model: e.target.value})}
              className="w-full px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              {(availableModels.length > 0 ? availableModels : providerModels[config.provider]).map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleValidateAPI}
            disabled={isValidating || !config.api_key}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isValidating ? 'Validando...' : 'Validar API'}
          </button>

          {validationResult && (
            <div className={`p-3 rounded-lg text-sm ${
              validationResult.valid 
                ? 'bg-green-600/20 text-green-300 border border-green-600/30' 
                : 'bg-red-600/20 text-red-300 border border-red-600/30'
            }`}>
              {validationResult.valid ? 'API validada com sucesso!' : `Erro: ${validationResult.error}`}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Chat Component
const Chat = ({ onBack }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);

  const sendMessage = async (message) => {
    if (!message.trim()) return;

    setIsLoading(true);
    const userMessage = { type: 'user', content: message, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message,
        session_id: sessionId
      });

      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        image: response.data.image,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
      setSuggestedQuestions(response.data.suggested_questions || []);
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'error',
        content: 'Desculpe, ocorreu um erro. Tente novamente.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setInputMessage('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-700">
      {/* Header */}
      <div className="bg-purple-900/50 backdrop-blur-md border-b border-purple-600/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="text-purple-300 hover:text-white transition-colors"
            >
              ← Voltar
            </button>
            <h1 className="text-2xl font-bold text-white">Sócrates</h1>
          </div>
          <div className="text-purple-200 text-sm">
            Sessão: {sessionId ? sessionId.substring(0, 8) : 'Nova'}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-purple-200 py-8">
            <h2 className="text-2xl font-bold mb-4">Bem-vindo ao Sócrates' Echo</h2>
            <p className="mb-4">Eu sou Sócrates, seu tutor de filosofia. Como posso ajudá-lo em sua jornada filosófica hoje?</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <button
                onClick={() => sendMessage("O que é filosofia?")}
                className="p-4 bg-purple-800/30 border border-purple-600/30 rounded-lg text-purple-200 hover:bg-purple-700/30 transition-colors"
              >
                O que é filosofia?
              </button>
              <button
                onClick={() => sendMessage("Fale sobre Platão")}
                className="p-4 bg-purple-800/30 border border-purple-600/30 rounded-lg text-purple-200 hover:bg-purple-700/30 transition-colors"
              >
                Fale sobre Platão
              </button>
              <button
                onClick={() => sendMessage("O que é o bem?")}
                className="p-4 bg-purple-800/30 border border-purple-600/30 rounded-lg text-purple-200 hover:bg-purple-700/30 transition-colors"
              >
                O que é o bem?
              </button>
              <button
                onClick={() => sendMessage("Explique a ética")}
                className="p-4 bg-purple-800/30 border border-purple-600/30 rounded-lg text-purple-200 hover:bg-purple-700/30 transition-colors"
              >
                Explique a ética
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-2xl p-4 ${
              message.type === 'user' 
                ? 'bg-purple-600 text-white' 
                : message.type === 'error'
                ? 'bg-red-600/20 text-red-300 border border-red-600/30'
                : 'bg-white/10 backdrop-blur-md text-white'
            }`}>
              {message.image && (
                <img
                  src={`data:image/png;base64,${message.image}`}
                  alt="Generated visual"
                  className="w-full rounded-lg mb-3"
                />
              )}
              <p className="whitespace-pre-wrap">{message.content}</p>
              <div className="text-xs opacity-70 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white/10 backdrop-blur-md text-white rounded-2xl p-4 max-w-xs">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-300"></div>
                <span>Sócrates está pensando...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Questions */}
      {suggestedQuestions.length > 0 && (
        <div className="p-4 bg-purple-900/30 border-t border-purple-600/30">
          <p className="text-purple-200 text-sm mb-2">Perguntas sugeridas:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => sendMessage(question)}
                className="px-3 py-1 bg-purple-700/30 border border-purple-600/30 rounded-full text-purple-200 text-sm hover:bg-purple-600/30 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 bg-purple-900/50 backdrop-blur-md border-t border-purple-600/30">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Digite sua pergunta..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-purple-800/30 border border-purple-600/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeView, setActiveView] = useState('home');
  const [showAPIConfig, setShowAPIConfig] = useState(false);
  const [trails, setTrails] = useState([]);
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    fetchTrails();
    fetchClasses();
  }, []);

  const fetchTrails = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/trails`);
      setTrails(response.data);
    } catch (error) {
      console.error('Error fetching trails:', error);
    }
  };

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/classes`);
      setClasses(response.data);
    } catch (error) {
      console.error('Error fetching classes:', error);
    }
  };

  const handleLogout = () => {
    logout();
  };

  if (activeView === 'chat') {
    return <Chat onBack={() => setActiveView('home')} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-700">
      {/* Header */}
      <div className="bg-purple-900/50 backdrop-blur-md border-b border-purple-600/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-white">Socrates' Echo</h1>
            <span className="text-purple-200">
              {user?.role === 'teacher' ? 'Professor' : 'Estudante'}: {user?.name}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowAPIConfig(true)}
              className="px-4 py-2 bg-purple-700/30 border border-purple-600/30 rounded-lg text-purple-200 hover:bg-purple-600/30 transition-colors"
            >
              Configurar API
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600/30 border border-red-600/30 rounded-lg text-red-200 hover:bg-red-500/30 transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-purple-800/30 border-b border-purple-600/30 p-4">
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveView('home')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeView === 'home' 
                ? 'bg-purple-600 text-white' 
                : 'text-purple-200 hover:bg-purple-700/30'
            }`}
          >
            Início
          </button>
          <button
            onClick={() => setActiveView('chat')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeView === 'chat' 
                ? 'bg-purple-600 text-white' 
                : 'text-purple-200 hover:bg-purple-700/30'
            }`}
          >
            Chat com Sócrates
          </button>
          {user?.role === 'teacher' && (
            <button
              onClick={() => setActiveView('teacher')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeView === 'teacher' 
                  ? 'bg-purple-600 text-white' 
                  : 'text-purple-200 hover:bg-purple-700/30'
              }`}
            >
              Painel do Professor
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeView === 'home' && (
          <div className="space-y-8">
            {/* Welcome Section */}
            <div className="text-center">
              <h2 className="text-4xl font-bold text-white mb-4">
                Bem-vindo, {user?.name}!
              </h2>
              <p className="text-purple-200 text-lg max-w-2xl mx-auto">
                Explore o mundo da filosofia com a ajuda de Sócrates, seu tutor de IA personalizado.
                Descubra conceitos, participe de diálogos socráticos e desenvolva seu pensamento crítico.
              </p>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-purple-600/30">
                <h3 className="text-xl font-bold text-white mb-4">Conversar com Sócrates</h3>
                <p className="text-purple-200 mb-4">
                  Inicie uma conversa filosófica com nosso tutor de IA.
                </p>
                <button
                  onClick={() => setActiveView('chat')}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all"
                >
                  Iniciar Chat
                </button>
              </div>

              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-purple-600/30">
                <h3 className="text-xl font-bold text-white mb-4">Trilhas de Aprendizado</h3>
                <p className="text-purple-200 mb-4">
                  Explore trilhas estruturadas de filosofia.
                </p>
                <div className="text-purple-300 text-sm">
                  {trails.length} trilhas disponíveis
                </div>
              </div>

              {user?.role === 'teacher' && (
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-purple-600/30">
                  <h3 className="text-xl font-bold text-white mb-4">Minhas Turmas</h3>
                  <p className="text-purple-200 mb-4">
                    Gerencie suas turmas e acompanhe o progresso dos alunos.
                  </p>
                  <div className="text-purple-300 text-sm">
                    {classes.length} turmas criadas
                  </div>
                </div>
              )}
            </div>

            {/* Philosophy Quote */}
            <div className="bg-gradient-to-r from-purple-800/30 to-purple-700/30 rounded-2xl p-8 border border-purple-600/30 text-center">
              <blockquote className="text-2xl font-semibold text-white mb-4">
                "A vida não examinada não vale a pena ser vivida."
              </blockquote>
              <cite className="text-purple-200">— Sócrates</cite>
            </div>
          </div>
        )}

        {activeView === 'teacher' && user?.role === 'teacher' && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-3xl font-bold text-white">Painel do Professor</h2>
              <button className="px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all">
                Criar Nova Turma
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {classes.map((classItem) => (
                <div key={classItem.id} className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-purple-600/30">
                  <h3 className="text-xl font-bold text-white mb-2">{classItem.name}</h3>
                  <p className="text-purple-200 mb-4">{classItem.description}</p>
                  <div className="text-purple-300 text-sm mb-4">
                    Código: {classItem.join_code}
                  </div>
                  <div className="text-purple-300 text-sm">
                    {classItem.student_ids.length} estudantes
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* API Configuration Modal */}
      {showAPIConfig && (
        <APIConfig onClose={() => setShowAPIConfig(false)} />
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-purple-700 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-300 mx-auto mb-4"></div>
          <p className="text-purple-200">Carregando...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <AuthForm />;
};

export default App;