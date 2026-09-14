# Containerlab image profiles

## Initial profile: `frr-free`

The first automated backend uses this profile:

```text
Routers: frrouting/frr:latest
Switches: wbitt/network-multitool:latest (temporary placeholder)
PCs: wbitt/network-multitool:latest
Servers: wbitt/network-multitool:latest
```

FRRouting is a practical starting point because it provides a Linux-based
routing environment for learning and local automation. The host image is used
for PC-like connectivity tests.

The switch image is not a true Layer-2 switch. In the first prototype it is a
placeholder so we can validate YAML generation and the deployment pipeline.
Before using switch-heavy labs, we must replace it with a real supported
containerlab switch or explicitly configure Linux bridging.

## Images are separate from containerlab

Containerlab deploys images; it does not automatically grant rights to use
proprietary network operating systems. Cisco, Juniper, and other vendor images
may require separate licenses or an account. Do not download or redistribute
images unless their license permits it.

## Pulling images

Image downloads are intentionally not performed by the MCP server. A user
should review and pull images explicitly on the host:

```bash
docker pull frrouting/frr:latest
docker pull wbitt/network-multitool:latest
```

Later we can add a read-only image availability check. Automatic image pulls
should require an explicit user action because they change the local Docker
environment and use network access.

## Future profiles

Possible future profiles include:

- A real Layer-2 switch profile
- Nokia SR Linux, subject to image and license requirements
- Legally available Cisco virtual images
- A minimal FRRouting-only profile for router-to-router labs
