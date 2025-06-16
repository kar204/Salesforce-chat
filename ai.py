import json
import logging
from config import logger
from watsonx_utils import get_watsonx_token, watsonx_url, watsonx_project_id, watsonx_model_id
import requests
import pandas as pd

MAX_TOKENS_PER_CHUNK = 1000  # Adjust based on WatsonX limits and prompt size

def convert_dataframes_to_dict(obj):
    """
    Recursively traverse obj and convert any pandas DataFrame or Series to dict.
    """
    if isinstance(obj, dict):
        return {k: convert_dataframes_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dataframes_to_dict(i) for i in obj]
    elif isinstance(obj, pd.DataFrame):
        # Convert DataFrame to list of dicts (records)
        return obj.to_dict(orient='records')
    elif isinstance(obj, pd.Series):
        # Convert Series to list
        return obj.tolist()
    else:
        return obj

def call_watsonx_summarizer(prompt: str) -> str:
    """
    Call WatsonX LLM with prompt for summarization.
    """
    try:
        token = get_watsonx_token()
        url = f"{watsonx_url}/ml/v1/projects/{watsonx_project_id}/deployments/{watsonx_model_id}/predictions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "text": prompt
            }
        }
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            result_json = response.json()
            text = result_json.get("predictions", [{}])[0].get("text", "")
            return text.strip()
        else:
            logger.error(f"WatsonX summarizer error: {response.status_code} {response.text}")
            return "Sorry, I couldn't generate a summary due to an error."
    except Exception as e:
        logger.error(f"Exception in WatsonX summarizer: {str(e)}")
        return "Sorry, I encountered an error while summarizing."

def summarize_analysis_result_with_ai(backend_result: dict, user_query: str) -> str:
    """
    Summarize backend analysis result into conversational text.
    """

    # Convert DataFrames inside backend_result to dict
    serializable_result = convert_dataframes_to_dict(backend_result)

    backend_json_str = json.dumps(serializable_result, indent=2)

    # Chunking if large data
    if len(backend_json_str) > MAX_TOKENS_PER_CHUNK:
        chunks = [backend_json_str[i:i+MAX_TOKENS_PER_CHUNK] for i in range(0, len(backend_json_str), MAX_TOKENS_PER_CHUNK)]
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            prompt = (
                f"Summarize the following data chunk {i+1} of {len(chunks)} "
                "in a clear and concise way for a business user:\n\n"
                f"{chunk}\n\nSummary:"
            )
            chunk_summary = call_watsonx_summarizer(prompt)
            chunk_summaries.append(chunk_summary)
        combined_summary_text = "\n\n".join(chunk_summaries)
        final_prompt = (
            f"Combine the following summaries into a single concise summary for a business user "
            f"based on their question: {user_query}\n\n{combined_summary_text}\n\nFinal Summary:"
        )
        final_summary = call_watsonx_summarizer(final_prompt)
        return final_summary

    else:
        prompt = (
            f"Given the following backend analysis result, please provide a concise, user-friendly summary "
            f"to answer the user query: {user_query}\n\nResult Data:\n{backend_json_str}\n\nSummary:"
        )
        return call_watsonx_summarizer(prompt)
import json
import requests
import numpy as np
import pandas as pd
from config import logger

def serialize_data(data):
    """
    Serialize data into JSON string safely.
    Handles pandas DataFrame, numpy arrays, dicts, lists, strings, and pandas Index.
    """
    try:
        if isinstance(data, pd.DataFrame):
            return data.to_json(orient="records")
        elif isinstance(data, (pd.Index, pd.RangeIndex)):
            return json.dumps(data.tolist())
        elif isinstance(data, np.ndarray):
            return json.dumps(data.tolist())
        elif isinstance(data, (dict, list)):
            return json.dumps(data)
        elif isinstance(data, str):
            return data
        else:
            return str(data)
    except Exception as e:
        logger.error(f"Serialization error: {e}")
        return str(data)

