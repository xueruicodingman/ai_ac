const API_BASE_URL = 'http://localhost:8000';

export const setAuthToken = (token: string) => {
  sessionStorage.setItem('auth_token', token);
};

export const clearAuthToken = () => {
  sessionStorage.removeItem('auth_token');
};

export const getHeaders = () => {
  // 每次都从sessionStorage读取，确保获取最新token
  const token = sessionStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// 认证 API
export const register = async (email: string, password: string) => {
  console.log('API: register called with email:', email);
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    
    console.log('API: register response status:', response.status);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API: register failed with error:', errorData);
      throw new Error(errorData.detail || `注册失败 (${response.status})`);
    }
    
    const data = await response.json();
    console.log('API: register response data:', data);
    return data;
  } catch (err: any) {
    console.error('API: register error:', err);
    throw err;
  }
};

export const login = async (email: string, password: string) => {
  console.log('API: login called with email:', email);
  try {
    console.log('API: making fetch request to:', `${API_BASE_URL}/api/auth/login`);
    
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    
    console.log('API: login got response, status:', response.status);
    console.log('API: login response headers:', response.headers);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API: login failed with error:', errorData);
      throw new Error(errorData.detail || `登录失败 (${response.status})`);
    }
    
    const data = await response.json();
    console.log('API: login response data:', data);
    
    if (!data.access_token) {
      throw new Error('登录响应缺少access_token');
    }
    setAuthToken(data.access_token);
    console.log('API: login token set successfully');
    return data;
  } catch (err: any) {
    console.error('API: login error:', err);
    throw err;
  }
};

export const logout = () => {
  clearAuthToken();
};

// 用户设置 API
export const getUserSettings = async () => {
  const response = await fetch(`${API_BASE_URL}/api/user/settings`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('获取设置失败');
  }
  
  return response.json();
};

export const updateUserSettings = async (settings: {
  api_key?: string;
  api_url?: string;
  default_model?: string;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/user/settings`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(settings),
  });
  
  if (!response.ok) {
    throw new Error('更新设置失败');
  }
  
  return response.json();
};

// 胜任力模型 API
export const generateCompetencyModel = async (params: {
  background?: string;
  specified_abilities?: string[];
  num_competencies: number;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/competency-models/generate`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  
if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "结束会话失败");
  }

  return response.json();
};

export const submitVisionFollowupStream = async (
  sessionId: number,
  content: string,
  onChunk: (content: string, done: boolean) => void,
  signal?: AbortSignal
) => {
  const token = sessionStorage.getItem('auth_token');
  
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/followup/stream`,
    {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ content }),
      signal,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交追问回答失败");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("无法读取响应");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) {
              throw new Error(data.error);
            }
            onChunk(data.content || "", data.done || false);
            if (data.done) break;
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    }
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') {
      return;
    }
    throw e;
  }
};

export const getCompetencyModel = async () => {
  const response = await fetch(`${API_BASE_URL}/api/competency-models`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取模型失败');
  }
  
  return response.json();
};

export const saveCompetencyModel = async (model: {
  name: string;
  dimensions: Array<{
    id: string;
    name: string;
    meaning: string;
    behavior_criteria: Array<{ id: string; title: string; description: string }>;
  }>;
  source_files?: string[];
}) => {
  const response = await fetch(`${API_BASE_URL}/api/competency-models`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(model),
  });
  
  if (!response.ok) {
    throw new Error('保存模型失败');
  }
  
  return response.json();
};

// 评估矩阵 API
export const generateEvaluationMatrix = async (competencyModel: {
  dimensions: Array<{
    id: string;
    name: string;
    meaning: string;
    behavior_criteria: Array<{ id: string; title: string; description: string }>;
  }>;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation-matrices/generate`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ competency_model: competencyModel }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '生成矩阵失败');
  }
  
  return response.json();
};

