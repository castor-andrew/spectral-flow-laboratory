# Add the simulator to andrewcastor.com

The authoritative Python solver must remain reachable for its WebSocket stream. Deploy this repository to a Python/Docker host, map `fluid.andrewcastor.com`, then embed it in the main site.

## Recommended deployment: Render

The repository now includes `render.yaml`, so Render can create the Docker web
service without manually entering build or start commands.

1. Sign in at <https://dashboard.render.com> with GitHub.
2. Select **New → Blueprint** and connect
   `castor-andrew/spectral-flow-laboratory`.
3. Accept the `spectral-flow-laboratory` service defined by `render.yaml` and
   wait for the first deploy to finish.
4. Open the generated `https://spectral-flow-laboratory.onrender.com/health`
   address and confirm it returns `{"ok":true,...}`.
5. In the service, open **Settings → Custom Domains**, add
   `fluid.andrewcastor.com`, and copy the exact Render hostname it supplies.
6. In Namecheap, open **Domain List → andrewcastor.com → Manage → Advanced
   DNS**. Add a **CNAME Record** with host `fluid` and the Render hostname as
   its value. Leave the existing `@` and `www` records unchanged so the
   previous main site stays live.
7. Return to Render and click **Verify** for the custom domain. Render will
   provision HTTPS automatically.
8. Confirm `https://fluid.andrewcastor.com/health`, then use the iframe markup
   below on the main site.

The free Render instance sleeps after inactivity, so its first visit can take
time to wake. For an always-ready portfolio experience, switch the service to
a paid compute plan after confirming the deployment.

Use one server worker: multiple workers would hold separate simulation states. This CPU implementation suits modest traffic; larger public traffic needs per-session workers and quotas.

## Embed markup

```html
<div class="fluid-simulator">
  <iframe src="https://fluid.andrewcastor.com/?embed=1"
    title="Interactive 3D spectral water-flow simulator"
    loading="lazy" allow="fullscreen"></iframe>
</div>
<style>
.fluid-simulator { width:100%; min-height:720px; background:#09151a; overflow:hidden; }
.fluid-simulator iframe { display:block; width:100%; height:720px; border:0; }
@media(max-width:850px) { .fluid-simulator,.fluid-simulator iframe { height:980px; } }
</style>
```

`?embed=1` removes the masthead and footer while preserving the Three.js viewport, controls, and diagnostics. It cannot run as static files alone because Python owns the physics.
