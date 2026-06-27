# Text chunking service
# Library: LangChain RecursiveCharacterTextSplitter

from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_sources(sources: list) -> list:
    """
    Split text from multiple sources into overlapping chunks.
    
    Args:
        sources: list of source dictionaries with source_name, source_type, text
        
    Returns:
        flat list of chunk dictionaries with text and metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    all_chunks = []

    for source in sources:
        source_name = source["source_name"]
        source_type = source["source_type"]
        text = source["text"]

        # split this source's text into chunks
        chunks = splitter.split_text(text)

        # add metadata to each chunk
        for index, chunk_text in enumerate(chunks):
            all_chunks.append({
                "text": chunk_text,
                "source_name": source_name,
                "source_type": source_type,
                "chunk_index": index
            })

    return all_chunks