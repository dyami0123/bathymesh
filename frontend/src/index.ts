import { serve } from "bun";
import index from "./index.html";

const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const server = serve({
  routes: {
    "/api/*": async (req) => {
      const incomingUrl = new URL(req.url);
      const targetUrl = new URL(
        incomingUrl.pathname + incomingUrl.search,
        BACKEND_ORIGIN
      );

      return fetch(targetUrl, {
        method: req.method,
        headers: req.headers,
        body:
          req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
      });
    },

    // Serve index.html for all unmatched routes.
    "/": index,

    "/api/hello": {
      async GET(req) {
        return Response.json({
          message: "Hello, world!",
          method: "GET",
        });
      },
      async PUT(req) {
        return Response.json({
          message: "Hello, world!",
          method: "PUT",
        });
      },
    },

    "/api/hello/:name": async (req) => {
      const name = req.params.name;
      return Response.json({
        message: `Hello, ${name}!`,
      });
    },
  },

  development: process.env.NODE_ENV !== "production" && {
    // Enable browser hot reloading in development
    hmr: true,

    // Echo console logs from the browser to the server
    console: true,
  },
});

console.log(`🚀 Server running at ${server.url}`);
