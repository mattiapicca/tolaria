# Deploy su Vercel

Questa guida spiega come fare il deploy di Tolaria su Vercel.

## Prerequisiti

1. Account Vercel (gratuito): https://vercel.com
2. Vercel CLI (opzionale): `npm i -g vercel`
3. Regole pre-processate (già fatto!)

## Preparazione

### 1. Committa i file pre-processati

```bash
git add rules/rules_data.json rules/chroma_db/
git commit -m "Add pre-processed MTG rules data"
git push
```

### 2. Verifica che tutto sia pronto

Controlla che questi file esistano:
- ✅ `rules/rules_data.json` (~2.3MB)
- ✅ `rules/chroma_db/` (~36MB)
- ✅ `vercel.json`
- ✅ `api/index.py`
- ✅ `.vercelignore`

## Deploy

### Opzione A: Deploy da GitHub (Consigliato)

1. **Vai su Vercel Dashboard**: https://vercel.com/dashboard
2. **Click "Add New Project"**
3. **Importa il tuo repository Git**
4. **Configura le variabili d'ambiente**:
   - Nome: `ANTHROPIC_API_KEY`
   - Valore: La tua chiave API Anthropic
5. **Click "Deploy"**

### Opzione B: Deploy da CLI

```bash
# Installa Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Aggiungi variabile d'ambiente
vercel env add ANTHROPIC_API_KEY

# Deploy in produzione
vercel --prod
```

## Configurazione

### Variabili d'Ambiente Richieste

- `ANTHROPIC_API_KEY`: La tua chiave API di Anthropic

### Limiti Vercel (Piano Gratuito)

- **Timeout**: 10 secondi (abbiamo impostato 60s per Pro)
- **Memoria**: 1GB (abbiamo impostato 3GB per Pro)
- **Dimensione deploy**: 250MB (siamo a ~40MB, OK!)

**Nota**: Se hai il piano gratuito e ricevi timeout, considera:
- Upgrade a Vercel Pro
- Deploy su Render/Railway (già configurati!)

## Struttura del Progetto

```
tolaria/
├── api/
│   ├── index.py        # Entry point Vercel
│   └── scryfall.py     # Scryfall client
├── rules/
│   ├── engine.py       # Rules engine
│   ├── parser.py       # PDF parser (non usato in prod)
│   ├── rules_data.json # Pre-processed rules ✨
│   └── chroma_db/      # Vector store ✨
├── frontend/
│   └── index.html      # Frontend
├── stack/
│   └── resolver.py     # Stack resolver
├── vercel.json         # Vercel config
├── requirements.txt    # Python deps
└── .vercelignore       # Files to ignore
```

## Test del Deploy

Dopo il deploy, testa questi endpoint:

```bash
# Health check
curl https://your-app.vercel.app/health

# Search card
curl https://your-app.vercel.app/api/search-card/Lightning%20Bolt

# Ask question (POST)
curl -X POST https://your-app.vercel.app/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What happens when I cast Lightning Bolt?",
    "cards": ["Lightning Bolt"]
  }'
```

## Troubleshooting

### Errore: "Module not found"
- Verifica che `requirements.txt` contenga tutte le dipendenze
- Controlla i log Vercel per dettagli

### Errore: "Function timeout"
- Piano gratuito: timeout a 10s
- Upgrade a Vercel Pro per 60s
- Alternativa: usa Render/Railway

### Errore: "ANTHROPIC_API_KEY not found"
- Aggiungi la variabile d'ambiente su Vercel Dashboard
- Vai su Settings > Environment Variables

### Vector store non trovato
- Assicurati di aver committato `rules/chroma_db/`
- Verifica che `.vercelignore` NON escluda `rules/`

## Monitoraggio

- **Logs**: https://vercel.com/dashboard > Il tuo progetto > Logs
- **Analytics**: https://vercel.com/dashboard > Il tuo progetto > Analytics
- **Function Metrics**: Monitora timeout e memoria

## Costi

- **Piano Hobby (Free)**:
  - 100GB bandwidth
  - 6000 minuti di esecuzione
  - 10s timeout

- **Piano Pro ($20/mese)**:
  - 1TB bandwidth
  - 60s timeout
  - 3GB memoria

## Alternative

Se Vercel non funziona bene, hai già configurato:
- **Render**: `render.yaml`
- **Railway**: `railway.json`
- **Docker**: `Dockerfile`

Questi sono migliori per ML/AI workloads!

## Link Utili

- Vercel Docs: https://vercel.com/docs
- Vercel Python: https://vercel.com/docs/functions/runtimes/python
- Support: https://vercel.com/support
