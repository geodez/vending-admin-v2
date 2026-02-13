# VPS Gateway Configuration Backup

This directory contains backup copies of the WireGuard and Nginx configurations used during the VPS gateway setup.

## Files

- `wg0.conf` - WireGuard configuration for the Proxmox VM (client side)
- `vending_vps_proxy.conf` - Initial Nginx reverse proxy configuration (VPS side)

## Note

These files are **reference copies only**. The actual working configurations are located on:

- **VPS:** `/etc/wireguard/wg1.conf` and `/etc/nginx/sites-available/vending`
- **Proxmox VM:** `/etc/wireguard/wg0.conf`

Do not use these files directly without reviewing current production settings.
