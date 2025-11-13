"""
Pre-process MTG rules PDF once and save everything
Run this ONCE locally, then commit the output to the repository
"""

import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from rules.parser import RulesParser


def preprocess_rules(pdf_path: str = "mtgrules.pdf"):
    """Pre-process PDF and save all data for deployment"""

    print("=" * 60)
    print("MTG Rules Pre-processor - Run once, commit the results")
    print("=" * 60)

    # Parse PDF
    print("\n[1/4] Parsing PDF...")
    parser = RulesParser(pdf_path)
    rules_data = parser.parse_pdf()

    # Save to JSON
    print("\n[2/4] Saving rules to JSON...")
    with open("rules/rules_data.json", "w", encoding="utf-8") as f:
        json.dump(rules_data, f, ensure_ascii=False, indent=2)

    print(f"   ✓ Saved {len(rules_data['rules'])} rules")
    print(f"   ✓ Saved {len(rules_data['glossary'])} glossary terms")

    # Create documents
    print("\n[3/4] Creating documents...")
    documents = []

    for rule in rules_data["rules"]:
        doc = Document(
            page_content=f"Rule {rule['number']}: {rule['text']}",
            metadata={"rule_number": rule["number"], "section": rule["section"]}
        )
        documents.append(doc)

    for term, entry in rules_data["glossary"].items():
        doc = Document(
            page_content=f"Glossary - {entry['term']}: {entry['definition']}",
            metadata={"type": "glossary", "term": entry["term"]}
        )
        documents.append(doc)

    # Split and create vector store
    print("\n[4/4] Creating vector store (this takes a few minutes)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vector_store = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory="rules/chroma_db"
    )

    print(f"   ✓ Created {len(split_docs)} document chunks")

    print("\n" + "=" * 60)
    print("✓ Done! Files created:")
    print("  - rules/rules_data.json")
    print("  - rules/chroma_db/")
    print("\nNext steps:")
    print("  1. git add rules/")
    print("  2. git commit -m 'Add pre-processed rules data'")
    print("  3. You can now DELETE mtgrules.pdf")
    print("  4. Deploy to Vercel/Render without the PDF!")
    print("=" * 60)


if __name__ == "__main__":
    preprocess_rules()
