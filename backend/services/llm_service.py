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

def generate_topic_summary(context: str, topic: str) -> str:
    """
    Generate a focused summary specifically about a given topic.
    
    Args:
        context: retrieved chunks relevant to the topic
        topic: the specific topic to summarize
        
    Returns:
        focused summary as string
    """
    system_prompt = """You are a precise knowledge assistant.
Your job is to generate focused summaries about specific topics.
Only include information directly related to the requested topic.
Do not add external knowledge. Base your answer only on the provided context."""

    user_prompt = f"""Context:
{context}

Generate a focused summary specifically about: {topic}

If the context contains limited information about this topic, clearly state that.
Structure your summary as:
1. Overview (2-3 sentences about {topic})
2. Key Details (bullet points of specific facts)
3. Source Coverage (how well the sources cover this topic)"""

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

def generate_podcast_script(context: str, topic: str, duration: int = 5) -> str:
    word_count = duration * 130

    system_prompt = """You are a professional podcast script writer.
STRICT RULES — follow exactly:
1. Only Alex and Sam speak. No guests ever.
2. Every line starts with EITHER "Alex:" OR "Sam:" — never "Sam: Alex:" or any other format
3. Only use information from the provided context. Zero external knowledge.
4. If topic is not in context, Alex says the topic isn't covered and both wrap up in 3 lines maximum.
5. Never repeat the other host's name at the start of your line."""
    user_prompt = f"""Write a podcast script for "KnowledgeCast".

Host 1: ALEX — asks sharp questions, challenges ideas, keeps conversation moving.
Host 2: SAM — explains clearly, uses examples from the context, gives depth.

CRITICAL RULES:
- There are NO guests. ONLY Alex and Sam speak. Never introduce a third person.
- Every single line MUST start with exactly "Alex:" or "Sam:" — no exceptions, no bold, no asterisks
- Only discuss information found in the provided context
- If context is not relevant to the topic, hosts should say so honestly
- Natural conversation — reactions, follow-ups, moments of clarity
- Target length: {word_count} words ({duration} minutes)
- Match tone to content type — not always educational
- Start with hosts introducing the topic
- End with key takeaways between Alex and Sam only

Context:
{context}

Topic to discuss: {topic}

Script:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )

    return response.choices[0].message.content