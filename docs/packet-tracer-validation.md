# Manual Packet Tracer validation checklist

Use this checklist after installing Cisco Packet Tracer. It validates the
generated commands in the actual simulator.

1. Ask Claude to generate a lab with 2 routers, 1 switch, and 2 PCs using OSPF.
2. Place two `2911` routers, one `2960` switch, and two PCs on the canvas.
3. Connect devices exactly as shown by the diagram.
4. Enter each router configuration in its CLI.
5. Enter the switch configuration in its CLI.
6. Enter each PC address under `Desktop > IP Configuration`.
7. On each router, run:

   ```text
   show ip interface brief
   show ip route
   show ip ospf neighbor
   ```

8. Test local and remote connectivity with `ping`.
9. Copy the final router and switch configurations back to Claude.
10. Call `verify_config` with the original plan and pasted configurations.

Expected OSPF checks:

- Interfaces show `up/up` after links are connected.
- OSPF neighbors reach the `FULL` state.
- OSPF routes appear in `show ip route`.
- PCs can ping their gateway.

If a command fails in Packet Tracer, record the device model, interface name,
command, and exact error. That information is needed to adjust the renderer.
