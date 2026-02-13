# VPS Gateway & Secure Tunneling Setup

## Overview
This document describes the networking architecture implemented to provide stable external access to the Vending Admin v2 project hosted on a Proxmox VM in Russia. Due to regional instability of Cloudflare Tunnels (Error 1033/530), a custom VPS-based gateway was established.

## Architecture
- **Entry Point:** VPS Gateway (Location: Outside Russia)
- **Host VM:** Proxmox VM (Location: Russia)
- **Tunnel:** WireGuard (encrypted host-to-host tunnel)
- **Protocol Proxy:** Nginx (VPS) -> WireGuard -> Nginx (Proxmox)

## Components & Configuration

### 1. WireGuard Tunnel
A dedicated WireGuard interface (`wg1` on VPS, `wg0` on Proxmox) establishes a private network `10.8.0.0/24`.

- **Proxmox IP:** `10.8.0.10`
- **VPS IP:** `10.8.0.1`
- **Port:** `51821` (Custom port to avoid conflicts with existing VPN services)

### 2. MTU & MSS Optimization (Critical)
To bypass ISP traffic "throttling" and ensure large bundles (JS/CSS) load correctly, the following optimizations were applied:
- **MTU:** Set to `1200` on both ends of the tunnel.
- **MSS Clamping:** Applied via `iptables` to automatically resize TCP segments.
  ```bash
  # Command applied on both VPS and Proxmox
  sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
  ```

### 3. Nginx Gateway (VPS)
Nginx on the VPS acts as the SSL termination point and reverse proxy.
- **SSL:** Managed by Certbot (Let's Encrypt).
- **Optimizations:**
    - `proxy_buffering off;` (reduces latency for stream-like delivery).
    - `gzip on;` (compresses large JS bundles before sending them through the tunnel).
    - Hardcoded `proxy_pass http://10.8.0.10:80;`.

### 4. DNS Configuration
- **Domain:** `romanrazdobreev.store`
- **Mode:** "Grey Cloud" (DNS Only) in Cloudflare.
- **Reason:** Direct connection to the VPS IP avoids potential Cloudflare blocklists in the destination region.

## Troubleshooting & Maintenance
- **Check Tunnel Status:** `sudo wg show`
- **Restart Tunnel:** `sudo wg-quick down wg0 && sudo wg-quick up wg0`
- **Nginx Logs (VPS):** `tail -f /var/log/nginx/access.log`
- **Certificate Renewal:** Managed automatically by `certbot` timer.

---
*Last updated: 2026-02-13 by Antigravity Assistant*
