# EDID Parsing Pipeline Architecture

This diagram illustrates the high-level architecture of the EDID parsing pipeline, showing the flow of data through the system and the technologies used at each stage.

```mermaid
graph TD
    subgraph "Data Sources"
        PDF[EDID Specification PDF]
        HEX[Example Hex Data]
    end

    subgraph "Extraction & Preprocessing"
        EXTRACT_PDF[extract_pdf.py<br>pdfplumber]
        EXTRACT_HEX[extract_hex_to_bin.py]
        CHUNKS[spec_chunks.json]
        EDID_BIN[edid.bin]
    end

    subgraph "Embedding & Indexing"
        EMBED[embed_store.py<br>OpenAI Embeddings API]
        FAISS[FAISS Vector Index<br>faiss-cpu]
        META[chunk_metadata.json]
    end

    subgraph "Field Discovery & Mapping"
        DISCOVER[discover_fields.py<br>OpenAI GPT-4o-mini]
        MAP[map_fields.py<br>FAISS Similarity Search]
        FIELDS[field_definitions.json]
        MAPPING[field_mapping.json]
    end

    subgraph "Code Generation"
        GENERATE[generate_code.py<br>OpenAI GPT-4o-mini]
        FUNCTIONS[Generated Parsing Functions]
    end

    subgraph "EDID Parsing"
        PARSER[parse_edid.py<br>Dynamic Function Loading]
        OUTPUT[parsed_edid.json]
    end

    %% Data flow connections
    PDF --> EXTRACT_PDF
    EXTRACT_PDF --> CHUNKS
    HEX --> EXTRACT_HEX
    EXTRACT_HEX --> EDID_BIN

    CHUNKS --> EMBED
    EMBED --> FAISS
    EMBED --> META

    FAISS --> DISCOVER
    META --> DISCOVER
    CHUNKS --> DISCOVER
    DISCOVER --> FIELDS

    FIELDS --> MAP
    FAISS --> MAP
    META --> MAP
    MAP --> MAPPING

    MAPPING --> GENERATE
    CHUNKS --> GENERATE
    GENERATE --> FUNCTIONS

    FUNCTIONS --> PARSER
    EDID_BIN --> PARSER
    FIELDS --> PARSER
    PARSER --> OUTPUT

    %% Styling
    classDef dataSource fill:#f9f,stroke:#333,stroke-width:2px;
    classDef dataFile fill:#bbf,stroke:#333,stroke-width:1px;
    classDef process fill:#bfb,stroke:#333,stroke-width:1px;
    classDef technology fill:#fbb,stroke:#333,stroke-width:1px;

    class PDF,HEX dataSource;
    class CHUNKS,EDID_BIN,META,FAISS,FIELDS,MAPPING,FUNCTIONS,OUTPUT dataFile;
    class EXTRACT_PDF,EXTRACT_HEX,EMBED,DISCOVER,MAP,GENERATE,PARSER process;
