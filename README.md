> A high-performance real-time SSE broadcasting system built with Java 21 Virtual Threads, Spring Boot 3, Redis Streams, and Next.js.
> (Java 21 가상 스레드, Spring Boot 3 AOT, Redis Streams, Next.js로 구축된 고성능 실시간 SSE 브로드캐스팅 시스템)

# 🚀 High-Concurrency Realtime Event Streams (Spring Boot 3 AOT + Virtual Threads)

![Java](https://img.shields.io/badge/Java-21-blue?style=for-the-badge&logo=openjdk)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.x-6DB33F?style=for-the-badge&logo=spring)
![GraalVM](https://img.shields.io/badge/GraalVM-Native_Image-EC2025?style=for-the-badge&logo=graalvm)
![Redis](https://img.shields.io/badge/Redis_Streams-DC382D?style=for-the-badge&logo=redis)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js)

A high-performance, real-time event broadcasting system designed to handle massive concurrent Server-Sent Events (SSE) connections efficiently using **Java 21 Virtual Threads**, **Spring Boot 3 AOT**, and **Redis Streams**.

## 🎯 Project Motivation & Architecture

Traditional thread-per-request models struggle with long-lived connections like SSE, often leading to thread exhaustion or high memory consumption. This project demonstrates how to overcome these limitations by leveraging modern Java features and robust message brokering.

### Why This Tech Stack? (기술 도입 배경)
* **Spring Boot 3 AOT & GraalVM:** Ahead-of-Time (AOT) compilation and native image generation drastically reduce the application's memory footprint and startup time. Combined with Virtual Threads, this creates an ultra-lightweight, highly scalable backend perfect for maintaining thousands of concurrent SSE connections in cloud-native environments.
* **Java 21 Virtual Threads:** Traditional Tomcat allocates one OS thread per SSE connection. By enabling Virtual Threads, blocking operations (like waiting for new events) unmount the virtual thread from the carrier thread, allowing millions of concurrent connections with minimal memory footprint and zero context-switching overhead.
* **Redis Streams:** Unlike standard Redis Pub/Sub (which is fire-and
