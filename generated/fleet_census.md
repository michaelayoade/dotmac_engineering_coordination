# Fleet census

- Provider observation: `2026-09-03T07:57:37+00:00`
- Workload observation: `2026-09-03T08:20:48+00:00`
- Declared hosts: `28`
- Running Docker containers: `193`
- Declared virtual guests: `20`
- Evidence: `provider_record` plus `live_observation`

Provider state does not decide declared purpose or lifecycle. Guest addresses report configured interfaces, not external reachability.

| Host | Provider hostname | Provider label | Guest hostname | IPv4 | IPv6 | Containers | Purpose |
|---|---|---|---|---|---|---:|---|
| `academy` | `vmi2490731` | academy LMS | `vmi2490731.contaboserver.net` | `149.102.135.97` | `2a02:c204:2249:731::1/64` | 2 | Dotmac Academy application |
| `control-runner` | `not-applicable` | on-prem | `dotmac-control-runner` | `160.119.127.188` | `not-declared` | 0 | Repository-scoped deployment control runners |
| `db-primary` | `vmi3291426` | db-primary - postgres redis standbys | `dotmac-db-primary` | `75.119.157.91` | `2a02:c207:2329:1426::1/64` | 10 | Primary database host; PostgreSQL and Redis standbys |
| `dotmac-labs` | `not-applicable` | on-prem | `workload observation missing` | `10.120.120.42` | `2c0f:e888:11:0:be24:11ff:fef3:6290` | 0 | Dotmac Academy lab runtime and containerlab worker |
| `erp` | `vmi2988431` | erp dotmac | `vmi2988431.contaboserver.net` | `149.102.158.167` | `2a02:c204:2298:8431::1/64` | 6 | Dotmac ERP application |
| `garki-core` | `not-applicable` | on-prem | `workload observation missing` | `160.119.127.252` | `2c0f:e888::252` | 0 | Abuja Garki core router and Dotmac Labs IPv4 egress/IPv6 edge |
| `idp-ha-1` | `vmi3537544` | idp-ha-1 | `vmi3537544.contaboserver.net` | `94.72.109.54` | `2a02:c204:2353:7544::1/64` | 1 | Identity provider HA node 1 |
| `idp-ha-2` | `vmi3537543` | idp-ha-2 | `vmi3537543` | `158.220.86.76` | `2a02:c204:2353:7543::1/64` | 1 | Identity provider HA node 2 |
| `idp-ha-3` | `vmi3537726` | idp-ha-3 | `vmi3537726.contaboserver.net` | `158.220.87.55` | `2a02:c204:2353:7726::1/64` | 1 | Identity provider HA node 3 |
| `idp-live` | `vmi3511689` | idp LIVE - keycloak and sub shadow | `idp` | `158.220.86.10` | `2a02:c204:2351:1689::1/64` | 5 | Identity provider; Keycloak and Sub shadow |
| `integrator-vendor-control` | `vmi2988430` | integrator and vendor control plane | `vmi2988430.contaboserver.net` | `149.102.158.144` | `2a02:c204:2298:8430::1/64` | 4 | Integrator and Vendor Control Plane |
| `mail-dotmac` | `vmi3492684` | mail dotmac ng | `mail.dotmac.ng` | `94.72.106.173` | `2a02:c204:2349:2684::1/64` | 18 | Mail for dotmac.ng |
| `mail-nhia` | `vmi3492689` | mail nhia gov ng | `mail.nhia.gov.ng` | `94.72.108.27` | `2a02:c204:2349:2689::1/64` | 18 | Mail for nhia.gov.ng |
| `nhia-moh-cloud` | `vmi2486898` | nhia and moh cloud - collabora nextcloud | `vmi2486898.contaboserver.net` | `149.102.130.231` | `2a02:c204:2248:6898::1/64` | 9 | NHIA and Ministry of Health cloud workloads |
| `ns1` | `not-applicable` | on-prem | `ns1.dotmac.ng` | `10.120.120.51` | `2c0f:e888:11:0:be24:11ff:fe2c:3ba8` | 0 | Authoritative DNS ns1.dotmac.ng |
| `ns2` | `vmi3519226` | ns2 dotmac ng | `ns2.dotmac.ng` | `169.58.201.243` | `2a02:c207:2351:9226::1/64` | 0 | Authoritative DNS ns2.dotmac.ng |
| `ns3` | `vmi3519229` | ns3 dotmac ng | `ns3.dotmac.ng` | `158.220.82.88` | `2a02:c204:2351:9229::1/64` | 0 | Authoritative DNS ns3.dotmac.ng |
| `observability-canary` | `vmi3537605` | SPARE - hardened 6vcpu 11gb ready to use | `vmi3537605.contaboserver.net` | `94.72.99.155` | `2a02:c204:2353:7605::1/64` | 0 | Reserved inactive host-only observability canary |
| `observe` | `vmi3291425` | observe - grafana prometheus openbao knowledge | `dotmac-observe` | `75.119.128.247` | `2a02:c207:2329:1425::1/64` | 28 | Grafana, Prometheus, OpenBao and Knowledge |
| `proxmox` | `not-applicable` | on-prem | `dotmacproxmox.local` | `10.120.120.20` | `2c0f:e888:11::14` | 0 | Single-node Proxmox VE hypervisor for Dotmac network and control-plane virtual machines |
| `s3` | `vmi3291427` | s3 minio AND forgejo registry | `dotmac-s3` | `194.163.130.216` | `2a02:c207:2329:1427::1/64` | 6 | MinIO object storage, Forgejo and registry |
| `seabone` | `not-applicable` | on-prem | `hp-server` | `160.119.127.195` | `2c0f:e888:12:0:1e98:ecff:fe11:3628` | 50 | On-prem application host for Sub, ERP, retired CRM/Omni, and staging workloads |
| `son-erp` | `vmi3027474` | son erp | `vmi3027474.contaboserver.net` | `149.102.149.5` | `2a02:c204:2302:7474::1/64` | 6 | SON ERP; CRM is retired |
| `sub-prod` | `vmi3348415` | sub prod | `vmi3348415.contaboserver.net` | `94.72.107.76` | `2a02:c204:2334:8415::1/64` | 27 | Dotmac Sub production |
| `test-server` | `vmi3537655` | testing server | `vmi3537655.contaboserver.net` | `85.190.246.211` | `2a02:c204:2353:7655::1/64` | 0 | Dedicated non-production test server |
| `web-cache` | `not-applicable` | on-prem | `web-cache` | `10.120.120.22` | `2c0f:e888:11:0:be24:11ff:fedc:a12d` | 0 | On-prem web cache |
| `workspace` | `vmi3511803` | workspace | `workspace` | `94.72.104.67` | `2a02:c204:2351:1803::1/64` | 1 | Dotmac Workspace |
| `zabbix` | `not-applicable` | on-prem | `zabbix` | `160.119.127.193` | `2c0f:e888:11:0:be24:11ff:fe3a:953b` | 0 | On-prem Zabbix monitoring |

