import os
import sys
import re
import json
import time
import string
import google.generativeai as genai

# Read API Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
    print("Please set it in your environment. Example (PowerShell):")
    print('  $env:GEMINI_API_KEY="your-api-key-here"')
    print("Then run this script again.\n")
    sys.exit(1)

# Configure Gemini (use REST transport to prevent gRPC hangs on Windows)
genai.configure(api_key=api_key, transport="rest")

# Files
HTML_FILE = "uhv_quiz.html"
NOTES_FILE = "extracted_notes.txt"
CACHE_FILE = "explanations_cache.json"

# Simple list of English stopwords to filter out common words
STOPWORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "can't", "cannot", 
    "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", 
    "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", 
    "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", 
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", 
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", 
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", 
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", 
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", 
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
])

def tokenize(text):
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 2]

def chunk_notes():
    if not os.path.exists(NOTES_FILE):
        print(f"[ERROR] Notes file '{NOTES_FILE}' not found. Please run 'python extract_text.py' first.")
        sys.exit(1)
        
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        notes_text = f.read()
        
    chunks = []
    current_source = "Unknown"
    
    lines = notes_text.split('\n')
    current_chunk = []
    
    for line in lines:
        if line.startswith("SOURCE FILE:"):
            if current_chunk:
                chunks.append({
                    "source": current_source,
                    "text": "\n".join(current_chunk).strip()
                })
                current_chunk = []
            current_source = line.replace("SOURCE FILE:", "").strip()
        elif line.startswith("--- Page") or line.startswith("--- Slide"):
            if current_chunk:
                chunks.append({
                    "source": current_source,
                    "text": "\n".join(current_chunk).strip()
                })
                current_chunk = []
            current_chunk.append(line)
        else:
            current_chunk.append(line)
            
    if current_chunk:
        chunks.append({
            "source": current_source,
            "text": "\n".join(current_chunk).strip()
        })
        
    # Pre-tokenize chunks for 100x faster retrieval queries
    for chunk in chunks:
        chunk["tokens"] = tokenize(chunk["text"])
        
    return chunks

def retrieve_context(question_dict, chunks, k=6):
    # Combine question and options for query
    query_str = question_dict["q"] + " " + " ".join(question_dict["opts"])
    query_tokens = set(tokenize(query_str))
    
    scored_chunks = []
    for chunk in chunks:
        chunk_tokens = chunk.get("tokens", [])
        # Score: overlap of unique query words
        score = sum(1 for w in query_tokens if w in chunk_tokens)
        scored_chunks.append((score, chunk))
        
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Take top k
    top_chunks = [item[1] for item in scored_chunks[:k]]
    
    # Format context
    context_parts = []
    for idx, c in enumerate(top_chunks):
        context_parts.append(f"--- Reference {idx+1} (Source: {c['source']}) ---\n{c['text']}")
        
    return "\n\n".join(context_parts)