def call_watsonx_api(prompt, watsonx_url, watsonx_project_id, watsonx_model_id, get_watsonx_token):
    """
    Calls the WatsonX API with the given prompt and returns the AI-generated summary.
    """
    access_token = get_watsonx_token()
    url = f"{watsonx_url}/ml/v1/text/chat?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "project_id": watsonx_project_id,
        "model_id": watsonx_model_id,
        "messages": [
            {"role": "system", "content": "You are a helpful, concise, conversational analytics assistant."},
            {"role": "user", "content": prompt}
        ],
        "parameters": {"decoding_method": "greedy"}
    }
    response = requests.post(url, headers=headers, json=data, timeout=120)
    response.raise_for_status()
    resp_json = response.json()

    if isinstance(resp_json, dict) and 'results' in resp_json and resp_json['results']:
        return resp_json['results'][0].get('generated_text', str(resp_json['results'][0]))
    elif isinstance(resp_json, dict) and 'choices' in resp_json and resp_json['choices']:
        return resp_json['choices'][0]['message'].get('content', str(resp_json['choices'][0]['message']))
    elif isinstance(resp_json, dict) and 'error' in resp_json:
        logger.error(f"WatsonX API Error: {resp_json}")
        return f"Sorry, there was an AI error: {resp_json['error']}"
    else:
        logger.error(f"WatsonX API unexpected response: {resp_json}")
        return "Sorry, I couldn't generate a summary for this result."

def summarize_analysis_result_with_ai(
    analysis_result,
    user_question,
    watsonx_url,
    watsonx_project_id,
    watsonx_model_id,
    get_watsonx_token,
    max_chunk_size=3000
):
    """
    Summarize large backend analysis results using chunking and WatsonX API.
    Returns a concise conversational summary with optional follow-up.
    """
    # Serialize data safely
    summary_data = ""
    try:
        if isinstance(analysis_result, dict) and "data" in analysis_result:
            summary_data = serialize_data(analysis_result["data"])
        else:
            summary_data = serialize_data(analysis_result)
    except Exception as e:
        logger.error(f"Failed to serialize analysis result: {e}")
        summary_data = str(analysis_result)

    # Chunk the JSON string into manageable pieces
    chunks = [summary_data[i:i+max_chunk_size] for i in range(0, len(summary_data), max_chunk_size)]

    summaries = []
    for idx, chunk in enumerate(chunks):
        prompt = f"""
You are an AI assistant that summarizes technical analytics results in friendly, concise, and conversational English.
Below is a user's question and a chunk of the corresponding data result (in JSON or table format).

User question:
{user_question}

Data chunk {idx+1} of {len(chunks)}:
{chunk}

Provide a clear, short summary focused on business insights. Add a relevant follow-up question such as "Would you like to see this by location or over time?" or "Would you like more details?" if appropriate.
"""
        try:
            summary = call_watsonx_api(
                prompt,
                watsonx_url,
                watsonx_project_id,
                watsonx_model_id,
                get_watsonx_token
            )
        except Exception as e:
            logger.error(f"Error calling WatsonX API for chunk {idx+1}: {e}")
            summary = f"(Summary unavailable for chunk {idx+1} due to an error.)"
        summaries.append(summary.strip())

    # Aggregate summaries if multiple chunks exist
    if len(summaries) > 1:
        agg_prompt = f"""
You are an AI assistant. Several summaries of data chunks are provided below.
Aggregate them into a single, clear, high-level summary for the user.

Summaries:
{chr(10).join(summaries)}

Final concise summary:
"""
        try:
            final_summary = call_watsonx_api(
                agg_prompt,
                watsonx_url,
                watsonx_project_id,
                watsonx_model_id,
                get_watsonx_token
            )
        except Exception as e:
            logger.error(f"Error calling WatsonX API for aggregated summary: {e}")
            final_summary = "\n".join(summaries)

        return final_summary.strip()
    else:
        return summaries[0]
