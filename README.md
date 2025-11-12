# Tolaria - MTG Rules & Stack Interaction AI Agent

Tolaria è un agente AI che risponde a domande su regole e interazioni di Magic: The Gathering, con visualizzazione della stack.

## Funzionalità

1. **Ricerca Carte**: Integrazione con Scryfall API per cercare carte MTG
2. **Visualizzazione Stack**: Rappresentazione visiva della stack con immagini delle carte
3. **Spiegazione Regole**: Analisi del regolamento ufficiale MTG
4. **Risoluzione Step-by-Step**: Spiegazione passo-passo della risoluzione della stack

## Setup

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

2. Crea un file `.env` con la tua API key di Anthropic:
```bash
cp .env.example .env
# Modifica .env con la tua chiave API
```

3. Avvia il server:
```bash
python main.py
```

## Struttura del Progetto

```
tolaria/
├── main.py                 # Entry point FastAPI
├── mtgrules.pdf           # Regolamento ufficiale MTG
├── requirements.txt       # Dipendenze Python
├── api/
│   └── scryfall.py       # Client Scryfall API
├── rules/
│   ├── parser.py         # Parser del PDF regole
│   └── engine.py         # RAG engine per le regole
├── stack/
│   ├── resolver.py       # Logica risoluzione stack
│   └── visualizer.py     # Creazione rappresentazione visiva
└── frontend/             # Web interface (React)
```

## Utilizzo

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Come si risolve la stack con Counterspell su Lightning Bolt?",
    "cards": ["Counterspell", "Lightning Bolt"]
  }'
```
