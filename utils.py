import os
import json
import google.generativeai as genai
import asyncio
import time
import re
import uuid # Importar para gerar IDs únicos

# --- Constantes ---
API_CALL_DELAY_SECONDS = 7
MAX_RETRIES = 3
RETRY_DELAY = 10

# --- Carregamento de Dados ---
# (load_json_data permanece igual)
def load_json_data(filepath):
    """Carrega dados de um arquivo JSON com tratamento de erro."""
    if not os.path.exists(filepath):
        print(f"AVISO (utils): Arquivo não encontrado: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERRO (utils): Erro ao decodificar JSON em {filepath}: {e}")
        return None
    except Exception as e:
        print(f"ERRO (utils): Erro inesperado ao ler {filepath}: {e}")
        return None

# --- Configuração da API Gemini (Retorna Modelo ou None) ---
# (configure_gemini permanece igual)
def configure_gemini(model_name="gemini-1.5-flash"):
    """Configura a API Gemini usando chave de ambiente e o nome do modelo especificado."""
    model = None
    print(f"INFO (utils): Tentando configurar Gemini com modelo '{model_name}'...")
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        print("INFO (utils): Chave API encontrada via variável de ambiente.")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            print(f"INFO (utils): Modelo Gemini '{model_name}' criado com SUCESSO.")
        except Exception as e:
            print(f"ERRO (utils): Falha ao configurar/criar modelo Gemini '{model_name}': {type(e).__name__} - {e}")
            model = None
    else:
        print("ERRO (utils): Variável de ambiente GEMINI_API_KEY não encontrada ou vazia.")
        print("ERRO (utils): A interpretação da IA será pulada.")
        model = None
    return model

# --- Chamada da API Gemini (com delay dinâmico, retries e IDs de log) ---
async def call_gemini_api(model, prompt):
    """Chama a API Gemini de forma assíncrona, tratando erros, com delay dinâmico, retries e IDs de log."""
    call_id = str(uuid.uuid4())[:8] # Gerar um ID curto para esta chamada específica
    log_prefix = f"INFO (utils) [Call {call_id}]:"
    error_prefix = f"ERRO (utils) [Call {call_id}]:"
    warn_prefix = f"AVISO (utils) [Call {call_id}]:"
    if not model:
        print(f"{warn_prefix} Chamada pulada porque o modelo não foi inicializado.")
        return "ERRO: Modelo Gemini não inicializado. Verifique a API Key."

    await asyncio.sleep(API_CALL_DELAY_SECONDS) # Atraso entre chamadas diferentes

    for attempt in range(MAX_RETRIES):
        print(f"{log_prefix} Chamando API Gemini... (Tentativa {attempt + 1}/{MAX_RETRIES})")
        try:
            response = await model.generate_content_async(prompt)
            print(f"{log_prefix} Chamada à API Gemini concluída (Tentativa {attempt + 1}).")
            # Processamento da resposta
            response_text = None
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
            elif response.parts:
                 response_text = "".join(part.text for part in response.parts).strip()
            elif hasattr(response, 'candidates') and response.candidates:
                 candidate = response.candidates[0]
                 if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                      response_text = "".join(part.text for part in candidate.content.parts).strip()

            # Verificar bloqueio APÓS tentar extrair texto
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_msg = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason
                print(f"{error_prefix} Chamada API bloqueada: {block_msg}")
                return f"ERRO API: Bloqueado - {block_msg}"

            # Verificar se o texto foi extraído com sucesso
            if response_text is not None and response_text != "": # Verifica se não é nulo ou vazio
                return response_text # Retorna o texto extraído
            else:
                 print(f"{warn_prefix} Resposta da API vazia ou estrutura inesperada após tentativa {attempt + 1}: {response}")
                 # Continuar para a próxima tentativa se houver, ou retornar erro no final
                 if attempt == MAX_RETRIES - 1:
                     return "ERRO API: Resposta vazia ou estrutura inesperada após todas as tentativas."


        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"{error_prefix} Tentativa {attempt + 1} falhou: {error_type} - {error_msg}")
            if "ResourceExhausted" in error_type or "DeadlineExceeded" in error_type or "ServiceUnavailable" in error_type or "InternalServerError" in error_type:
                if attempt < MAX_RETRIES - 1:
                    suggested_delay_seconds = RETRY_DELAY
                    try:
                        match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', error_msg, re.IGNORECASE)
                        if match:
                            suggested_delay_seconds = int(match.group(1)) + 1
                            print(f"{log_prefix} API sugeriu retry em {match.group(1)}s.")
                        else:
                             print(f"{log_prefix} Não foi possível extrair retry_delay da mensagem. Usando padrão de {RETRY_DELAY}s.")
                    except Exception as parse_error:
                         print(f"{warn_prefix} Erro ao parsear retry_delay: {parse_error}. Usando padrão de {RETRY_DELAY}s.")
                    wait_time = max(suggested_delay_seconds, RETRY_DELAY)
                    print(f"{log_prefix} Aguardando {wait_time}s antes de tentar novamente...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"{error_prefix} Máximo de {MAX_RETRIES} tentativas atingido.")
                    return f"ERRO API: Falha após {MAX_RETRIES} tentativas - {error_type}"
            else:
                 return f"ERRO API: Falha não recuperável na chamada - {error_type}"
    # Esta linha só deve ser alcançada se o loop terminar sem retornar explicitamente
    print(f"{error_prefix} Falha inesperada no processo de chamada após todas as tentativas.")
    return "ERRO API: Falha inesperada no processo de chamada."
