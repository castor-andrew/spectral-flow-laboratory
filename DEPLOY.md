# Add the simulator to andrewcastor.com

The authoritative Python solver must remain reachable for its WebSocket stream. Deploy this repository to a Python/Docker host, map `fluid.andrewcastor.com`, then embed it in the main site.

## Deployment

1. Push this folder to a Git repository.
2. Create a web service on Render, Railway, Fly.io, or another Docker host.
3. Use the included `Dockerfile`; it reads the provider's `PORT` and listens on `0.0.0.0`.
4. Add `fluid.andrewcastor.com` as a custom domain and create the DNS record specified by the host.
5. Confirm `https://fluid.andrewcastor.com/health` returns `{"ok":true,...}`.

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
