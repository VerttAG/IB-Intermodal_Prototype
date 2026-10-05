// Password gate in front of the whole demo (Vercel Routing Middleware).
// One shared password, no user name. Set it as the environment variable DEMO_PASSWORD
// in the Vercel project; without it nobody gets in.
// ponytail: no limit on wrong attempts; add rate limiting if the demo is ever more than a prototype.

export const config = { matcher: '/(.*)' };

const COOKIE = 'demo_auth';

async function sha256(text) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function page(message, status) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Intermodal demo</title>
<style>body{font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;background:#f4f5f7;color:#1d2330}
form{background:#fff;padding:24px;border-radius:12px;width:min(320px,90vw);box-shadow:0 2px 12px #0002}
label{display:block;font-weight:600;margin-bottom:8px}input,button{width:100%;box-sizing:border-box;padding:10px;font-size:16px;border-radius:8px}
input{border:1px solid #9aa3b2;margin-bottom:12px}button{border:0;background:#1d2330;color:#fff;font-weight:600}p{color:#b3261e;margin:0 0 12px}</style></head>
<body><form method="post"><label for="password">Password</label>${message ? `<p role="alert">${message}</p>` : ''}
<input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
<button type="submit">Open demo</button></form></body></html>`,
    { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });
}

export default async function middleware(request) {
  const password = process.env.DEMO_PASSWORD;
  if (!password) return new Response('Demo password is not configured.', { status: 503 });
  const token = await sha256(password);

  const cookies = request.headers.get('cookie') || '';
  if (cookies.split(/;\s*/).includes(`${COOKIE}=${token}`)) {
    return new Response(null, { headers: { 'x-middleware-next': '1' } }); // continue to the page
  }

  if (request.method === 'POST') {
    const entered = (await request.formData()).get('password');
    if (entered !== password) return page('Wrong password.', 401);
    return new Response(null, {
      status: 303,
      headers: {
        location: new URL(request.url).pathname,
        'set-cookie': `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=43200`,
      },
    });
  }
  return page('', 401);
}
