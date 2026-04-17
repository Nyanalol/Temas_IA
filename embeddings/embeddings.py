"""
embeddings.py — Experimentos con embeddings: tokenización y vectores de frase.

Este script es exploratorio. Corre directamente con:
    python embeddings/embeddings.py   (desde la raíz del proyecto)

No depende de config.py ni de Ollama: los modelos se descargan
automáticamente de Hugging Face y se ejecutan 100% en local.
"""

from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch


# ============================================================
# PARTE 1
# Tokenización y embeddings contextuales con Transformers
# ============================================================

# Este modelo de DeBERTa genera representaciones contextuales.
# "Contextual" significa que el vector de cada token depende de
# las palabras que tiene alrededor.
model_name = "microsoft/deberta-v3-xsmall"

# El tokenizer transforma texto humano en números que el modelo entiende.
tokenizer = AutoTokenizer.from_pretrained(model_name)

# AutoModel devuelve el backbone del modelo, sin cabeza de clasificación.
model = AutoModel.from_pretrained(model_name)

text = "Hello world, my name is Miguel Ángel"

# return_tensors="pt" devuelve tensores de PyTorch.
tokens = tokenizer(text, return_tensors="pt")

print("\n===== TOKENS GENERADOS =====")
print(tokens)

# Qué estás viendo en "tokens":
#   input_ids      → IDs numéricos de cada token
#   token_type_ids → distingue segmentos (aquí todo a 0, solo hay una frase)
#   attention_mask → 1 = token válido, 0 = padding

# model(**tokens) devuelve varias salidas.
# La posición [0] es last_hidden_state: un embedding por cada token.
outputs = model(**tokens)
token_embeddings = outputs[0]

print("\n===== SHAPE DE LOS EMBEDDINGS POR TOKEN =====")
print(token_embeddings.shape)

# torch.Size([1, 10, 384]) significa:
#   1   → batch size (una sola frase)
#   10  → número de tokens
#   384 → dimensión del vector de cada token en este modelo

# IMPORTANTE: aquí todavía NO tienes un único vector para la frase completa.
# Tienes un vector POR CADA TOKEN.


# ============================================================
# PARTE 2
# Embedding de frase completa con Sentence Transformers
# ============================================================

# Este modelo está pensado para similitud semántica, búsqueda y clustering.
# Devuelve directamente un único vector para toda la frase.
sentence_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

sentence_text = "Hello world, my name is Miguel Ángel"

# encode() hace el promedio de los embeddings de tokens internamente.
sentence_embedding = sentence_model.encode(sentence_text)

print("\n===== SHAPE DEL EMBEDDING DE FRASE =====")
print(sentence_embedding.shape)

# (768,) significa:
#   768 → dimensión del vector que representa TODA la frase


# ============================================================
# RESUMEN
# ============================================================

print("\n===== RESUMEN =====")
print("Transformers (AutoModel)   → un vector por token  → shape [batch, tokens, dim]")
print("SentenceTransformer        → un vector por frase  → shape [dim]")
