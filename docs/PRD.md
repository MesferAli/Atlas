# Product Requirements Document (PRD)
# Saudi AI Middleware v2.1

**Document Version:** 2.1 (Final Approved)
**Date:** January 19, 2026
**Owner:** XCircle Enterprise Solutions
**Status:** **APPROVED FOR PRODUCTION**

-----

## Executive Summary
### Product Overview
Saudi AI Middleware v2.1 is an enterprise-grade AI orchestration platform hosted on **Alibaba Cloud (Riyadh)**. It provides intelligent routing between multiple AI providers (Claude, GPT-4o, ALLaM) with built-in Saudi context understanding, PDPL compliance enforcement, and legacy system integration.

### Business Objectives
1. **Reduce AI costs by 30-60%** through intelligent multi-provider routing.
1. **Ensure PDPL compliance** with automatic PII detection and local processing.
1. **Bridge Legacy Systems** by enabling "Chat with Data" for Oracle/ERP databases.
1. **Enable enterprise adoption** with security, audit trails, and compliance.

-----

## 1. Product Vision & Strategy

### 1.1 Vision Statement
*"To become the trusted AI infrastructure layer for Saudi enterprises, enabling secure, compliant, and cost-effective AI adoption at scale."*

### 1.2 Strategic Goals (Updated)
#### Q1 2026 (Current - MVP)
- ✅ Launch MVP on **Alibaba Cloud SA**
- ✅ Onboard 5 enterprise pilot customers
- ✅ **Deploy "Oracle Connector Lite" (Read-Only RAG)** for pilot success
- ✅ Achieve PDPL compliance certification

-----

## 3. Product Features & Requirements

### 3.1 Core Features (MVP - Q1 2026)

#### Feature 4: Oracle Connector Lite (Read-Only) [NEW for MVP]
**Description:** A secure, read-only agent capable of answering natural language queries based on Oracle Database schemas without modifying data.
**Goal:** Enable Pilot customers to "Chat with their ERP" immediately in Q1.
**Technical:** Uses `python-oracledb` Thin Mode via **Atlas Secure Agent** tunnel.
**Security:** Strictly Read-Only permissions. No DDL/DML allowed.

-----

## 4. Technical Architecture

### 4.1 System Architecture (Updated for Alibaba)
- **Cloud Provider:** Alibaba Cloud (Saudi Arabia Region - Riyadh)
- **Database:** PostgreSQL + Redis + Qdrant
- **Integration:** Atlas Secure Agent (Encrypted Tunnel) for Oracle DB

### 4.2 Infrastructure Stack
- **Compute:** ECS (Elastic Compute Service)
- **Orchestration:** ACK (Kubernetes)
- **Registry:** ACR (Enterprise Edition)

-----

## 11. Development Roadmap (Updated)
### 11.1 Q1 2026 (CURRENT)
- [ ] **Alibaba Cloud SA** deployment (ACK + ACR)
- [ ] **Oracle Connector Lite** deployment for Pilot
