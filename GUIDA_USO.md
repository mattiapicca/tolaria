# 🧙‍♂️ Tolaria - Guida all'Uso

Tolaria è un agente AI completo per rispondere a domande su regole e interazioni di Magic: The Gathering, con visualizzazione della stack.

## ✨ Funzionalità Principali

1. **Ricerca Carte** - Integrazione con Scryfall API per recuperare dati e immagini di carte MTG
2. **Analisi Regole** - Parsing del regolamento ufficiale MTG (304 pagine, 1936 regole)
3. **Vector Database** - 4723 chunk indicizzati per ricerca semantica veloce
4. **Stack Resolver** - Risoluzione corretta della stack con ordine LIFO
5. **Visualizzazione Interattiva** - Carte sovrapposte con immagini reali
6. **AI Explanations** - Spiegazioni dettagliate powered by Claude AI

## 🚀 Avvio Rapido

### 1. Installazione Dipendenze

```bash
pip install -r requirements.txt
pip install langchain-community  # Richiesto per vector store
```

### 2. Configurazione API Key

Crea/modifica il file `.env`:

```bash
ANTHROPIC_API_KEY=your_api_key_here
PORT=8000
```

**IMPORTANTE**: Assicurati di avere crediti disponibili sul tuo account Anthropic.

### 3. Avvio Server

```bash
python3 main.py
```

Il server si avvierà su `http://localhost:8000`

**Nota**: La prima inizializzazione richiede ~2 minuti per:
- Parsing del PDF delle regole (304 pagine)
- Creazione del vector database
- Caricamento dei modelli di embedding

### 4. Accesso Web Interface

Apri il browser a: **http://localhost:8000**

## 📖 Come Usare l'Interfaccia Web

### Passo 1: Inserisci la Domanda

Esempio:
```
Player 1 gioca Lightning Bolt con target Player 2.
Player 2 risponde con Counterspell su Lightning Bolt.
Come si risolve la stack?
```

### Passo 2: Aggiungi le Carte

Inserisci i nomi delle carte coinvolte:
- Lightning Bolt
- Counterspell

Clicca "Aggiungi" per ogni carta.

### Passo 3: Analizza

Clicca **"🔍 Analizza Interazione"**

### Risultati

Riceverai:

1. **Spiegazione Dettagliata**
   - Come si risolve la situazione
   - Perché succede così secondo le regole
   - Cosa succede ai permanenti/giocatori

2. **Riferimenti alle Regole**
   - Numeri specifici delle regole citate
   - Sezioni rilevanti del comprehensive rules

3. **Visualizzazione Stack**
   - Ordine delle carte sulla stack
   - Sequenza di risoluzione (LIFO)
   - Carte sovrapposte con immagini

4. **Resolution Steps**
   - Passo-passo cosa succede
   - Stato della stack dopo ogni step

## 🔧 Utilizzo API

### Endpoint Principale

**POST** `/api/ask`

```json
{
  "question": "La tua domanda sulle regole",
  "cards": ["Card Name 1", "Card Name 2"],
  "player_actions": [
    {
      "card": "Lightning Bolt",
      "player": "Player 1",
      "targets": ["Player 2"]
    },
    {
      "card": "Counterspell",
      "player": "Player 2",
      "targets": ["Lightning Bolt"]
    }
  ]
}
```

### Risposta

```json
{
  "stack_visualization": [
    {
      "card": { /* dati carta da Scryfall */ },
      "controller": "Player 1",
      "targets": ["Player 2"],
      "position": 0
    }
  ],
  "resolution_steps": [
    {
      "step_number": 1,
      "action": "Resolve Counterspell",
      "description": "...",
      "state_after": "..."
    }
  ],
  "explanation": "Spiegazione dettagliata...",
  "rules_references": ["405.1", "608.2a"]
}
```

### Altri Endpoint

**GET** `/api/search-card/{card_name}` - Cerca una singola carta
**GET** `/health` - Health check del server

## 💡 Esempi di Domande

### Esempio 1: Counterspell Base
```
Domanda: Come si risolve Counterspell su Lightning Bolt?
Carte: Lightning Bolt, Counterspell
```