def parse_html_questions():
    if not os.path.exists(HTML_FILE):
        print(f"[ERROR] Quiz file '{HTML_FILE}' not found.")
        sys.exit(1)
        
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Find QUESTIONS array
    match = re.search(r'const QUESTIONS = \[(.*?)\];\s*\n\s*const FREQ_LABEL', html_content, re.DOTALL)
    if not match:
        print("[ERROR] Could not find QUESTIONS array in HTML file.")
        sys.exit(1)
        
    array_text = match.group(1)
    
    # Parse individual objects
    lines = array_text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('//') or not stripped:
            continue
        cleaned_lines.append(line)
    cleaned_text = '\n'.join(cleaned_lines)
    
    questions = []
    depth = 0
    start = -1
    for i, c in enumerate(cleaned_text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start != -1:
                obj_str = cleaned_text[start:i+1]
                py_str = obj_str
                py_str = re.sub(r'(\b(freq|q|opts|a|explanations))\s*:', r'"\1":', py_str)
                py_str = re.sub(r',\s*\]', ']', py_str)
                py_str = re.sub(r',\s*\}', '}', py_str)
                try:
                    parsed = json.loads(py_str)
                    questions.append(parsed)
                except Exception as e:
                    try:
                        parsed = eval(py_str, {"__builtins__": None}, {})
                        questions.append(parsed)
                    except Exception as ex:
                        print(f"[WARNING] Skipping question due to parsing error: {obj_str[:100]}... Error: {ex}")
                start = -1
                
    print(f"Successfully parsed {len(questions)} questions from HTML.")
    return html_content, questions

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Cache file was corrupted: {e}. Starting fresh.")
    return {}

def generate_batch_explanations(batch_qs, model):
    prompt = f"""
You are an expert tutor for the course 'Universal Human Values' (UHV).
Below are multiple-choice questions (MCQs), each paired with the most relevant passages retrieved from the course lecture slides and modules (under "relevant_context").

Use this context as your source of truth to write detailed explanations for each option.
For each question, you MUST provide an explanation for each of its 4 options:
- For the CORRECT option, explain why it is correct based on UHV concepts in the retrieved notes.
- For each INCORRECT option, explain why it is incorrect or how it differs from the correct concept/state.

Format the output strictly as a JSON list of objects. Each object must have:
1. "q": The exact text of the question (to map it back).
2. "explanations": A list of 4 strings (explanations for option 0, 1, 2, and 3 in that exact order).

Keep explanations concise but highly educational (2-3 sentences each). Do not include any markdown formatting outside the JSON code block.

=== QUESTIONS & CONTEXTS TO PROCESS ===
{json.dumps(batch_qs, indent=2)}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
            request_options={"timeout": 120}
        )
        data = json.loads(response.text)
        return data, False
    except Exception as e:
        err_msg = str(e)
        is_quota = "quota" in err_msg.lower() or "429" in err_msg or "resourceexhausted" in err_msg.lower()
        print(f"[ERROR] Gemini API call failed: {e}")
        return None, is_quota

def inject_explanations_to_html(original_html, questions, cache):
    for q in questions:
        q_text = q['q']
        if q_text in cache:
            q['explanations'] = cache[q_text]
            
    js_lines = ["const QUESTIONS = ["]
    for q in questions:
        freq = q.get('freq', 1)
        q_text = json.dumps(q['q'], ensure_ascii=False)
        opts = json.dumps(q['opts'], ensure_ascii=False)
        a = q['a']
        if 'explanations' in q:
            exps = json.dumps(q['explanations'], ensure_ascii=False)
            js_lines.append(f"  {{freq:{freq}, q:{q_text}, opts:{opts}, a:{a}, explanations:{exps}}},")
        else:
            js_lines.append(f"  {{freq:{freq}, q:{q_text}, opts:{opts}, a:{a}}},")
    js_lines.append("];")
    js_block = "\n".join(js_lines)
    
    pattern = r'const QUESTIONS = \[(.*?)\];\s*\n\s*const FREQ_LABEL'
    replacement = js_block + "\n\nconst FREQ_LABEL"
    updated_html = re.sub(pattern, replacement, original_html, flags=re.DOTALL)
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(updated_html)
    print(f"[SUCCESS] Updated '{HTML_FILE}' with generated explanations!")

def main():
    print("Starting UHV Quiz Explanation Generation using RAG...")
    chunks = chunk_notes()
    print(f"Loaded notes and split into {len(chunks)} slide/page chunks.")
    
    html_content, questions = parse_html_questions()
    cache = load_cache()
    
    # Identify questions that need explanations
    pending_qs = []
    for q in questions:
        q_text = q['q']
        if q_text not in cache or len(cache[q_text]) != len(q['opts']):
            # Retrieve relevant notes for this specific question
            context = retrieve_context(q, chunks, k=5)
            pending_qs.append({
                "q": q['q'],
                "opts": q['opts'],
                "correct_option_index": q['a'],
                "correct_option_text": q['opts'][q['a']],
                "relevant_context": context
            })
            
    total_total = len(questions)
    total_pending = len(pending_qs)
    print(f"Total Questions: {total_total} | Already explained: {total_total - total_pending} | Pending: {total_pending}")
    
    if total_pending == 0:
        print("All questions already have explanations in cache. Injecting into HTML...")
        inject_explanations_to_html(html_content, questions, cache)
        return

    # List of models to rotate through to bypass per-model free-tier daily quotas
    models_to_try = [
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]
    model_idx = 0
    model = genai.GenerativeModel(models_to_try[model_idx])
    
    batch_size = 4  # Reduced from 10 to prevent large prompt timeouts

    i = 0
    while i < total_pending:
        batch = pending_qs[i:i+batch_size]
        print(f"\nProcessing batch {i // batch_size + 1} of {(total_pending - 1) // batch_size + 1} (questions {i+1} to {min(i+batch_size, total_pending)})...")
        print(f"Using model: {models_to_try[model_idx]}")
        
        success = False
        quota_hit = False
        for attempt in range(3):
            result, is_quota = generate_batch_explanations(batch, model)
            if result:
                added_count = 0
                for item in result:
                    if 'q' in item and 'explanations' in item:
                        cache[item['q']] = item['explanations']
                        added_count += 1
                save_cache(cache)
                print(f"Success! Generated explanations for {added_count} questions. Saved to cache.")
                success = True
                break
            elif is_quota:
                print(f"[QUOTA EXCEEDED] Model '{models_to_try[model_idx]}' hit quota limits.")
                if model_idx + 1 < len(models_to_try):
                    model_idx += 1
                    print(f"Switching to next model: '{models_to_try[model_idx]}'...")
                    model = genai.GenerativeModel(models_to_try[model_idx])
                    quota_hit = True
                    break  # Break attempt loop to retry batch with new model
                else:
                    print("[ERROR] All models in the list have exhausted their quotas.")
                    break
            else:
                print(f"Attempt {attempt + 1} failed. Retrying in 25 seconds...")
                time.sleep(25)
                
        if success:
            i += batch_size
            if i < total_pending:
                print("Waiting 10 seconds to comply with rate limits...")
                time.sleep(10)
        elif quota_hit:
            # Retry the exact same batch using the next model
            continue
        else:
            print("[ERROR] Batch failed repeatedly without quota recovery. Stopping script.")
            break
            
    # Inject completed explanations
    print("\nInjecting completed explanations into the HTML quiz...")
    inject_explanations_to_html(html_content, questions, cache)
    print("Done!")

if __name__ == "__main__":
    main()
