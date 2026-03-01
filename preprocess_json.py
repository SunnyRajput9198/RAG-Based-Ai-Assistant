import os
import json
import pandas as pd
import joblib
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text_list):
    return model.encode(text_list).tolist()

# ════════════════════════════════════════════════════════════════
# LOAD EXISTING DATA
# ════════════════════════════════════════════════════════════════
if os.path.exists("data.embeddings.joblib"):
    existing_df = joblib.load("data.embeddings.joblib")
    my_dicts = existing_df.to_dict('records')
    chunk_id = len(my_dicts)
    existing_titles = existing_df['title'].unique().tolist()
    print(f"📊 Existing data: {len(my_dicts)} chunks from {len(existing_titles)} videos/PDFs")
else:
    my_dicts = []
    chunk_id = 0
    existing_titles = []
    print("📊 No existing data found. Starting fresh.")

# ════════════════════════════════════════════════════════════════
# PROCESS JSON FILES
# ════════════════════════════════════════════════════════════════
jsons = [f for f in os.listdir("jsons") if f.endswith('.json')]

if not jsons:
    print("⚠️  No JSON files found in jsons/ directory!")
    exit()

print(f"\n🔍 Found {len(jsons)} JSON files to check\n")

processed_count = 0

for json_file in jsons:
    json_path = f"jsons/{json_file}"
    
    # 🔧 FIX 1: Open with UTF-8 encoding
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except UnicodeDecodeError as e:
        print(f"⚠️  Warning: Unicode error in {json_file}, trying with error handling...")
        try:
            with open(json_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = json.load(f)
        except Exception as e2:
            print(f"❌ Failed to read {json_file}: {e2}")
            continue
    except Exception as e:
        print(f"❌ Failed to read {json_file}: {e}")
        continue
    
    # Check if chunks exist
    if 'chunks' not in content or not content['chunks']:
        print(f"⚠️  Skipping {json_file} - no chunks found")
        continue
    
    # Already processed hai toh skip karo
    title = content['chunks'][0].get('title', 'Unknown')
    if title in existing_titles:
        print(f"⏭️  Skipping {json_file} - already processed")
        continue

    print(f"🔄 Creating Embeddings for {json_file}")
    
    # Create embeddings for all chunks
    texts = [c.get('text', '') for c in content['chunks']]
    
    # Filter out empty texts
    valid_chunks = [c for c in content['chunks'] if c.get('text', '').strip()]
    valid_texts = [c['text'] for c in valid_chunks]
    
    if not valid_texts:
        print(f"⚠️  No valid text found in {json_file}")
        continue
    
    embeddings = create_embedding(valid_texts)

    # 🔧 FIX 2: Add video_url and source_type support
    video_url = content.get('video_url', None)  # Get from metadata
    
    for i, chunk in enumerate(valid_chunks):
        # Add chunk data
        chunk['chunk_id'] = chunk_id
        chunk['embedding'] = embeddings[i]
        
        # 🆕 Add video_url if not present in chunk
        if 'video_url' not in chunk:
            chunk['video_url'] = video_url
        
        # 🆕 Add source_type if not present
        if 'source_type' not in chunk:
            # Determine type based on fields
            if 'page_estimate' in chunk:
                chunk['source_type'] = 'pdf'
            else:
                chunk['source_type'] = 'video'
        
        chunk_id += 1
        my_dicts.append(chunk)
    
    processed_count += 1
    print(f"✅ Processed {len(valid_chunks)} chunks from {json_file}")

# ════════════════════════════════════════════════════════════════
# SAVE TO JOBLIB
# ════════════════════════════════════════════════════════════════
if processed_count == 0:
    print("\n⚠️  No new files to process!")
else:
    df = pd.DataFrame.from_records(my_dicts)
    
    # Ensure required columns exist
    required_cols = ['video_url', 'source_type']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESSING COMPLETE!")
    print(f"{'='*60}")
    print(f"📊 Total chunks: {len(df)}")
    print(f"🎥 Videos: {len(df[df['source_type'] == 'video'])} chunks")
    print(f"📄 PDFs: {len(df[df['source_type'] == 'pdf'])} chunks")
    print(f"🔗 Chunks with video_url: {df['video_url'].notna().sum()}")
    print(f"💾 Saved to: data.embeddings.joblib")
    print(f"{'='*60}\n")
    
    # Show sample
    print("📝 Sample data (first 3 rows):")
    print(df[['number', 'title', 'start', 'end', 'video_url', 'source_type']].head(3))
    
    joblib.dump(df, "data.embeddings.joblib")
    print("\n✅ Saved!")