**Risposta attesa**:
1. Player 1 gioca Lightning Bolt (va sulla stack)
2. Player 2 risponde con Counterspell targeting Lightning Bolt
3. Counterspell risolve per primo (LIFO)
4. Lightning Bolt viene counterato e non risolve

### Esempio 2: Combat Tricks
```
Domanda: Player 1 attacca con una creatura 2/2.
Player 2 gioca Giant Growth sul bloccantefor 3/3.
Player 1 risponde con Lightning Bolt.
Chi vince il combattimento?
Carte: Giant Growth, Lightning Bolt
```

### Esempio 3: Priorità
```
Domanda: Come funziona la priorità quando si risponde a uno spell?
Carte: (nessuna specifica)
```

## 🎨 Visualizzazione Stack

La visualizzazione mostra:

1. **Carte Sovrapposte**
   - TOP OF STACK chiaramente marcato
   - Ultima carta giocata completamente visibile
   - Offset di 80px per vedere tutte le carte

2. **Badge Posizione**
   - Numero indica la posizione nella stack
   - 1 = bottom, N = top

3. **Controller Labels**
   - Chi ha giocato la carta
   - Nome della carta

4. **Ordine di Gioco vs Risoluzione**
   - **Ordine di Gioco**: cronologico (prima → dopo)
   - **Ordine di Risoluzione**: LIFO (top → bottom)

5. **Spell Counterati**
   - Sfondo rosso
   - Messaggio "viene counterato e non risolve"
   - Non appare nella risoluzione finale

## 🐛 Troubleshooting

### Errore: "credit balance is too low"
**Soluzione**: Verifica/ricarica i crediti su console.anthropic.com

### Errore: "Module not found"
**Soluzione**:
```bash
pip install langchain-community
pip install sentence-transformers
```

### Server lento al primo avvio
**Normale**: Il parsing del PDF richiede ~2 minuti la prima volta

### Port 8000 già in uso
**Soluzione**: Cambia PORT nel file `.env`

### Carte non trovate
**Verifica**:
- Nome corretto (usa Scryfall fuzzy search)
- Connessione internet attiva
- Rispetta rate limits di Scryfall (100ms tra richieste)

## 📚 Struttura Codice

```
tolaria/
├── main.py                 # FastAPI server
├── mtgrules.pdf           # Comprehensive Rules
├── api/
│   └── scryfall.py       # Scryfall API client
├── rules/
│   ├── parser.py         # PDF parser
│   └── engine.py         # RAG engine + Claude AI
├── stack/
│   ├── resolver.py       # Stack resolution logic
│   └── visualizer.py     # HTML visualization
└── frontend/
    └── index.html        # Web interface
```

## 🔐 Sicurezza

- Non committare mai `.env` con le API key
- `.env` è già in `.gitignore`
- Usa variabili d'ambiente in production

## 🚦 Performance

### Tempi Tipici

- **Startup**: ~120 secondi (parsing + vector DB)
- **Query con AI**: ~5-10 secondi
- **Query solo carte**: ~1 secondo
- **Visualizzazione**: istantanea

### Cache

- Vector database salvato in `chroma_db/`
- Riavvii successivi più veloci (non re-parse PDF)
- Elimina `chroma_db/` per rigenerare

## 📝 Note Tecniche

### Regole Parsate
- **Total Rules**: 1936
- **Glossary Terms**: 737
- **Document Chunks**: 4723
- **Stack Rules**: 198 specifiche

### Dependencies Key
- **FastAPI**: Web server
- **Anthropic**: Claude AI per spiegazioni
- **Scryfall**: Database carte MTG
- **LangChain**: RAG framework
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings

## 🎯 Roadmap Future

- [ ] Support per abilities triggered
- [ ] Multiple stack states visualization
- [ ] Export come PDF/immagine
- [ ] Database di esempi comuni
- [ ] Support per formati specifici (Commander, etc.)
- [ ] Interfaccia mobile ottimizzata

## 📞 Support

Per bug o feature requests, apri una issue nel repository.

---

Creato con ❤️ per la community di Magic: The Gathering
