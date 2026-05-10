import sys
sys.path.insert(0, '.')

print('Starting...', flush=True)
from vector_store.chroma_manager import ChromaDBManager
print('1. ChromaDBManager imported', flush=True)

import os
os.environ['GOOGLE_API_KEY'] = 'AIzaSyADfqdQk44kB2-g68MRclAQLjFKfdpjXFQ'
import google.generativeai as genai
print('2. genai imported', flush=True)

print('Done!', flush=True)