## Provider private networks

- `idp` (`10.0.0.0/22`, id `61441`): 0 attached instances.

## Drift

- `provider_non_running_host_ids`: none
- `missing_provider_host_ids`: none
- `unknown_provider_host_ids`: none
- `provider_address_mismatch_host_ids`: none
- `missing_guest_ipv4_host_ids`: none
- `missing_guest_ipv6_host_ids`: `nhia-moh-cloud`
- `missing_workload_host_ids`: `dotmac-labs`, `garki-core`
- `unknown_workload_host_ids`: none

## Agent access

Pointers identify where credentials are held; this report never dereferences them.

| Host | SSH alias | User | Route | Identity pointer | Recovery pointer | API access |
|---|---|---|---|---|---|---|
| `academy` | `academy` | `root` | `academy` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/academy#root_password` | none declared |
| `control-runner` | `control-runner` | `dotmac` | `via seabone to 10.120.120.52` | `local-key:~/dotmac-network/ssh-keys/proxmox-server` | `not verified` | none declared |
| `db-primary` | `db-primary` | `root` | `db-primary` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/db-primary#root_password` | none declared |
| `dotmac-labs` | `dotmac-labs` | `dotmac` | `via seabone to 10.120.120.42` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `erp` | `erp` | `root` | `erp` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/erp#root_password` | none declared |
| `garki-core` | `garki-core` | `dottmacc` | `160.119.127.252` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `idp-ha-1` | `idp-ha-1` | `root` | `idp-ha-1` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `idp-ha-2` | `idp-ha-2` | `root` | `idp-ha-2` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `idp-ha-3` | `idp-ha-3` | `root` | `idp-ha-3` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `idp-live` | `idp-live` | `root` | `idp-live` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/keycloak#root_password` | none declared |
| `integrator-vendor-control` | `integrator-vendor-control` | `root` | `integrator-vendor-control` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `mail-dotmac` | `mail-dotmac` | `root` | `mail-dotmac` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/mail-dotmac#root_password` | none declared |
| `mail-nhia` | `mail-nhia` | `root` | `mail-nhia` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/mail-nhia#root_password` | none declared |
| `nhia-moh-cloud` | `nhia-moh-cloud` | `root` | `nhia-moh-cloud` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/cloud-nhia#root_password` | none declared |
| `ns1` | `ns1` | `root` | `via seabone to 10.120.120.51` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/ns1#root_password` | none declared |
| `ns2` | `ns2` | `root` | `ns2` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/ns2#root_password` | none declared |
| `ns3` | `ns3` | `root` | `ns3` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/ns3#root_password` | none declared |
| `observability-canary` | `observability-canary` | `root` | `observability-canary` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `observe` | `observe` | `root` | `observe` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/observe#root_password` | none declared |
| `proxmox` | `proxmox` | `root` | `via seabone to 10.120.120.20` | `local-key:~/dotmac-network/ssh-keys/proxmox-server` | `not verified` | proxmox-cluster-via-pvesh: verified (ssh://proxmox/pvesh); proxmox-https-api: verified (https://10.120.120.20:8006/api2/json) [bao://secret/dotmac/proxmox/fleet-inventory#api_token] |
| `s3` | `s3` | `root` | `s3` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/s3#root_password` | none declared |
| `seabone` | `seabone` | `dotmac` | `160.119.127.195` | `local-key:~/.ssh/id_ed25519_seabone` | `not verified` | none declared |
| `son-erp` | `son-erp` | `root` | `son-erp` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/crm#root_password` | none declared |
| `sub-prod` | `sub-prod` | `root` | `sub-prod` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/sub-prod#root_password` | none declared |
| `test-server` | `test-server` | `root` | `test-server` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `web-cache` | `web-cache` | `root` | `via seabone to 10.120.120.22` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |
| `workspace` | `workspace` | `root` | `workspace` | `local-key:~/.ssh/id_ed25519` | `bao://secret/dotmac/hosts/workspace#root_password` | none declared |
| `zabbix` | `zabbix` | `zabbixdotmac` | `160.119.127.193` | `local-key:~/.ssh/id_ed25519` | `not verified` | none declared |

## Containers by host

### academy

| Container | Image | State | Health |
|---|---|---|---|
| `academy-db` | `postgres:16` | `running` | `healthy` |
| `promtail` | `grafana/promtail:3.0.0` | `running` | `not-reported` |

### control-runner

Host-only; Docker is not installed.

### db-primary

| Container | Image | State | Health |
|---|---|---|---|
| `dotmac-postgres` | `postgis/postgis:16-3.4-alpine` | `running` | `healthy` |
| `dotmac-redis` | `redis:7-alpine` | `running` | `healthy` |
| `dotmac_erp_standby` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_omni_standby` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_splynx_source_audit` | `mysql:8.0` | `running` | `not-reported` |
| `dotmac_sub_funding_audit` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_sub_standby` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `node-exporter` | `prom/node-exporter:latest` | `running` | `not-reported` |
| `postgres-exporter` | `quay.io/prometheuscommunity/postgres-exporter:latest` | `running` | `not-reported` |
| `redis-exporter` | `oliver006/redis_exporter:latest` | `running` | `not-reported` |

### erp

| Container | Image | State | Health |
|---|---|---|---|
| `dotmac_erp_app` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `healthy` |
| `dotmac_erp_beat` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `not-reported` |
| `dotmac_erp_redis` | `redis:7` | `running` | `not-reported` |
| `dotmac_erp_worker` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `not-reported` |
| `dotmac_pg_local` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `promtail` | `grafana/promtail:latest` | `running` | `not-reported` |

### idp-ha-1

| Container | Image | State | Health |
|---|---|---|---|
| `keycloak` | `quay.io/keycloak/keycloak:26.0` | `running` | `not-reported` |

### idp-ha-2

| Container | Image | State | Health |
|---|---|---|---|
| `keycloak` | `quay.io/keycloak/keycloak:26.0` | `running` | `not-reported` |

### idp-ha-3

| Container | Image | State | Health |
|---|---|---|---|
| `keycloak` | `quay.io/keycloak/keycloak:26.0` | `running` | `not-reported` |

### idp-live

| Container | Image | State | Health |
|---|---|---|---|
| `dotmac_sub_thin_shadow_app` | `342a9b805d6a` | `running` | `healthy` |
| `dotmac_sub_thin_shadow_postgres` | `681931a625df` | `running` | `healthy` |
| `dotmac_sub_thin_shadow_redis` | `e7723ff73d96` | `running` | `healthy` |
| `keycloak-keycloak-1` | `quay.io/keycloak/keycloak:26.0` | `running` | `healthy` |
| `keycloak-postgres-1` | `postgres:16-alpine` | `running` | `healthy` |

### integrator-vendor-control

| Container | Image | State | Health |
|---|---|---|---|
| `dotmac_vendor_control_plane-app-1` | `ghcr.io/michaelayoade/dotmac_vendor_control_plane` | `running` | `healthy` |
| `dotmac_vendor_control_plane-db-1` | `postgres:16` | `running` | `healthy` |
| `integrator-api-1` | `registry.dotmac.io/dotmac/integrator` | `running` | `healthy` |
| `integrator-db-1` | `postgres:16` | `running` | `healthy` |

### mail-dotmac

| Container | Image | State | Health |
|---|---|---|---|
| `mailcowdockerized-acme-mailcow-1` | `ghcr.io/mailcow/acme:1.92` | `running` | `not-reported` |
| `mailcowdockerized-clamd-mailcow-1` | `ghcr.io/mailcow/clamd:1.70` | `running` | `healthy` |
| `mailcowdockerized-dockerapi-mailcow-1` | `ghcr.io/mailcow/dockerapi:2.11` | `running` | `not-reported` |
| `mailcowdockerized-dovecot-mailcow-1` | `ghcr.io/mailcow/dovecot:2.33` | `running` | `not-reported` |
| `mailcowdockerized-ipv6nat-mailcow-1` | `robbertkl/ipv6nat` | `running` | `not-reported` |
| `mailcowdockerized-memcached-mailcow-1` | `memcached:alpine` | `running` | `not-reported` |
| `mailcowdockerized-mysql-mailcow-1` | `mariadb:10.11` | `running` | `not-reported` |
| `mailcowdockerized-netfilter-mailcow-1` | `ghcr.io/mailcow/netfilter:1.61` | `running` | `not-reported` |
| `mailcowdockerized-nginx-mailcow-1` | `ghcr.io/mailcow/nginx:1.03` | `running` | `not-reported` |
| `mailcowdockerized-ofelia-mailcow-1` | `mcuadros/ofelia:latest` | `running` | `not-reported` |
| `mailcowdockerized-olefy-mailcow-1` | `ghcr.io/mailcow/olefy:1.15` | `running` | `not-reported` |
| `mailcowdockerized-php-fpm-mailcow-1` | `ghcr.io/mailcow/phpfpm:1.93` | `running` | `not-reported` |
| `mailcowdockerized-postfix-mailcow-1` | `ghcr.io/mailcow/postfix:1.80` | `running` | `not-reported` |
| `mailcowdockerized-redis-mailcow-1` | `redis:7.4.2-alpine` | `running` | `not-reported` |
| `mailcowdockerized-rspamd-mailcow-1` | `ghcr.io/mailcow/rspamd:2.2` | `running` | `not-reported` |
| `mailcowdockerized-sogo-mailcow-1` | `ghcr.io/mailcow/sogo:1.133` | `running` | `not-reported` |
| `mailcowdockerized-unbound-mailcow-1` | `ghcr.io/mailcow/unbound:1.24` | `running` | `healthy` |
| `mailcowdockerized-watchdog-mailcow-1` | `ghcr.io/mailcow/watchdog:2.08` | `running` | `not-reported` |

### mail-nhia

| Container | Image | State | Health |
|---|---|---|---|
| `mailcowdockerized-acme-mailcow-1` | `ghcr.io/mailcow/acme:1.92` | `running` | `not-reported` |
| `mailcowdockerized-clamd-mailcow-1` | `ghcr.io/mailcow/clamd:1.70` | `running` | `healthy` |
| `mailcowdockerized-dockerapi-mailcow-1` | `ghcr.io/mailcow/dockerapi:2.11` | `running` | `not-reported` |
| `mailcowdockerized-dovecot-mailcow-1` | `ghcr.io/mailcow/dovecot:2.33` | `running` | `not-reported` |
| `mailcowdockerized-ipv6nat-mailcow-1` | `robbertkl/ipv6nat` | `running` | `not-reported` |
| `mailcowdockerized-memcached-mailcow-1` | `memcached:alpine` | `running` | `not-reported` |
| `mailcowdockerized-mysql-mailcow-1` | `mariadb:10.11` | `running` | `not-reported` |
| `mailcowdockerized-netfilter-mailcow-1` | `ghcr.io/mailcow/netfilter:1.61` | `running` | `not-reported` |
| `mailcowdockerized-nginx-mailcow-1` | `ghcr.io/mailcow/nginx:1.03` | `running` | `not-reported` |
| `mailcowdockerized-ofelia-mailcow-1` | `mcuadros/ofelia:latest` | `running` | `not-reported` |
| `mailcowdockerized-olefy-mailcow-1` | `ghcr.io/mailcow/olefy:1.15` | `running` | `not-reported` |
| `mailcowdockerized-php-fpm-mailcow-1` | `ghcr.io/mailcow/phpfpm:1.93` | `running` | `not-reported` |
| `mailcowdockerized-postfix-mailcow-1` | `ghcr.io/mailcow/postfix:1.80` | `running` | `not-reported` |
| `mailcowdockerized-redis-mailcow-1` | `redis:7.4.2-alpine` | `running` | `not-reported` |
| `mailcowdockerized-rspamd-mailcow-1` | `ghcr.io/mailcow/rspamd:2.2` | `running` | `not-reported` |
| `mailcowdockerized-sogo-mailcow-1` | `ghcr.io/mailcow/sogo:1.133` | `running` | `not-reported` |
| `mailcowdockerized-unbound-mailcow-1` | `ghcr.io/mailcow/unbound:1.24` | `running` | `healthy` |
| `mailcowdockerized-watchdog-mailcow-1` | `ghcr.io/mailcow/watchdog:2.08` | `running` | `not-reported` |

### nhia-moh-cloud

| Container | Image | State | Health |
|---|---|---|---|
| `easypanel-traefik.1.t3c8cljs3b4vixnng72fuf0ip` | `traefik:3.6.7` | `running` | `not-reported` |
| `easypanel.1.zyh6zft8wjpla9turhmrbcjum` | `easypanel/easypanel:latest` | `running` | `not-reported` |
| `moh_collabora.1.xgx3eia7c3bfn5vhweqlg3ved` | `collabora/code:latest` | `running` | `healthy` |
| `moh_nextcloud-db.1.6znsary56uk2ag1o82hngq4wr` | `postgres:17` | `running` | `not-reported` |
| `moh_nextcloud.1.r6umknjiawn6pk08qir1hrbqg` | `nextcloud:31.0.2` | `running` | `not-reported` |
| `nhia_collabora.1.vb8elcl5bylbj2j7fqt6h7gh6` | `collabora/code:latest` | `running` | `healthy` |
| `nhia_new_nextcloud-db.1.jgw3bsno3km9vm41j2wwp0qt7` | `postgres:17` | `running` | `not-reported` |
| `nhia_new_nextcloud.1.aj0pqpqepmci306ou77zfeu7d` | `nextcloud:31.0.4` | `running` | `not-reported` |
| `nhia_nhia-postgres-db.1.5za5ix7pmlcx9d809ytbofp5r` | `postgres:17` | `running` | `not-reported` |

### ns1

Host-only; Docker is not installed.

### ns2

Host-only; Docker is not installed.

### ns3

Host-only; Docker is not installed.

### observability-canary

Host-only; Docker is not installed.

### observe

| Container | Image | State | Health |
|---|---|---|---|
| `alertmanager` | `prom/alertmanager:latest` | `running` | `not-reported` |
| `cadvisor` | `gcr.io/cadvisor/cadvisor:latest` | `running` | `healthy` |
| `claude_knowledge-app-1` | `claude_knowledge-app:latest` | `running` | `healthy` |
| `claude_knowledge-db-1` | `postgres:16-alpine` | `running` | `healthy` |
| `claude_knowledge-indexer-1` | `85c25ba4e068` | `running` | `not-reported` |
| `claude_knowledge-ollama-1` | `ollama/ollama:0.32.1` | `running` | `healthy` |
| `cloudpg` | `postgres:16-alpine` | `running` | `not-reported` |
| `dotmac-positive-admission-pg-OqtKR3` | `postgis/postgis:16-3.4` | `running` | `not-reported` |
| `dotmac-positive-admission-pg-rebased2` | `postgis/postgis:16-3.4` | `running` | `not-reported` |
| `dotmac_billing_test_20260817-postgres-1` | `postgres:16` | `running` | `healthy` |
| `dotmac_sub_party_collision_pg` | `postgis/postgis:16-3.4` | `running` | `not-reported` |
| `erp-pg` | `postgres:16` | `running` | `not-reported` |
| `glitchtip` | `glitchtip/glitchtip:latest` | `running` | `not-reported` |
| `glitchtip-worker` | `glitchtip/glitchtip:latest` | `running` | `not-reported` |
| `grafana` | `grafana/grafana:latest` | `running` | `not-reported` |
| `loki` | `grafana/loki:latest` | `running` | `not-reported` |
| `netrecon-5459-postgres-1` | `postgres:16` | `running` | `healthy` |
| `node-exporter` | `prom/node-exporter:latest` | `running` | `not-reported` |
| `openbao` | `openbao/openbao:2` | `running` | `healthy` |
| `pq1-postgres-1` | `postgres:16` | `running` | `healthy` |
| `pq2-postgres-1` | `postgres:16` | `running` | `healthy` |
| `prometheus` | `prom/prometheus:latest` | `running` | `not-reported` |
| `promtail` | `grafana/promtail:latest` | `running` | `not-reported` |
| `sla-pr2-postgres` | `postgis/postgis:16-3.4` | `running` | `healthy` |
| `sp-pg` | `postgres:16` | `running` | `not-reported` |
| `subpg` | `postgis/postgis:16-3.4` | `running` | `not-reported` |
| `subscriber-retirement-pg-20260819` | `postgis/postgis:16-3.4` | `running` | `not-reported` |
| `vendor_billing_adoption_test-postgres-1` | `postgres:16` | `running` | `healthy` |

### proxmox

Host-only; Docker is not installed.

### s3

| Container | Image | State | Health |
|---|---|---|---|
| `forgejo-caddy-1` | `caddy:2-alpine` | `running` | `not-reported` |
| `forgejo-forgejo-1` | `codeberg.org/forgejo/forgejo:11` | `running` | `not-reported` |
| `forgejo-forgejo-db-1` | `postgres:16-alpine` | `running` | `healthy` |
| `minio` | `minio/minio:latest` | `running` | `healthy` |
| `node-exporter` | `prom/node-exporter:latest` | `running` | `not-reported` |
| `nominatim` | `mediagis/nominatim:4.4` | `running` | `not-reported` |

### seabone

| Container | Image | State | Health |
|---|---|---|---|
| `app_monitor-grafana-1` | `grafana/grafana:11.5.2` | `running` | `not-reported` |
| `app_monitor-loki-1` | `grafana/loki:3.4.2` | `running` | `not-reported` |
| `app_monitor-prometheus-1` | `prom/prometheus:v3.2.1` | `running` | `not-reported` |
| `codex_academy_inventory_pg_20260819` | `postgres:16` | `running` | `healthy` |
| `codex_academy_inventory_staging_pg_20260819` | `postgres:16` | `running` | `healthy` |
| `codex_backoffice_people_red_20260818` | `python:3.12-slim` | `running` | `not-reported` |
| `codex_erp_people_pg_20260819` | `postgres:16` | `running` | `healthy` |
| `codex_erp_people_validation_20260819` | `codex/erp-integrator-inventory-test:b969-candidate-r2` | `running` | `not-reported` |
| `codex_kernel_gate_static_sql_20260819` | `python:3.12-bookworm` | `running` | `not-reported` |
| `codex_starter_people_audit_20260818` | `python:3.12-bookworm` | `running` | `not-reported` |
| `codex_starter_people_pg_20260818` | `postgres:16` | `running` | `not-reported` |
| `dotmac_erp_app` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `healthy` |
| `dotmac_erp_beat` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `not-reported` |
| `dotmac_erp_db` | `23d19d971a56` | `running` | `not-reported` |
| `dotmac_erp_minio` | `minio/minio:latest` | `running` | `healthy` |
| `dotmac_erp_openbao` | `openbao/openbao:2` | `running` | `healthy` |
| `dotmac_erp_redis` | `redis:7` | `running` | `not-reported` |
| `dotmac_erp_worker` | `ghcr.io/michaelayoade/dotmac_erp` | `running` | `not-reported` |
| `dotmac_network_map_restore_20260814` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_omni_app` | `ghcr.io/michaelayoade/dotmac_crm:sha-1a72fb2` | `running` | `healthy` |
| `dotmac_omni_celery_beat` | `ghcr.io/michaelayoade/dotmac_crm:sha-1a72fb2` | `running` | `not-reported` |
| `dotmac_omni_celery_worker` | `ghcr.io/michaelayoade/dotmac_crm:sha-1a72fb2` | `running` | `not-reported` |
| `dotmac_omni_db` | `postgis/postgis:16-3.4` | `running` | `healthy` |
| `dotmac_omni_redis` | `redis:7-alpine` | `running` | `healthy` |
| `dotmac_sub_app` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_bandwidth_poller` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_bandwidth` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_billing` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_ingestion` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_monitoring` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_notifications` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_notifications_immediate` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_tr069` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_db` | `postgis/postgis:16-3.4` | `running` | `healthy` |
| `dotmac_sub_genieacs` | `dotmac_sub-genieacs:1.2.13` | `running` | `not-reported` |
| `dotmac_sub_genieacs_mongodb` | `mongo:4.4` | `running` | `not-reported` |
| `dotmac_sub_minio` | `minio/minio:RELEASE.2025-01-20T14-49-07Z` | `running` | `not-reported` |
| `dotmac_sub_nominatim` | `mediagis/nominatim:4.4` | `running` | `not-reported` |
| `dotmac_sub_openbao` | `quay.io/openbao/openbao:latest` | `running` | `healthy` |
| `dotmac_sub_redis` | `redis:7` | `running` | `healthy` |
| `dotmac_sub_syslog_listener` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `not-reported` |
| `dotmac_sub_team_inbox_smtp` | `ghcr.io/michaelayoade/dotmac_sub` | `running` | `unhealthy` |
| `dotmac_sub_victoriametrics` | `victoriametrics/victoria-metrics:v1.96.0` | `running` | `not-reported` |
| `dotmac_vmagent` | `victoriametrics/vmagent:v1.96.0` | `running` | `not-reported` |
| `node-exporter` | `prom/node-exporter:v1.9.1` | `running` | `not-reported` |
| `promtail-central` | `grafana/promtail:3.0.0` | `running` | `not-reported` |
| `splynx_restore` | `mysql:8.0` | `running` | `healthy` |
| `vcp-stack2-6mhws8-postgres-1` | `postgres:16` | `running` | `healthy` |
| `vcpstack2bysp3d-postgres-1` | `postgres:16` | `running` | `healthy` |

### son-erp

| Container | Image | State | Health |
|---|---|---|---|
| `promtail` | `grafana/promtail:latest` | `running` | `not-reported` |
| `son_erp_app` | `son_erp_app:latest` | `running` | `healthy` |
| `son_erp_beat` | `son_erp-beat` | `running` | `not-reported` |
| `son_erp_db` | `postgis/postgis:16-3.4` | `running` | `healthy` |
| `son_erp_redis` | `redis:7` | `running` | `not-reported` |
| `son_erp_worker` | `son_erp-worker` | `running` | `not-reported` |

### sub-prod

| Container | Image | State | Health |
|---|---|---|---|
| `dotmac_network_map_restore_20260814` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_network_map_restore_20260817_221228_segments` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_network_map_restore_importer_20260814_v2` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_network_map_restore_test` | `postgis/postgis:16-3.4-alpine` | `running` | `not-reported` |
| `dotmac_pg_local` | `postgis/postgis:16-3.4-alpine` | `running` | `healthy` |
| `dotmac_radius_pg_test` | `postgis/postgis:16-3.4-alpine` | `running` | `healthy` |
| `dotmac_redis_local` | `redis:7-alpine` | `running` | `healthy` |
| `dotmac_sub_app` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_bandwidth_poller` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_beat` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_bandwidth` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_billing` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_ingestion` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_monitoring` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_notifications` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_notifications_immediate` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_celery_worker_tr069` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_freeradius` | `freeradius/freeradius-server:3.2.7` | `running` | `not-reported` |
| `dotmac_sub_genieacs` | `ghcr.io/michaelayoade/dotmac_sub-genieacs:1.2.13` | `running` | `not-reported` |
| `dotmac_sub_genieacs_mongodb` | `mongo:4.4` | `running` | `not-reported` |
| `dotmac_sub_nominatim` | `mediagis/nominatim:4.4` | `running` | `not-reported` |
| `dotmac_sub_promtail` | `grafana/promtail:3.0.0` | `running` | `not-reported` |
| `dotmac_sub_syslog_listener` | `2ba253f42663` | `running` | `not-reported` |
| `dotmac_sub_team_inbox_smtp` | `94a820a2ce73` | `running` | `healthy` |
| `dotmac_sub_victoriametrics` | `victoriametrics/victoria-metrics:v1.96.0` | `running` | `not-reported` |
| `dotmac_vmagent` | `victoriametrics/vmagent:v1.96.0` | `running` | `not-reported` |

### test-server

Docker is installed; no running containers observed.

### web-cache

Host-only; Docker is not installed.

### workspace

| Container | Image | State | Health |
|---|---|---|---|
| `workspace-workspace-1` | `dotmac-workspace:37189f8` | `running` | `healthy` |

### zabbix

Host-only; Docker is not installed.
