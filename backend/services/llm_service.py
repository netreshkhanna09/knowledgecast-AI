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

def generate_podcast_script(context: str, topic: str, duration: int) -> str:
    """
    Generate a two-host podcast script from retrieved context.

    Args:
        context: retrieved chunks relevant to the topic
        topic: podcast topic
        duration: podcast duration in minutes

    Returns:
        podcast script as string
    """

    # Approx word count for spoken podcast
    word_count_map = {
        2: 300,
        5: 750,
        10: 1500,
        15: 2200
    }

    target_words = word_count_map.get(duration, 750)

    system_prompt = """You are an expert educational podcast script writer.
Your job is to convert technical content into a clear, engaging two-host podcast script.
Use ONLY the provided context.
Do not add external knowledge.
Keep the tone conversational, simple, and useful for learners."""

    user_prompt = f"""Context:
{context}

Create a two-host podcast script on the topic: {topic}

Requirements:
- Duration: approximately {duration} minutes
- Target length: around {target_words} words
- Use two hosts: Host A and Host B
- Format every line like:
  Host A: ...
  Host B: ...
- Start with a short intro
- Explain the topic clearly
- Include examples or analogies only if they are supported by the context
- End with a short conclusion
- Do not mention that you are using retrieved chunks or context

Podcast Script:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2500
    )

    return response.choices[0].message.content