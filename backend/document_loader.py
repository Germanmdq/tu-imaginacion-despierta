import os
import re
import warnings
from pypdf import PdfReader
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

def clean_page_text(text):
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        # Skip headers
        if re.search(r'Biblioteca\s+Neville\s+Goddard', l, re.IGNORECASE):
            continue
        # Skip page number lines
        if re.search(r'^P\u00e1gina\s+\d+\s*$', l, re.IGNORECASE) or re.search(r'^P\u00e1gina\s+\d+\s*\|\s*', l, re.IGNORECASE):
            continue
        if "Página" in l and ("Tomo" in l or "|" in l):
            continue
        # Skip copyright footer
        if "elclubdelaimaginacion.com" in l or "el club de la imaginacion" in l.lower():
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

def extract_text_from_pdf(file_path):
    """
    Extracts text page by page from a PDF file, cleaning headers and footers.
    """
    docs = []
    try:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text = clean_page_text(text)
            if text and text.strip():
                docs.append({
                    "text": text,
                    "page": i + 1,
                    "chapter": ""
                })
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
    return docs

def extract_text_from_epub(file_path):
    """
    Extracts text from an EPUB file, parsing HTML items chapter by chapter.
    """
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    docs = []
    try:
        book = epub.read_epub(file_path)
        chapter_index = 1
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = item.get_content()
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n')
                
                # Basic cleanup
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text_content = '\n'.join(lines)
                
                if len(text_content.strip()) > 50:
                    # Try to extract a chapter title if possible
                    title = f"Capítulo {chapter_index}"
                    h1 = soup.find('h1')
                    h2 = soup.find('h2')
                    if h1 and h1.text.strip():
                        title = h1.text.strip()[:60]
                    elif h2 and h2.text.strip():
                        title = h2.text.strip()[:60]
                        
                    docs.append({
                        "text": text_content,
                        "page": chapter_index,
                        "chapter": title
                    })
                    chapter_index += 1
    except Exception as e:
        print(f"Error parsing EPUB {file_path}: {e}")
    return docs

def extract_text_from_txt(file_path):
    """
    Extracts text from a plain text or Markdown file.
    """
    docs = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            if text.strip():
                docs.append({
                    "text": text,
                    "page": 1,
                    "chapter": "Documento de texto"
                })
    except Exception as e:
        print(f"Error parsing text file {file_path}: {e}")
    return docs

def load_document(file_path):
    """
    Determines file type and loads text content.
    """
    _, ext = os.path.splitext(file_path.lower())
    source_name = os.path.basename(file_path)
    
    if ext == '.pdf':
        docs = extract_text_from_pdf(file_path)
    elif ext == '.epub':
        docs = extract_text_from_epub(file_path)
    elif ext in ['.txt', '.md', '.markdown']:
        docs = extract_text_from_txt(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return []
        
    for doc in docs:
        doc["source"] = source_name
        
    return docs

def chunk_text(documents, chunk_size=1000, chunk_overlap=200):
    """
    Splits document sections into overlapping chunks using a sliding window.
    Appends metadata describing the source, page, and chunk index.
    """
    chunks = []
    for doc in documents:
        text = doc.get("text", "")
        if not text.strip():
            continue
        
        doc_length = len(text)
        if doc_length <= chunk_size:
            chunks.append({
                "text": text,
                "metadata": {
                    "source": doc.get("source", ""),
                    "page": doc.get("page", 1),
                    "chapter": doc.get("chapter", ""),
                    "chunk_index": 0
                }
            })
            continue
            
        chunk_idx = 0
        start = 0
        while start < doc_length:
            end = start + chunk_size
            
            # Avoid cutting words by adjusting the endpoint backward if there's whitespace
            if end < doc_length:
                search_limit = max(start, end - chunk_overlap)
                space_pos = text.rfind(" ", search_limit, end)
                newline_pos = text.rfind("\n", search_limit, end)
                
                pos = max(space_pos, newline_pos)
                if pos > start:
                    end = pos + 1
                    
            chunk_slice = text[start:end].strip()
            if chunk_slice:
                chunks.append({
                    "text": chunk_slice,
                    "metadata": {
                        "source": doc.get("source", ""),
                        "page": doc.get("page", 1),
                        "chapter": doc.get("chapter", ""),
                        "chunk_index": chunk_idx
                    }
                })
                chunk_idx += 1
                
            start = end - chunk_overlap
            if start >= doc_length or end >= doc_length:
                break
    return chunks
