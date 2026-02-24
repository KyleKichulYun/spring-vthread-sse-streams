# spring-vthread-sse-streams
"A high-performance real-time SSE broadcasting system built with Java 21 Virtual Threads, Spring Boot 3, Redis Streams, and Next.js." (Java 21 가상 스레드, Spring Boot 3, Redis Streams, Next.js로 구축된 고성능 실시간 SSE 브로드캐스팅 시스템)

# 🚀 High-Concurrency Realtime Event Streams (Spring Boot + Virtual Threads)

![Java](https://img.shields.io/badge/Java-21-blue?style=for-the-badge&logo=openjdk)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.x-6DB33F?style=for-the-badge&logo=spring)
![Redis](https://img.shields.io/badge/Redis_Streams-DC382D?style=for-the-badge&logo=redis)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js)

A high-performance, real-time event broadcasting system designed to handle massive concurrent Server-Sent Events (SSE) connections efficiently using **Java 21 Virtual Threads** and **Redis Streams**.

## 🎯 Project Motivation & Architecture

Traditional thread-per-request models struggle with long-lived connections like SSE, often leading to thread exhaustion or high memory consumption. This project demonstrates how to overcome these limitations by leveraging modern Java features and robust message brokering.

### Why This Tech Stack? (기술 도입 배경)
* **Java 21 Virtual Threads:** Traditional Tomcat allocates one OS thread per SSE connection. By enabling Virtual Threads, blocking operations (like waiting for new events) unmount the virtual thread from the carrier thread, allowing millions of concurrent connections with minimal memory footprint and zero context-switching overhead.
* **Redis Streams:** Unlike standard Redis Pub/Sub (which is fire-and-forget), Redis Streams provides persistent message logging and Consumer Groups. This ensures no message is lost during temporary disconnections and allows horizontal scaling of the Spring Boot application.
* **Next.js & Server-Sent Events (SSE):** SSE is natively supported by browsers (via `EventSource`), making it lightweight and perfect for unidirectional real-time data flow (Server to Client) compared to WebSockets.

## 🏗️ Architecture Flow

```mermaid
sequenceDiagram
    participant Client (Next.js)
    participant Spring Boot (Backend)
    participant Redis (Streams)

    Client (Next.js)->>Spring Boot (Backend): 1. Subscribe to SSE Endpoint (/api/stream)
    Note over Spring Boot (Backend): Handled by Virtual Thread
    Spring Boot (Backend)-->>Client (Next.js): 2. Keep Connection Open
    
    Note over Redis (Streams): External Event Occurs
    Redis (Streams)->>Spring Boot (Backend): 3. Read new messages (Consumer Group)
    Spring Boot (Backend)->>Client (Next.js): 4. Push Event Data (SseEmitter)
