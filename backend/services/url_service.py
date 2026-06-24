# URL/article text extraction service
# Library: newspaper3k

from newspaper import Article

def extract_text_from_url(url: str) -> dict:
    """
    Extract title and text content from a webpage URL.
    
    Args:
        url: the webpage URL to extract content from
        
    Returns:
        dictionary with 'title' and 'text' keys
        
    Raises:
        ValueError: if URL is invalid or extraction fails
    """
    # basic URL validation
    if not url.startswith("http"):
        raise ValueError("Invalid URL. Must start with http:// or https://")

    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        raise ValueError(f"Could not extract content from URL: {url}")

    # clean the extracted text
    text = article.text.strip()
    text = " ".join(text.split())

    # check if extraction actually got meaningful content
    if len(text) < 100:
        raise ValueError(
            f"Extracted content too short. This page may not be a standard article: {url}"
        )

    return {
        "title": article.title,
        "text": text
    }