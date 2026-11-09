
# Task 5 — Subnet Allocation

## Given Network

Base network: 10.20.0.0/16

We must allocate four subnets using VLSM
(Variable Length Subnet Mask), starting with
the largest host requirement.

## Subnet Allocation

| Subnet | Hosts Required | Network/CIDR | Usable Host Range | Broadcast | Usable Hosts |
|---|---:|---|---|---|---:|
| app | 1000 | 10.20.0.0/22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1022 |
| public | 250 | 10.20.4.0/24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 100 | 10.20.5.0/25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 20 | 10.20.5.128/27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

## Calculations

Usable hosts = 2^(32 - prefix) - 2

### 1. App subnet
Required: 1000 hosts

2^10 - 2 = 1022

Prefix: /22

Network: 10.20.0.0/22

### 2. Public subnet
Required: 250 hosts

2^8 - 2 = 254

Prefix: /24

Network: 10.20.4.0/24

### 3. Data subnet
Required: 100 hosts

2^7 - 2 = 126

Prefix: /25

Network: 10.20.5.0/25

### 4. Management subnet
Required: 20 hosts

2^5 - 2 = 30

Prefix: /27

Network: 10.20.5.128/27

## Explanation

VLSM allows subnets of different sizes to be
allocated based on their host requirements.

We allocate the largest subnet first to avoid
address fragmentation and ensure efficient use
of the available 10.20.0.0/16 address space.

The four allocated subnets do not overlap.
