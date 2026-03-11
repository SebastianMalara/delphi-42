# DELPHI‑42

### A post‑apocalyptic oracle node for Meshtastic

Delphi‑42 is an experimental **offline oracle node** built on:

-   Meshtastic LoRa mesh network
-   Raspberry Pi
-   Offline knowledge bases (Kiwix / ZIM archives)
-   A small local LLM

It allows people to **ask questions via Meshtastic direct messages**,
and receive short answers generated from an offline knowledge base.

No internet required.

The node also periodically broadcasts **cryptic oracle messages** on the
public mesh to invite nearby nodes to seek it.

------------------------------------------------------------------------

# Concept

In a world without reliable connectivity, knowledge becomes scarce.

Delphi‑42 is a **digital shrine of knowledge**:

-   discoverable through the **Meshtastic mesh**
-   powered by **offline libraries**
-   queryable via **LoRa messages**
-   accessible locally via **WiFi hotspot**

Users can:

1.  ask questions via Meshtastic DM
2.  receive short oracle answers
3.  request the oracle's location
4.  physically travel to the node
5.  connect to its WiFi and access the full knowledge archive

------------------------------------------------------------------------

# Features

## Meshtastic Oracle Bot

The node connects to a Meshtastic radio and:

-   listens for **Direct Messages**
-   ignores public messages
-   answers questions
-   sends periodic **oracle broadcasts** on channel 0

Supported commands (via DM):

    help
    where
    pos
    ask <question>

Examples:

    ask how to purify water
    ask hypothermia symptoms
    where

------------------------------------------------------------------------

## Oracle Broadcasts

Occasionally the node writes on the public channel:

    THE ORACLE LISTENS. SEND DM FOR COUNSEL.
    ASH NODE AWAKE.
    SEEK WISDOM IN PRIVATE.

These messages advertise the oracle without flooding the mesh.

------------------------------------------------------------------------

## Location Sharing

The oracle **never shares its position publicly**.

When asked via DM:

    where

the bot sends a **private position packet** to the requesting node.

------------------------------------------------------------------------

## Offline Knowledge

The oracle retrieves knowledge from **offline datasets** such as:

-   Wikipedia
-   survival manuals
-   first aid
-   repair guides

Content is typically stored in **ZIM archives** and served through
**Kiwix**.

------------------------------------------------------------------------

## Local WiFi Archive

When users physically reach the oracle node, they can connect to its
WiFi hotspot and browse the entire knowledge archive through a local web
interface.

------------------------------------------------------------------------

# System Architecture

    Meshtastic Network
            │
            ▼
       Meshtastic Node
            │ USB
            ▼
    Raspberry Pi Oracle Node
     ├── oracle-bot
     ├── oracle-core
     ├── local LLM
     ├── knowledge index
     └── Kiwix server
            │
            ▼
     WiFi hotspot
            │
            ▼
     users / explorers

------------------------------------------------------------------------

# Software Components

## oracle-bot

Handles Meshtastic communication.

Responsibilities:

-   listen to incoming packets
-   respond to **DM only**
-   publish periodic oracle messages
-   send position packets
-   route queries to oracle-core

------------------------------------------------------------------------

## oracle-core

The reasoning engine.

Responsibilities:

-   classify user intent
-   retrieve knowledge from local index
-   generate short answers using an LLM
-   enforce response length limits

------------------------------------------------------------------------

## Knowledge Index

Offline documents are processed into a searchable index.

Pipeline:

    ZIM archive
       ↓
    text extraction
       ↓
    chunking
       ↓
    SQLite FTS index

------------------------------------------------------------------------

# Hardware

Recommended configuration:

-   Raspberry Pi 5 (16GB)
-   Meshtastic LoRa device
-   SSD storage for knowledge base
-   Solar panel + LiFePO4 battery
-   Weatherproof enclosure

------------------------------------------------------------------------

# Repository Structure

    delphi-42
    │
    ├─ bot
    │  ├─ radio_interface.py
    │  ├─ message_router.py
    │  ├─ command_parser.py
    │  └─ oracle_bot.py
    │
    ├─ core
    │  ├─ oracle_service.py
    │  ├─ retriever.py
    │  ├─ intent.py
    │  ├─ prompt_builder.py
    │  └─ llm_runner.py
    │
    ├─ ingest
    │  ├─ zim_extract.py
    │  ├─ chunker.py
    │  └─ build_index.py
    │
    ├─ config
    │  └─ oracle.yaml
    │
    ├─ systemd
    │  ├─ oracle-bot.service
    │  └─ oracle-core.service
    │
    └─ README.md

------------------------------------------------------------------------

# Installation (planned)

Install Meshtastic Python client:

    pip install meshtastic

Connect radio device:

    /dev/ttyUSB0

Start services:

    systemctl start oracle-bot
    systemctl start oracle-core

------------------------------------------------------------------------

# Roadmap

### Phase 1

-   Meshtastic DM listener
-   command parser
-   oracle broadcasts

### Phase 2

-   knowledge index
-   deterministic answers

### Phase 3

-   local LLM integration

### Phase 4

-   WiFi archive
-   pilgrimage mode

------------------------------------------------------------------------

# Project Status

Early experimental prototype.

------------------------------------------------------------------------

# Inspiration

-   Meshtastic mesh networks
-   Offline internet projects
-   Knowledge shrines
-   Post‑collapse communication systems

------------------------------------------------------------------------

# License

TBD
