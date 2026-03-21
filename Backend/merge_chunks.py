import os
import json
import math

n = 50          # chunks per group
overlap = 10    # chunks to overlap

for filename in os.listdir("jsons"):
    if filename.endswith(".json"):
        file_path = os.path.join("jsons", filename)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        new_chunks = []
        chunks = data["chunks"]
        num_chunks = len(chunks)

        step = n - overlap  # shift window
        i = 0

        while i < num_chunks:
            start_idx = i
            end_idx = min(i + n, num_chunks)

            chunk_group = chunks[start_idx:end_idx]

            new_chunks.append({
                "number": chunk_group[0]["number"],
                "title": chunk_group[0]["title"],
                "start": chunk_group[0]["start"],
                "end": chunk_group[-1]["end"],
                "text": " ".join(c["text"] for c in chunk_group)
            })

            i += step  # move window forward

        # Save file
        os.makedirs("newjsons", exist_ok=True)
        with open(os.path.join("newjsons", filename), "w", encoding="utf-8") as json_file:
            json.dump({"chunks": new_chunks, "text": data["text"]}, json_file, indent=4)