export const getEvaluationMatrix = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/evaluation-matrices`, {
      headers: getHeaders()
    });
    
    if (response.status === 404) {
      console.log('Matrix not found (404), returning null');
      return null;
    }
    
    if (!response.ok) {
      const error = await response.json();
      console.error('Matrix API error:', error);
      throw new Error(error.detail || '获取矩阵失败');
    }
    
    return response.json();
  } catch (err) {
    console.error('getEvaluationMatrix exception:', err);
    throw err;
  }
};

export const saveEvaluationMatrix = async (data: {
  model_id: number;
  tools: Array<{ id: string; name: string; weight: number; enabled: boolean }>;
  matrix: Record<string, Record<string, boolean>>;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation-matrices`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('保存矩阵失败');
  }
  
  return response.json();
};

// 题本生成 API
export const generateQuestionnaire = async (
  toolId: string, 
  competencyModel: any, 
  evaluationMatrix: any,
  backgroundFileContent?: string,
  requirement?: string
) => {
  const requestBody = {
    competency_model: competencyModel,
    evaluation_matrix: evaluationMatrix,
    background_file_content: backgroundFileContent || null,
    requirement: requirement || ""
  };
  console.log('generateQuestionnaire 请求体:', requestBody);
  console.log('background_file_content 值:', backgroundFileContent);
  console.log('background_file_content 类型:', typeof backgroundFileContent);
  console.log('background_file_content 长度:', backgroundFileContent?.length);
  
  const response = await fetch(`${API_BASE_URL}/api/questionnaires/generate?tool_id=${toolId}`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(requestBody),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '生成题本失败');
  }
  
  return response.json();
};

export const getQuestionnaires = async () => {
  const response = await fetch(`${API_BASE_URL}/api/questionnaires`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('获取题本失败');
  }
  
  return response.json();
};

export const getQuestionnaire = async (toolId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/questionnaires/${toolId}`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('获取题本失败');
  }
  
  return response.json();
};

export const saveQuestionnaire = async (data: {
  tool_id: string;
  model_id: number;
  matrix_id: number;
  content: string;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/questionnaires`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('保存题本失败');
  }
  
  return response.json();
};

// 文件上传 API
export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const token = sessionStorage.getItem('auth_token');
  
  const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
    method: 'POST',
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error('文件上传失败');
  }
  
  return response.json();
};

// 评委手册 API
export const generateJudgeHandbook = async (params: {
  competency_model: any;
  evaluation_matrix: any;
  questionnaires: Array<{ tool_id: string; tool_name: string; content: string }>;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-handbooks/generate`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `生成评委手册失败 (${response.status})`);
  }
  
  return response.json();
};

export const getJudgeHandbook = async () => {
  const response = await fetch(`${API_BASE_URL}/api/judge-handbooks`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取评委手册失败');
  }
  
  return response.json();
};

export const generateJudgeHandbookByTool = async (
  tool: string,
  content: string,
  competencyModel: any,
  evaluationMatrix: any
) => {
  const requestBody = {
    competency_model: competencyModel,
    evaluation_matrix: evaluationMatrix,
    content: content
  };

  const response = await fetch(`${API_BASE_URL}/api/judge-handbooks/generate/${tool}`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(requestBody),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `生成评委手册失败 (${response.status})`);
  }
  
  return response.json();
};

export const saveJudgeHandbook = async (data: {
  model_id: number;
  matrix_id: number;
  questionnaire_ids: number[];
  content: string;
  word_url?: string;
  pdf_url?: string;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-handbooks`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || '保存评委手册失败');
  }
  
  return response.json();
};

// 报告生成 API
export const generateFullReport = async (params: {
  behavior_record: string;
  ability_standards: Array<{ id: string; name: string; meaning: string; behavior_criteria: Array<{ id: string; title: string; description: string }> }>;
  report_type: '反馈版' | '组织版' | '个人版';
}) => {
  const response = await fetch(`${API_BASE_URL}/api/reports/generate/full`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  
if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let errorMessage = errorData.detail || `生成评委手册失败 (${response.status})`;
    if (Array.isArray(errorMessage)) {
      errorMessage = errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
    }
    throw new Error(errorMessage);
  }
  
  return response.json();
};

