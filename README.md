# Cozy Manchot


## Local development

Use Node.js 22.17+ and Bun.

```sh
bun install --frozen-lockfile
bun run dev
bun run check
bun run test
bun run build
bun run preview
```

Vite is only the local preview and build tool. The output is static HTML, CSS, and JavaScript. Deploy the whole `dist` directory to a static host with directory index URLs and a custom `404.html` page.

The contact form, newsletter, and checkout keep the original demonstration behavior. They display confirmations locally and do not send messages, take payments, or save orders to a backend.
