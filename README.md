# CDC PulseBot

- [Overview](#overview)
- [Key Features](#key-features)
  - [Dashboard for Situational Monitoring](#dashboard-for-situational-monitoring)
  - [AI-Powered Chat Interface for Rapid Insights](#ai-powered-chat-interface-for-rapid-insights)
- [Mission-Critical Use Cases](#mission-critical-use-cases)
  - [Early Detection of Emerging Symptoms and Outbreaks](#early-detection-of-emerging-symptoms-and-outbreaks)
  - [Real-Time Situation Awareness During Health Crises](#real-time-situation-awareness-during-health-crises)
  - [Supplementing Surveillance with Unstructured Data Streams](#supplementing-surveillance-with-unstructured-data-streams)
  - [Rapid Behavioral Health and Intervention Monitoring](#rapid-behavioral-health-and-intervention-monitoring)
  - [Accelerating Hypothesis Formation for Field Investigations](#accelerating-hypothesis-formation-for-field-investigations)
  - [Enabling Faster Decision-Making Through AI-Assisted Summarization](#enabling-faster-decision-making-through-ai-assisted-summarization)
- [Architecture](#architecture)
  - [Architecture Diagram](#architecture-diagram)
  - [Process A: Tweet Ingestion and Indexing (tweets-ingestion-app)](#process-a-tweet-ingestion-and-indexing-tweets-ingestion-app)
  - [Process B: AI Enrichment and Vector Embedding (tweets-search)](#process-b-ai-enrichment-and-vector-embedding-tweets-search)
  - [Process C: Dashboard and Chat App (tweets_analysis_app)](#process-c-dashboard-and-chat-app-tweets_analysis_app)
- [Security](#security)
  - [Networking Architecture](#networking-architecture)
  - [Networking Diagram](#networking-diagram)
  - [Secure AI Chat with Internal Data](#secure-ai-chat-with-internal-data)
  - [FedRAMP-High and Zero Trust Compatibility](#fedramp-high-and-zero-trust-compatibility)
- [Deployment](#deployment)
  - [tweets-ingestion-app](#tweets-ingestion-app)
  - [tweets-search](#tweets-search)
  - [tweets_analysis_app](#tweets-analysis-app)

## Overview

**CDC PulseBot** is a real-time public health surveillance tool designed to strengthen the CDC's ability to detect early health signals, monitor emerging public health concerns, and respond faster to evolving situations. By indexing tweets mentioning the CDC and enabling retrieval-augmented generation (RAG) search capabilities powered by OpenAI, PulseBot provides leadership and analysts a new channel of timely, actionable information extracted directly from public discourse.

PulseBot complements traditional surveillance efforts by offering a faster, broader view of emerging health issues from unstructured data streams.

---

## Key Features

### Dashboard for Situational Monitoring

- **Time-Targeted Analysis**  
  Enables CDC teams to track changes in public conversation across customizable periods, supporting real-time situational assessments during outbreaks or emergency events.

- **Population Engagement Metrics**  
  Measures tweet volume, sentiment shifts, and language diversity to help identify when and where public health issues are gaining traction.

- **Entity Extraction for Thematic Awareness**  
  Automatically surfaces symptoms, diseases, organizations, and emerging topics under public discussion, supporting early warning systems.

- **Top Tweets for Signal Amplification**  
  Highlights influential public posts that may indicate emerging health narratives or public concerns needing closer monitoring.

### AI-Powered Chat Interface for Rapid Insights

- **Natural Language Operational Queries**  
  Allows CDC analysts to quickly pose operationally relevant questions (e.g., "What symptoms are being discussed?", "What public concerns are surfacing?") without technical query construction.

- **OpenAI Summarization for Decision Support**  
  Synthesizes large volumes of public chatter into concise, source-backed summaries, speeding up information processing during critical response windows.

- **Source Transparency and Traceability**  
  Displays top retrieved tweets alongside summaries to maintain traceability and confidence in AI-generated insights.

- **Follow-Up Exploration**  
  Suggests next steps for deeper investigation, supporting iterative analysis as public health events unfold.

---

## Mission-Critical Use Cases

### Early Detection of Emerging Symptoms and Outbreaks

CDC teams can identify mentions of new or unusual symptoms circulating in the public weeks before they appear in structured clinical datasets, supporting faster epidemiological investigation and containment measures.

### Real-Time Situation Awareness During Health Crises

During pandemics, natural disasters, or localized outbreaks, PulseBot allows leadership to access synthesized, up-to-date reports of public concerns, barriers to healthcare access, or evolving needs, improving response targeting and speed.

### Supplementing Surveillance with Unstructured Data Streams

PulseBot enhances the CDC's surveillance capacity by filling gaps left by traditional data sources, capturing real-time observations and concerns from diverse communities without the delay of formal reporting channels.

### Rapid Behavioral Health and Intervention Monitoring

By querying public reactions to new health guidelines, interventions, or programs, analysts can monitor adoption barriers and behavioral responses in near real time, allowing for dynamic adjustments to public health strategies.

### Accelerating Hypothesis Formation for Field Investigations

PulseBot supports field epidemiology by surfacing early themes and issues (e.g., "Is there increased discussion about water contamination in affected regions?") that can guide survey development, interviews, and sampling strategies.

### Enabling Faster Decision-Making Through AI-Assisted Summarization

Through OpenAI-powered summarization of retrieved tweet content, analysts can transition from raw unstructured data to actionable insights within minutes, supporting faster, better-informed operational decisions during fast-moving health events.

---
## Architecture

### Architecture Diagram

![Architecture Diagram](docs/PulseBotArchDiagram.png)

### Process A: Tweet Ingestion and Indexing (tweets-ingestion-app)

### Process B: AI Enrichment and Vector Embedding (tweets-search)

### Process C: Dashboard and Chat App (tweets_analysis_app)

## Security

### Networking Architecture

PulseBot’s current deployment is secured using Azure Virtual Network (VNet) integration with Service Endpoints. This design ensures that communication between Azure services—including ingestion functions, storage accounts, and cognitive search—is routed entirely through the Azure backbone network without traversing the public internet.

Key elements of the current security posture include:
- Azure Function App and Web App are integrated into the Virtual Network.
- Azure Storage and Azure Cognitive Search are accessed using Service Endpoints tied to the Virtual Network.
- Data transmission between services remains internal to Microsoft's protected infrastructure.

This architecture provides several security advantages:
- **Reduced Attack Surface**: No public IP exposure for core services minimizes potential external threats.
- **Data-in-Transit Protection**: Traffic between services remains confined to private, secured Azure infrastructure.
- **Stronger Access Control**: Integration with VNets enables enforcement of network security groups (NSGs) and route tables for further traffic filtering and segmentation.
- **Operational Efficiency**: Secure communication is achieved without sacrificing performance, scalability, or manageability for cloud-native applications.

#### Networking Diagram

![Networking Diagram](path-or-link-to-diagram.png)

### Secure AI Chat with Internal Data

PulseBot is currently an open-source project that demonstrates AI-powered natural language chat over a public dataset (Twitter data). However, the architecture is specifically designed to support private, internal datasets in secure environments.

Key points:
- **Internal-Only Data Handling**: When deployed into a CDC-controlled Azure environment, all ingestion, indexing, retrieval, and AI summarization occur entirely within CDC-managed cloud resources.
- **Azure OpenAI Private Deployments**: PulseBot uses Azure OpenAI models, which can be deployed privately inside the CDC’s Azure subscription. No public OpenAI services (e.g., ChatGPT API) are required.
- **No External Data Transmission**: Neither the user’s questions nor the underlying data are ever sent outside the secured Azure environment when properly deployed.
- **Designed for Sensitive Data**: While public social media data is used for demonstration today, the system is architected to support sensitive or classified datasets without modification.

This enables CDC teams to chat with internal datasets securely, leveraging modern AI capabilities while maintaining full control over information security and compliance standards.

### FedRAMP-High and Zero Trust Compatibility

While the current deployment leverages Service Endpoints for backbone isolation, PulseBot's modular architecture and deployment pipelines are designed to support migration to higher-assurance architectures required by federal agencies. Specifically, the solution can be adapted to:

- **Private Endpoints**: Replace Service Endpoints with Private Endpoints, ensuring all service communication occurs entirely within private address spaces and cannot be accessed via the public internet.
- **Private DNS Zones**: Integrate with Private DNS Zones for internal resolution of Azure service names to private IPs, maintaining full control over network name resolution.
- **Complete Internet Isolation**: Configure services to eliminate all public IP exposure, meeting requirements for fully isolated cloud environments.
- **Secure CI/CD Pipelines**: Adapt GitHub Actions workflows to operate through private build agents or self-hosted runners within CDC-controlled networks.
- **Compliance Alignment**: PulseBot’s design supports deployment scenarios that meet or align with:
  - **FedRAMP High** security baselines
  - **FISMA Moderate/High** system security categorizations
  - **Trusted Internet Connection (TIC 3.0)** guidelines for federal cloud deployments
  - **Zero Trust Architecture (ZTA)** principles when combined with appropriate access control and telemetry solutions

---

## Deployment

This repository contains modular application components designed for teams who have provisioned their Azure infrastructure.

### tweets-ingestion-app

Python Azure Function App that ingests CDC-related tweets from Twitter, processes them, and indexes them into Azure AI Search for retrieval and enrichment.

### tweets-search

JSON definitions for configuring Azure AI Search components, including:
- Search Index schema
- Skillset for enrichment (entity recognition, key phrase extraction)
- Indexer for data ingestion
- Data source connection (e.g., Azure Blob Storage)

This module enables semantic enrichment and vector-based retrieval capabilities.

### tweets_analysis_app

FastAPI web application providing:
- Dashboard for visualizing key metrics, trends, and entities
- RAG-based Chat Interface for asking natural language questions against the indexed tweet data
- Backend services with Pydantic models and Jinja templates for dynamic page rendering

This component allows CDC analysts and leadership to interact with the data visually and conversationally.

> **Note:**  
> Infrastructure as Code (IaC) templates are not included. Azure services (e.g., Azure Functions, AI Search, Storage Accounts, Web App) must be provisioned manually before deploying these components.


---
