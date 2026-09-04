# Distributed Caching Architecture ⚙️

## Core Strategies
- **Cache-Aside (Lazy Loading)**: Application queries the cache first. On cache miss, it reads from the primary database, writes back to cache, and returns data.
- **Write-Through**: Application writes to cache, and cache immediately persists synchronously to the database.
- **Write-Behind (Write-Back)**: Application writes to cache, and cache asynchronously flushes writes to the database in batch.

## Eviction Policies
1. **LRU (Least Recently Used)**: Evicts items that haven't been accessed for the longest duration.
2. **LFU (Least Frequently Used)**: Tracks access counts and evicts items with the lowest cumulative frequency.
3. **FIFO**: First-in, first-out queue eviction.

## PathEd Milestone Notes
- Mastered Token Bucket sliding rate limiter + Redis cache cluster.
- Implemented O(1) eviction using hash map + doubly linked list.
