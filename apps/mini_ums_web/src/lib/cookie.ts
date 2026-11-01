// Shared by the proxy and server code. The cookie holds the API session token and is
// httpOnly, so page scripts (including the voice widget) can never read it.
export const SESSION_COOKIE = "univra_session";
