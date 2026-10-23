from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from german_compound_splitter import comp_split
import re

app = FastAPI(title="German Compound Splitter Service")

class SplitRequest(BaseModel):
    word: str
    method: str = Field(default='charsplit')

@app.post("/split")
def split_word(request: SplitRequest):
    ahocs = False
    splitter = False

    word = request.word.strip()
    method = request.method.strip()

    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    if method == 'charsplit':
        try:
            if not splitter:
                from charsplit import Splitter
                splitter = Splitter()
            results = splitter.split_compound(word)
            components = [results[0][1], results[0][2]]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to split {word}: {e}.")
    elif method == 'german_compound_splitter':
        try:
            input_file = 'german.dic'
            ahocs = comp_split.read_dictionary_from_file(input_file) if not ahocs else ahocs
            dissection = comp_split.dissect(word, ahocs, make_singular=False)
            components = comp_split.merge_fractions(dissection)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to split {word}: {e}.")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown method {method}.")

    return {
        "word": word,
        "splittable": len(components) > 1,
        "components": components
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
