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

# Cargamos el tokenizer del mismo modelo.
# El tokenizer transforma texto humano en números que el modelo entiende.
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Cargamos el modelo base.
# AutoModel devuelve el backbone del modelo, no una cabeza de clasificación.
model = AutoModel.from_pretrained(model_name)

# Texto de ejemplo.
text = "Hello world, my name is Miguel Ángel"

# Tokenizamos.
# return_tensors="pt" devuelve tensores de PyTorch.
tokens = tokenizer(text, return_tensors="pt")

print("\n===== TOKENS GENERADOS =====")
print(tokens)

# Qué estás viendo en "tokens"
# input_ids
#   Son los ids numéricos de cada token.
# token_type_ids
#   En muchos modelos sirven para distinguir segmentos.
#   Aquí salen a 0 porque solo hay una frase.
# attention_mask
#   Marca con 1 los tokens válidos y con 0 el padding.
#
# En tu output viste:
# torch.Size([1, 10, 384])
# Eso significa:
#   1  -> tamaño del batch, una sola frase
#   10 -> número de tokens generados para esa frase
#   384 -> tamaño del vector de cada token en este modelo

# Pasamos los tokens por el modelo.
# model(**tokens) devuelve varias salidas.
# La posición [0] suele ser last_hidden_state.
# Esa salida contiene un embedding por cada token.
outputs = model(**tokens)
token_embeddings = outputs[0]

print("\n===== EMBEDDINGS POR TOKEN =====")
print(token_embeddings)

print("\n===== SHAPE DE LOS EMBEDDINGS POR TOKEN =====")
print(token_embeddings.shape)

# Resumen mental de esta parte:
# texto
# -> tokenizer
# -> tokens numéricos
# -> modelo
# -> un vector por token
#
# Es decir, NO estás obteniendo todavía un único vector para toda la frase.
# Estás obteniendo un vector para cada token.

# ============================================================
# PARTE 2
# Embedding de frase completo con Sentence Transformers
# ============================================================

# Ahora cargamos un modelo pensado para similitud semántica,
# búsqueda, clustering y comparación entre frases.
#
# A diferencia del bloque anterior, aquí lo normal es obtener
# directamente un único vector para toda la frase.
sentence_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

sentence_text = "Hello world, my name is Ansh"

# encode() devuelve directamente el embedding de la frase completa.
sentence_embedding = sentence_model.encode(sentence_text)

print("\n===== EMBEDDING DE FRASE =====")
print(sentence_embedding)

print("\n===== SHAPE DEL EMBEDDING DE FRASE =====")
print(sentence_embedding.shape)

# En tu output apareció:
# (768,)
#
# Eso significa:
#   768 -> tamaño del vector de la frase completa
#
# Aquí ya no tienes un vector por token.
# Aquí tienes un único vector que resume toda la frase.

# ============================================================
# RESUMEN FINAL
# ============================================================

print("\n===== RESUMEN =====")
print("Transformers con AutoModel devuelve embeddings por token.")
print("SentenceTransformer devuelve un embedding para la frase completa.")