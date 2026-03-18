// Cloudflare Pages Function: proxy /api/* to Cloud Run backend
export const onRequest: PagesFunction = async (context) => {
  const backendOrigin = (context.env.BACKEND_ORIGIN as string | undefined) ||
    'https://sdd-flow-backend-i2oevdkzpq-ew.a.run.app';

  const incomingUrl = new URL(context.request.url);
  const targetUrl = new URL(incomingUrl.pathname + incomingUrl.search, backendOrigin);

  const upstreamRequest = new Request(targetUrl.toString(), context.request);
  return fetch(upstreamRequest);
};
