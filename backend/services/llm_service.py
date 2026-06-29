# LLM service
# Using Groq API with Llama 3

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# initialize Groq client once at module level
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(query: str, context: str) -> str:
    """
    Send query + retrieved context to Groq LLM and get answer.
    
    Args:
        query: the user's question
        context: retrieved chunks joined as one string
        
    Returns:
        LLM generated answer as string
    """
    system_prompt = """You are a precise knowledge assistant. 
Your job is to answer questions based ONLY on the provided context.
Do not use any external knowledge or make assumptions.
If the answer is not found in the context, clearly say 'I could not find this information in the provided sources.'
Keep answers concise, accurate, and well-structured."""

    user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content


def generate_summary(context: str) -> str:
    """
    Generate executive summary from retrieved context.
    
    Args:
        context: full text from all sources
        
    Returns:
        structured summary as string
    """
    system_prompt = """You are a knowledge synthesizer.
Generate a structured summary based ONLY on the provided content.
Do not add external knowledge."""

    user_prompt = f"""Content:
{context}

Generate a structured summary with these sections:
1. Executive Summary (2-3 sentences)
2. Key Insights (3-5 bullet points)
3. Main Takeaways (2-3 bullet points)"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content