export const saveReport = async (data: {
  record_id: number;
  report_type: string;
  candidate_id: string;
  candidate_name?: string;
  scores_data?: Record<string, number>;
  radar_chart_url?: string;
  total_score?: number;
  content: Record<string, any>;
  language?: string;
  word_url?: string;
  pdf_url?: string;
  status: string;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `保存报告失败 (${response.status})`);
  }
  
  return response.json();
};

export const getReports = async () => {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `获取报告失败 (${response.status})`);
  }
  
  return response.json();
};

// 获取文件内容
export const getFileContent = async (fileId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/files/${fileId}/content`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('获取文件内容失败');
  }
  
  return response.json();
};

// 练习相关 API
export const startPractice = async (toolId: string = "beh") => {
  const response = await fetch(`${API_BASE_URL}/api/practice/start`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ tool_id: toolId }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "开始练习失败");
  }
  
  return response.json();
};

export const submitAnswer = async (
  sessionId: number,
  content: string,
  inputType: string = "text"
) => {
  const response = await fetch(
    `${API_BASE_URL}/api/practice/${sessionId}/answer`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content, input_type: inputType }),
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交回答失败");
  }
  
  return response.json();
};

export const getSessionStatus = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/practice/${sessionId}/status`,
    {
      headers: getHeaders(),
    }
  );
  
  if (!response.ok) {
    throw new Error("获取状态失败");
  }
  
  return response.json();
};

export const getSessionHistory = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/practice/${sessionId}/history`,
    {
      headers: getHeaders(),
    }
  );
  
  if (!response.ok) {
    throw new Error("获取历史失败");
  }
  
  return response.json();
};

// 角色扮演练习 API
export const startRolePlayPractice = async () => {
  const response = await fetch(`${API_BASE_URL}/api/roleplay/start`, {
    method: "POST",
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "开始角色扮演练习失败");
  }
  
  return response.json();
};

export const submitRolePlayAnswer = async (
  sessionId: number,
  content: string
) => {
  const response = await fetch(
    `${API_BASE_URL}/api/roleplay/${sessionId}/answer`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content }),
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交回答失败");
  }
  
  return response.json();
};

export const getRolePlaySessionStatus = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/roleplay/${sessionId}/status`,
    {
      headers: getHeaders(),
    }
  );
  
  if (!response.ok) {
    throw new Error("获取状态失败");
  }
  
  return response.json();
};

export const submitRolePlayAnswerStream = async (
  sessionId: number,
  content: string,
  onChunk: (content: string, done: boolean) => void,
  signal?: AbortSignal
) => {
  const token = sessionStorage.getItem('auth_token');
  
  const response = await fetch(
    `${API_BASE_URL}/api/roleplay/${sessionId}/answer/stream`,
    {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ content }),
      signal,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交回答失败");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("无法读取响应");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) {
              throw new Error(data.error);
            }
            onChunk(data.content || "", data.done || false);
            if (data.done) break;
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    }
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') {
      return;
    }
    throw e;
  }
};

export const endRolePlaySession = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/roleplay/${sessionId}/end`,
    {
      method: "POST",
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "结束会话失败");
  }

  return response.json();
};

// 个人愿景练习 API
export const startVisionPractice = async (data: {
  questionnaire_content: string;
  duration?: number;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/vision/start`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "开始愿景练习失败");
  }

  return response.json();
};

export const submitVisionAnswer = async (
  sessionId: number,
  content: string
) => {
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/answer`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交回答失败");
  }

  return response.json();
};

export const submitVisionFollowup = async (
  sessionId: number,
  content: string
) => {
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/followup`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交追问回答失败");
  }

  return response.json();
};

export const getVisionSessionStatus = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/status`,
    {
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error("获取状态失败");
  }

  return response.json();
};

export const submitVisionAnswerStream = async (
  sessionId: number,
  content: string,
  onChunk: (content: string, done: boolean) => void,
  signal?: AbortSignal
) => {
  const token = sessionStorage.getItem('auth_token');
  
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/answer/stream`,
    {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ content }),
      signal,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "提交回答失败");
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("无法读取响应");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) {
              throw new Error(data.error);
            }
            onChunk(data.content || "", data.done || false);
            if (data.done) break;
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    }
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') {
      return;
    }
    throw e;
  }
};

export const endVisionPracticeSession = async (sessionId: number) => {
  const response = await fetch(
    `${API_BASE_URL}/api/vision/${sessionId}/end`,
    {
      method: "POST",
      headers: getHeaders(),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "结束会话失败");
  }

  return response.json();
};

// 评价标准 API
export const getEvaluationCriteria = async () => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation-criteria`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取评价标准失败');
  }
  
  return response.json();
};

export const saveEvaluationCriteria = async (data: any) => {
  const response = await fetch(`${API_BASE_URL}/api/evaluation-criteria`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '保存评价标准失败');
  }
  
  return response.json();
};

// 评委组 API
export const getJudges = async () => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取评委失败');
  }
  
  return response.json();
};

export const saveJudges = async (judges: any[]) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(judges),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '保存评委失败');
  }
  
  return response.json();
};

export const generateJudges = async (count: number) => {
  const response = await fetch(`${API_BASE_URL}/api/judge-teams/generate?count=${count}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '生成评委失败');
  }
  
  return response.json();
};

// 知识库 API
export const getKnowledgeBase = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取知识库失败');
  }
  
  return response.json();
};

export const uploadDocument = async (tool: string, file: File, chunkConfig: { strategy?: string; separator?: string; max_length?: number }) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('chunk_config', JSON.stringify(chunkConfig));
  
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    method: 'POST',
    headers: {
      'Authorization': sessionStorage.getItem('auth_token') ? `Bearer ${sessionStorage.getItem('auth_token')}` : '',
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '上传文档失败');
  }
  
  return response.json();
};

export const updateChunks = async (tool: string, chunkConfig: { strategy?: string; separator?: string; max_length?: number }) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/chunks`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(chunkConfig),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '更新切片失败');
  }
  
  return response.json();
};

export const updateChunkContent = async (tool: string, chunkId: string, chunkData: { title?: string; content?: string; keywords?: string[] }) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/chunks/${chunkId}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(chunkData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '更新切片失败');
  }
  
  return response.json();
};

export const deleteChunk = async (tool: string, chunkId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/chunks/${chunkId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '删除切片失败');
  }
  
  return response.json();
};

export const addChunk = async (tool: string, chunkData: { title?: string; content?: string; keywords?: string[] }) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/chunks`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(chunkData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '添加切片失败');
  }
  
  return response.json();
};

export const deleteKnowledgeBase = async (tool: string) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '删除知识库失败');
  }
  
  return response.json();
};

export const useHandbookAsSource = async (tool: string, chunkConfig: { strategy?: string; separator?: string; max_length?: number }) => {
  const response = await fetch(`${API_BASE_URL}/api/knowledge-base/${tool}/use-handbook`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(chunkConfig),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '使用手册失败');
  }
  
  return response.json();
};

// 行为评价 API
export const getToolsWithCompetencies = async () => {
  const response = await fetch(`${API_BASE_URL}/api/behavior-evaluation/tools`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取工具失败');
  }
  
  return response.json();
};

export const getPracticeSessionsByTool = async (toolId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/behavior-evaluation/sessions/${toolId}`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取练习记录失败');
  }
  
  return response.json();
};

export const getSessionEvaluationData = async (sessionId: number) => {
  const response = await fetch(`${API_BASE_URL}/api/behavior-evaluation/session/${sessionId}`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取评价数据失败');
  }
  
  return response.json();
};

export const getCurrentUser = async () => {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('获取用户信息失败');
  }
  
  return response.json();
};